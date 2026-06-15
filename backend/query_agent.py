import os
# 导入 LangChain 核心组件
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.chat_models import ChatTongyi
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 1. 填入你的阿里云 API_KEY
os.environ["DASHSCOPE_API_KEY"] = "sk-91b5c2013f354bf78ebd2475fa23bd73"


def start_tour_guide_agent():
    print("🤖 正在唤醒灵山胜境专属 AI 导游...")

    # ==========================================
    # 组件 A：加载记忆（本地 ChromaDB 档案馆）
    # ==========================================
    embeddings = DashScopeEmbeddings(model="text-embedding-v3")
    db = Chroma(persist_directory="./chroma_db_final", embedding_function=embeddings)
    # 把数据库变成一个“检索器”，每次游客提问，捞出最相关的 3 张卡片
    retriever = db.as_retriever(search_kwargs={"k": 3})

    # ==========================================
    # 组件 B：加载大脑（通义千问大语言模型）
    # ==========================================
    # temperature=0.5 让导游的回答既准确又带有一点生动的情感
    llm = ChatTongyi(model="qwen-turbo", temperature=0.5)

    # ==========================================
    # 组件 C：设定人设（Prompt 模板）
    # ==========================================
    system_template = """你是一位热情、专业的“灵山胜境”专属AI导游。
你的任务是根据下面提供的【参考资料】来回答游客的问题。

【参考资料】
{context}

【导游守则】
1. 你的回答必须基于【参考资料】中的内容，不能瞎编乱造。
2. 如果参考资料里没有提到游客问的问题，你要礼貌地道歉，并说明资料有限。
3. 语气要像真实的导游一样亲切，可以直接用“您好”、“欢迎来到灵山”等词汇。

游客的问题是：{question}
"""
    prompt = ChatPromptTemplate.from_template(system_template)

    # ==========================================
    # 组件 D：组装 LCEL 黄金流水线 (LangChain 核心魔法)
    # ==========================================
    # 这一句代码，干了以前几百行代码才能干的事！
    def format_docs(docs):
        # 把捞出来的卡片拼成一段长文本
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
    )

    print("✅ 导游已就位，知识库已连接！\n")
    print("=" * 40)

    # ==========================================
    # 模拟前端游客提问
    # ==========================================
    # 你可以随便改这个测试问题，比如问灵山大佛多高，或者有什么好玩的
    user_question = "请问灵山大佛是用什么材质做的？大概有多高呀？"
    print(f"👤 游客提问：{user_question}")
    print("🎙️ AI 导游思考中 (翻阅资料)...\n")

    # 触发流水线，直接拿结果！
    result = rag_chain.invoke(user_question)
    print(f"🤖 导游回答：\n{result}")
    print("=" * 40)


if __name__ == "__main__":
    start_tour_guide_agent()