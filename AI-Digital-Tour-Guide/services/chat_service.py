import os
import re
from datetime import date, datetime
from sqlalchemy.orm import Session

# ==========================================
# 1. 导入 LangChain 超级大脑组件
# ==========================================
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ==========================================
# 2. 导入原有业务模型
# ==========================================
from models import Conversation, Stat

# ⚠️ 注意：实战中建议将 API_KEY 写在队友配置的 .env 文件中
# 这里为了快速联调，你可以先写死
os.environ["DASHSCOPE_API_KEY"] = "sk-91b5c2013f354bf78ebd2475fa23bd73"

# ==========================================
# 3. 情感分析关键词 (保留队友原有逻辑，供管理大屏使用)
# ==========================================
POSITIVE_WORDS = re.compile(
    r"好|棒|喜欢|开心|满意|赞|不错|推荐|值得|漂亮|美|壮观|震撼|惊喜|太|很棒"
)
NEGATIVE_WORDS = re.compile(
    r"差|不好|失望|贵|坑|无聊|烂|后悔|不值|难吃|骗|乱|差劲"
)

def analyze_emotion(text: str) -> str:
    """基于关键词的情感分析，返回 positive / negative / neutral"""
    if POSITIVE_WORDS.search(text):
        return "positive"
    elif NEGATIVE_WORDS.search(text):
        return "negative"
    return "neutral"

# ==========================================
# 4. 初始化全局 LangChain RAG 引擎
# ==========================================
print("🧠 [ChatService] 正在唤醒高精度 Chroma 向量知识库与通义引擎...")

embeddings = DashScopeEmbeddings(model="text-embedding-v3")
# 确保 chroma_db_final 文件夹放在了项目根目录
db = Chroma(persist_directory="./chroma_db_final", embedding_function=embeddings)
retriever = db.as_retriever(search_kwargs={"k": 3})

llm = ChatTongyi(model="qwen-turbo", temperature=0.5)

# 【完美融合】保留了队友的“小灵”人设，加入了严密的 RAG 纪律
SYSTEM_TEMPLATE = """你是「灵山胜境」景区的AI数字人导游，名叫"小灵"。

你的特点：
- 热情亲切，说话带一点禅意但不刻意
- 回答风格口语化，像真人导游聊天
- 尊称游客为"您"

你的任务是根据下面提供的【参考资料】来回答游客的问题。

【参考资料】
{context}

【导游守则】
1. 必须基于【参考资料】回答问题，绝不能编造信息。
2. 如果参考资料中没有相关信息，请诚实告知游客，并建议他咨询景区工作人员。
3. 回答控制在200字以内，简洁清晰。
4. 回答末尾可以加一句相关小贴士（可选）。
5. 始终保持友善和耐心。

游客的问题是：{question}
"""
prompt = ChatPromptTemplate.from_template(SYSTEM_TEMPLATE)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()} 
    | prompt 
    | llm 
    | StrOutputParser()
)

# ==========================================
# 5. 对外暴露的核心处理流
# ==========================================
async def process_chat(
    db: Session,
    session_id: str,
    message: str
) -> dict:
    """
    处理一次对话：LangChain 检索生成 + 情感分析 + 统计更新。
    """
    # ── 第一阶段：交给 LangChain 超级大脑处理问答 ──
    try:
        # 直接调用你的 RAG 流水线，一步到位完成检索和回答
        answer = rag_chain.invoke(message)
        source = "chroma_rag"
    except Exception as e:
        print(f"❌ 模型调用失败: {e}")
        # 兜底回复保持原有风格
        answer = "阿弥陀佛～小灵的脑电波暂时走神了，请稍后再试哦。"
        source = "fallback"

    # ── 第二阶段：情感分析（供队友的 ECharts 大屏使用） ──
    emotion = analyze_emotion(message)

    # ── 第三阶段：保存对话记录（写进数据库） ──
    conv = Conversation(
        session_id=session_id,
        user_input=message,
        bot_answer=answer,
        source=source,
        emotion=emotion,
    )
    db.add(conv)
    db.commit()

    # ── 第四阶段：更新每日统计 ──
    _update_stats(db, session_id, emotion)

    return {
        "answer": answer,
        "emotion": emotion,
        "source": source,
        "spot_id": None, # Chroma 切片暂无单一景点ID映射，给 None 即可
    }

# ==========================================
# 6. 保留原有每日统计模块
# ==========================================
def _update_stats(db: Session, session_id: str, emotion: str):
    """
    更新每日统计数据：
    - 同一 session 当日首次对话时 service_count += 1
    - 情感计数每次对话都更新
    """
    today = date.today()

    # 检查这个 session 今天是否已经计过数
    existing = db.query(Conversation).filter(
        Conversation.session_id == session_id,
        Conversation.create_time >= datetime.combine(today, datetime.min.time()),
    ).first()

    is_first_today = (
        existing is None or
        existing.id == db.query(Conversation).filter(
            Conversation.session_id == session_id
        ).order_by(Conversation.id.asc()).first().id
    )

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