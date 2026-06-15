import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 导入 LangChain 组件
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ⚠️ 填入你的阿里云 API_KEY
os.environ["DASHSCOPE_API_KEY"] = "sk-91b5c2013f354bf78ebd2475fa23bd73"

# ==========================================
# 1. 初始化 FastAPI 引擎与跨域配置 (CORS)
# ==========================================
app = FastAPI(title="灵山胜境 AI 导游后端")

# 【避坑神器】：必须加跨域中间件，否则前端 Vue 会报 CORS 拦截错误！
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发阶段允许所有前端端口接入 (如 localhost:5173)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 2. 全局加载大模型与知识库 (避免每次提问都重新加载)
# ==========================================
print("🧠 正在启动后端服务器，预热灵山知识库...")
embeddings = DashScopeEmbeddings(model="text-embedding-v3")
db = Chroma(persist_directory="./chroma_db_final", embedding_function=embeddings)
retriever = db.as_retriever(search_kwargs={"k": 3})

llm = ChatTongyi(model="qwen-turbo", temperature=0.5)

system_template = """你是一位热情、专业的“灵山胜境”专属AI导游。
你的任务是根据下面提供的【参考资料】来回答游客的问题。

【参考资料】
{context}

【导游守则】
1. 必须基于【参考资料】回答，绝不瞎编。
2. 资料中没有的，礼貌致歉。
3. 语气亲切自然。

游客的问题是：{question}
"""
prompt = ChatPromptTemplate.from_template(system_template)


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# 构建全局唯一 Agent 流水线
rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
)
print("✅ 后端引擎就绪！随时准备接收前端请求。")


# ==========================================
# 3. 定义前端传过来的数据格式 (契约)
# ==========================================
class ChatRequest(BaseModel):
    question: str
    # 未来这里还可以加上队友传来的 interest_tag (风景/历史) 等参数


# ==========================================
# 4. 暴露核心 API 接口
# ==========================================
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    print(f"\n👤 收到前端游客提问：{request.question}")

    # 触发 LangChain 进行思考和生成
    answer = rag_chain.invoke(request.question)

    print(f"🤖 返回给前端的回答：{answer}")

    # 按照标准的 JSON 格式返回给前端
    return {
        "code": 200,
        "message": "success",
        "data": {
            "reply": answer
        }
    }


if __name__ == "__main__":
    import uvicorn

    # 启动服务器，运行在 8000 端口
    uvicorn.run(app, host="0.0.0.0", port=8000)