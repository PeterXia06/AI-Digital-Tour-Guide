"""
推荐服务
- 基于 ChromaDB 向量检索 + LLM 结构化路线规划
- 双数据库融合 (Vector DB + SQL DB)
"""
import json
import re
from typing import Optional
from sqlalchemy.orm import Session

from dotenv import load_dotenv, find_dotenv

from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from models import Spot
# 【修复点】使用 knowledge_service 导出的共享 retriever 单例
from services.knowledge_service import retriever

# 加载环境变量
load_dotenv(find_dotenv())

print("🗺️  [RecommendService] 正在启动大模型结构化路线规划引擎...")

# ── 初始化 LLM ──
# temperature=0.1 极低温，让大模型极其理智，防止输出畸形的 JSON
llm = ChatTongyi(model="qwen-turbo", temperature=0.1)

# ── 路线推荐模板 ──
# 【修复点】补充了缺失的变量名 RECOMMEND_TEMPLATE
RECOMMEND_TEMPLATE = """你是「灵山胜境」景区的AI行程规划师。

你的特点：
- 热情亲切，说话带一点禅意但不刻意
- 回答风格口语化，像真人导游聊天
- 尊称游客为"您"

【必须严格遵守的输出格式】
你必须且只能输出一个合法的 JSON 数据（不要用 ```json 包裹，直接输出大括号），格式严格如下：
{{
    "name": "为路线起个好听的名字(如: 灵山禅意静心游)",
    "type": "{tag}",
    "duration": "如: 3小时 / 半日游",
    "description": "路线的总体特色介绍(50字左右)",
    "spots": [
        {{
            "name": "景点名称(必须是参考资料里真实存在的)",
            "intro": "景点简介(一句话)",
            "highlight": "核心看点"
        }}
    ]
}}

【参考资料】
{context}
"""
prompt = ChatPromptTemplate.from_template(RECOMMEND_TEMPLATE)

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# 组装流水线
recommend_chain = prompt | llm | StrOutputParser()


# ==========================================
# 核心业务逻辑：双数据库融合 (Vector DB + SQL DB)
# ==========================================
def get_recommendations(db: Session, tag: str) -> dict:
    """
    通过大模型生成路线，并与 SQLite/MySQL 中的真实 Spot ID 进行绑定。
    """
    print(f"\n🎯 [RecommendService] 收到智能路线请求，主题：{tag}")

    try:
        # 第一步：去 Chroma 向量库捞出知识点
        docs = retriever.invoke(f"适合{tag}主题的景点和游览路线")
        context = format_docs(docs)

        # 第二步：逼迫大模型吐出标准 JSON 格式的路线
        raw_response = recommend_chain.invoke({"tag": tag, "context": context})

        # 容错处理：清除大模型有时手贱加上的 markdown 代码块标记
        cleaned_json = re.sub(r"^```json\s*", "", raw_response, flags=re.IGNORECASE)
        cleaned_json = re.sub(r"\s*```$", "", cleaned_json)

        # 解析为 Python 字典
        llm_route = json.loads(cleaned_json)

        # 【修复点】防御：确保 llm_route 是 dict
        if not isinstance(llm_route, dict):
            raise ValueError(f"LLM 返回了非预期的类型: {type(llm_route)}")

        # 第三步：魔法时刻 🌟 —— 实体对齐
        # 大模型生成的只是文字，我们需要给它挂上真实的数据库 spot_id
        aligned_spots = []
        for spot in llm_route.get("spots", []):
            spot_name = spot.get("name", "")

            # 去关系型数据库里模糊查询，找真实的景点记录
            db_spot = db.query(Spot).filter(Spot.name.contains(spot_name)).first()

            aligned_spots.append({
                "spot_id": db_spot.spot_id if db_spot else f"ai_gen_{len(aligned_spots)}",
                "name": spot_name,
                "intro": spot.get("intro", ""),
                "highlight": spot.get("highlight", ""),
                "tag": db_spot.tag if db_spot else tag,
            })

        llm_route["spots"] = aligned_spots

        print("✅ 大模型结构化路线生成并对齐完毕！")

        return {
            "tag": tag,
            "routes": [llm_route],  # 完美贴合前端的 Array 结构
        }

    except Exception as e:
        print(f"❌ 推荐引擎解析失败，触发安全兜底逻辑: {e}")
        # 如果大模型抽风 JSON 解析失败，执行队友以前的兜底方案
        fallback_spots = db.query(Spot).filter(Spot.tag == tag).limit(3).all()
        return {
            "tag": tag,
            "routes": [{
                "name": f"{tag}经典探索",
                "type": tag,
                "duration": "随心游",
                "description": f"为您匹配了基础的{tag}精选景点",
                "spots": [
                    {
                        "spot_id": s.spot_id,
                        "name": s.name,
                        "intro": (s.detail or "")[:50],
                        "highlight": "精选推荐",
                        "tag": s.tag,
                    } for s in fallback_spots
                ],
            }] if fallback_spots else [],
        }
