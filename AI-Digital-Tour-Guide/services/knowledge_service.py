"""
知识库检索服务
- jieba 分词 + 关键词匹配
- 内存缓存（首次加载后常驻，CUD 操作后刷新）
"""
import jieba
import re
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session

from models import Knowledge

# ── 停用词表（常见无意义词汇） ──
STOP_WORDS = set([
    "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些",
    "什么", "怎么", "如何", "为什么", "吗", "呢", "吧", "啊", "哦", "嗯",
    "请问", "可以", "能", "告诉", "一下", "大概", "大约", "左右", "请",
    "这个", "那个", "哪个", "哪里", "哪儿", "多少", "多久",
])

# ── 内存缓存 ──
_cache: Optional[List[dict]] = None


def _tokenize(text: str) -> List[str]:
    """分词并过滤停用词和标点"""
    words = jieba.lcut(text)
    result = []
    for w in words:
        w = w.strip().lower()
        if w and len(w) > 1 and w not in STOP_WORDS and not re.match(r'^[^\w]+$', w):
            result.append(w)
    return result


def _match_score(keywords: List[str], target_text: str) -> float:
    """
    计算匹配分数：命中关键词数 / 总关键词数
    """
    if not keywords:
        return 0.0
    target_lower = target_text.lower()
    hits = sum(1 for kw in keywords if kw in target_lower)
    return hits / len(keywords)


def load_cache(db: Session) -> List[dict]:
    """
    从数据库加载全部知识库条目到内存缓存。
    """
    global _cache
    records = db.query(Knowledge).all()
    _cache = [r.to_dict() for r in records]
    return _cache


def get_cache() -> List[dict]:
    """获取当前缓存（如果未初始化则返回空列表）"""
    global _cache
    return _cache or []


def refresh_cache(db: Session) -> List[dict]:
    """刷新缓存（CUD 操作后调用）"""
    return load_cache(db)


def search_knowledge(
    db: Session,
    user_input: str,
    threshold: float = 0.6
) -> Tuple[Optional[dict], float, str]:
    """
    双阶段检索的第一阶段：知识库关键词匹配。

    参数：
        db: 数据库会话
        user_input: 用户输入文本
        threshold: 匹配分数阈值（默认0.6）

    返回：
        (best_match, score, source)
        - best_match: 最佳匹配的 Knowledge 字典，无匹配时为 None
        - score: 匹配分数
        - source: 始终为 "knowledge_base"
    """
    # 分词
    keywords = _tokenize(user_input)
    if not keywords:
        return None, 0.0, "knowledge_base"

    # 从缓存或数据库获取
    records = get_cache()
    if not records:
        records = load_cache(db)
    if not records:
        return None, 0.0, "knowledge_base"

    # 对每条 FAQ 计算匹配分数（问题权重 0.7，答案权重 0.3）
    best = None
    best_score = 0.0
    for rec in records:
        q_score = _match_score(keywords, rec["question"])
        a_score = _match_score(keywords, rec["answer"])
        score = q_score * 0.7 + a_score * 0.3
        if score > best_score:
            best_score = score
            best = rec

    if best and best_score >= threshold:
        return best, best_score, "knowledge_base"
    return None, best_score, "knowledge_base"


def get_related_records(user_input: str, top_k: int = 5) -> List[dict]:
    """
    获取与用户输入最相关的 Top-K 条知识库记录，
    作为 DeepSeek API 的上下文。

    使用缓存数据，无需 DB 查询。
    """
    keywords = _tokenize(user_input)
    records = get_cache()
    if not records or not keywords:
        return records[:top_k] if records else []

    # 按分数排序取 Top-K
    scored = []
    for rec in records:
        score = _match_score(keywords, rec["question"]) * 0.7 + \
                _match_score(keywords, rec["answer"]) * 0.3
        if score > 0:
            scored.append((score, rec))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [rec for _, rec in scored[:top_k]]
