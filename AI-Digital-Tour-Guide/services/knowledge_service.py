import os
from dotenv import load_dotenv, find_dotenv
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import DashScopeEmbeddings


# find_dotenv() 会自动向上级目录寻找 .env 文件，100% 绝对不会迷路！
load_dotenv(find_dotenv())



# ==========================================
# 1. 预热核心大脑：连接高维向量空间
# ==========================================
print("🗄️  [KnowledgeService] 正在连接高维空间向量数据库 (Chroma)...")
embeddings = DashScopeEmbeddings(model="text-embedding-v3")
# 【修复点】使用绝对路径，避免 CWD 不同导致的路径错误
_chroma_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db_final")
db_chroma = Chroma(persist_directory=_chroma_dir, embedding_function=embeddings)
# 【修复点】导出共享 retriever，避免 chat_service / recommend_service 各自创建
retriever = db_chroma.as_retriever(search_kwargs={"k": 3})

# ==========================================
# 2. 向量检索彻底替代 jieba (核心升级)
# ==========================================
def search_knowledge(
    db: Session,
    user_input: str,
    threshold: float = 0.3  # 向量距离阈值（视具体距离算法微调，0.3是个合理的默认参考）
) -> Tuple[Optional[dict], float, str]:
    """
    第一阶段检索：使用 Chroma 语义相似度替代原有的 jieba 关键词命中率。
    """
    # similarity_search_with_relevance_scores 会返回 (Document, score) 元组
    docs_with_scores = db_chroma.similarity_search_with_relevance_scores(user_input, k=1)
    
    if not docs_with_scores:
        return None, 0.0, "chroma_base"

    best_doc, score = docs_with_scores[0]

    # 将高维卡片伪装成原系统认识的 dict 格式，保持接口契约完美对接
    best_match = {
        "question": "（基于语义匹配）",
        "answer": best_doc.page_content,
        "spot_id": None
    }

    # 如果相关度低于阈值，直接判定为未命中
    if score < threshold:
        return None, score, "chroma_base"

    return best_match, score, "chroma_base"

def get_related_records(user_input: str, top_k: int = 5) -> List[dict]:
    """
    获取 Top-K 相关记录：不再需要循环打分排序，Chroma 底层已用最优算法完成检索。
    """
    docs = db_chroma.similarity_search(user_input, k=top_k)
    
    result = []
    for doc in docs:
        result.append({
            "question": "（基于语义匹配）",
            "answer": doc.page_content
        })
    return result

# ==========================================
# 3. 向后兼容层 (保证后台管理面板不崩溃)
# ==========================================
# 因为现在所有大模型检索都已经物理隔离到了 ChromaDB (Word解析)
# 管理员在 Web 界面对 SQLite 的修改暂时不会影响大模型。
# 保留以下空函数，确保 app.py 的路由和前端后台不出 500 报错。

def load_cache(db: Session) -> List[dict]:
    return []

def get_cache() -> List[dict]:
    return []

def refresh_cache(db: Session) -> List[dict]:
    return []