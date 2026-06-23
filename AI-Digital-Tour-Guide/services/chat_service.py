"""
对话处理服务
- 双阶段问答（知识库 → DeepSeek 兜底）
- 关键词情感分析
- 每日统计更新
"""
import re
import time
import httpx
from datetime import date, datetime
from typing import Tuple, Optional
from sqlalchemy.orm import Session

from config import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL
from models import Conversation, Stat
from services.knowledge_service import search_knowledge, get_related_records


# ── 情感分析关键词 ──
POSITIVE_WORDS = re.compile(
    r"好|棒|喜欢|开心|满意|赞|不错|推荐|值得|漂亮|美|壮观|震撼|惊喜|太|很棒"
)
NEGATIVE_WORDS = re.compile(
    r"差|不好|失望|贵|坑|无聊|烂|后悔|不值|难吃|骗|乱|差劲"
)

# ── DeepSeek System Prompt ──
SYSTEM_PROMPT = """你是「灵山胜境」景区的AI数字人导游，名叫"小灵"。

你的特点：
- 热情亲切，说话带一点禅意但不刻意
- 回答风格口语化，像真人导游聊天
- 尊称游客为"您"

你必须遵守以下规则：
1. 基于提供的【参考资料】回答问题，不要编造信息
2. 如果参考资料中没有相关信息，请诚实告知游客，并建议他咨询景区工作人员
3. 回答控制在200字以内，简洁清晰
4. 回答末尾可以加一句相关小贴士（可选）
5. 回复不要带阿弥陀佛等宗教词汇，保持中立和专业
6. 始终保持友善和耐心"""

def analyze_emotion_keyword(text: str) -> str:
    """基于关键词的情感分析（API不可用时的降级方案）"""
    if POSITIVE_WORDS.search(text):
        return "positive"
    elif NEGATIVE_WORDS.search(text):
        return "negative"
    return "neutral"


async def analyze_emotion(text: str) -> str:
    """
    用大模型进行情感分析，返回 positive / negative / neutral。
    API 不可用时降级为关键词匹配。
    """
    if not DEEPSEEK_API_KEY:
        return analyze_emotion_keyword(text)

    prompt = (
        "分析以下游客对景区导游回答的情感倾向。"
        "只回复一个词：positive（正面）、negative（负面）或 neutral（中性）。\n"
        f"游客说的话：\"{text}\""
    )
    timeout = httpx.Timeout(5.0, read=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{DEEPSEEK_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": DEEPSEEK_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 10,
                    "temperature": 0,
                },
            )
            if resp.status_code == 200:
                result = resp.json()["choices"][0]["message"]["content"].strip().lower()
                if "positive" in result:
                    return "positive"
                elif "negative" in result:
                    return "negative"
                return "neutral"
    except Exception:
        pass
    # 降级
    return analyze_emotion_keyword(text)


async def call_deepseek(user_input: str, context_records: list) -> str:
    """
    调用 DeepSeek API 生成回答。

    参数：
        user_input: 用户问题
        context_records: 知识库相关记录列表

    返回：
        AI 生成的回答文本
    """
    if not DEEPSEEK_API_KEY:
        return _fallback_answer()

    # 构建上下文
    context_parts = []
    for i, rec in enumerate(context_records, 1):
        context_parts.append(
            f"【参考资料{i}】\n问题：{rec['question']}\n回答：{rec['answer']}"
        )
    context_text = "\n\n".join(context_parts) if context_parts else "暂无相关参考资料"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"【参考资料】\n{context_text}\n\n【游客问题】\n{user_input}"}
    ]

    timeout = httpx.Timeout(10.0, read=10.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(2):  # 最多2次尝试
            try:
                resp = await client.post(
                    f"{DEEPSEEK_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": DEEPSEEK_MODEL,
                        "messages": messages,
                        "max_tokens": 500,
                        "temperature": 0.7,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    if attempt == 0:
                        continue  # 重试一次
            except Exception:
                if attempt == 0:
                    continue

    return _fallback_answer()


def _fallback_answer() -> str:
    """DeepSeek API 不可用时的兜底回答"""
    return (
        "小灵暂时无法回答这个问题 😅\n\n"
        "您可以试试问我这些问题：\n"
        "• 灵山大佛有多高？\n"
        "• 九龙灌浴几点表演？\n"
        "• 灵山有什么好玩的？\n"
        "• 门票多少钱？"
    )


async def process_chat(
    db: Session,
    session_id: str,
    message: str
) -> dict:
    """
    处理一次对话：检索 + 情感分析 + 统计更新。

    返回：
        {
            "answer": str,
            "emotion": str,
            "source": "knowledge_base" | "deepseek",
            "spot_id": str | None
        }
    """
    # ── 第一阶段：知识库检索 ──
    best_match, score, source = search_knowledge(db, message, threshold=0.6)

    answer = None
    spot_id = None

    if best_match:
        answer = best_match["answer"]
        spot_id = best_match.get("spot_id")
        source = "knowledge_base"
    else:
        # ── 第二阶段：DeepSeek 兜底 ──
        context_records = get_related_records(message, top_k=5)
        answer = await call_deepseek(message, context_records)
        source = "deepseek"
        spot_id = context_records[0].get("spot_id") if context_records else None

    # ── 情感分析（大模型判断，API不可用时自动降级关键词）──
    emotion = await analyze_emotion(message)

    # ── 保存对话记录 ──
    conv = Conversation(
        session_id=session_id,
        user_input=message,
        bot_answer=answer,
        source=source,
        emotion=emotion,
    )
    db.add(conv)
    db.commit()

    # ── 更新每日统计 ──
    _update_stats(db, session_id, emotion)

    return {
        "answer": answer,
        "emotion": emotion,
        "source": source,
        "spot_id": spot_id,
    }


def _update_stats(db: Session, session_id: str, emotion: str):
    """
    更新每日统计数据：
    - 同一 session 当日首次对话时 service_count += 1
    - 情感计数每次对话都更新
    """
    today = date.today()

    # 检查这个 session 今天是否已经计过数
    # 统计今天这个 session 已有的对话数（包括刚刚创建的那条）
    count_today = db.query(Conversation).filter(
        Conversation.session_id == session_id,
        Conversation.create_time >= datetime.combine(today, datetime.min.time()),
    ).count()

    # 如果只有1条（就是刚才创建的），说明今天是第一次
    is_first_today = (count_today == 1)

    # 获取或创建今日 Stat
    stat = db.query(Stat).filter(Stat.date == today).first()
    if not stat:
        stat = Stat(date=today, service_count=0, positive_count=0, negative_count=0, neutral_count=0)
        db.add(stat)
        db.flush()

    if is_first_today:
        stat.service_count += 1

    if emotion == "positive":
        stat.positive_count += 1
    elif emotion == "negative":
        stat.negative_count += 1
    else:
        stat.neutral_count += 1

    db.commit()
