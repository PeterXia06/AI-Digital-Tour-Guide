import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from data_processor import load_and_process_scenic_docs

# 【核心警告】：务必填入你和队友申请的真实阿里云 API_KEY
os.environ["DASHSCOPE_API_KEY"] = "sk-91b5c2013f354bf78ebd2475fa23bd73"


def build_vector_database():
    print("🔥 终极阶段：开始构建灵山专属高维记忆档案馆...")

    # 🎯 核心修改：动态算出 data/scene 的绝对路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    scene_dir = os.path.normpath(os.path.join(current_dir, "../data/scene"))

    print(f"📍 锁定目标弹药库: {scene_dir}")

    # 1. 召唤切分器，明确指定去 scene 文件夹拿数据
    chunks = load_and_process_scenic_docs(data_dir=scene_dir)

    if not chunks:
        print("❌ 错误：没有获取到任何卡片，请检查 data/scene 文件夹是否为空。")
        return

    # 2. 召唤阿里云的 Embedding 数学家
    print(f"\n🧠 成功提取 {len(chunks)} 张纯血统卡片！正在连接阿里云数学引擎...")
    embeddings = DashScopeEmbeddings(model="text-embedding-v3")

    # 3. 终极大招：存入 ChromaDB
    persist_dir = "./chroma_db_final"
    print(f"🚀 开始将卡片高维化并写入本地数据库 ({persist_dir})...")

    # 初始化一个空的本地数据库文件夹
    db = Chroma(embedding_function=embeddings, persist_directory=persist_dir)

    # 分批写入（如果只有几十张卡片，瞬间就能跑完）
    batch_size = 100
    total_chunks = len(chunks)
    for i in range(0, total_chunks, batch_size):
        batch_chunks = chunks[i: i + batch_size]
        db.add_documents(batch_chunks)
        print(f"📦 进度: 已归档 {min(i + batch_size, total_chunks)} / {total_chunks} 张卡片...")

    print(f"\n🎉 伟大工程完毕！全部数据已封印至本地。你的 Agent 已经拥有了灵山的完整记忆！")


if __name__ == "__main__":
    build_vector_database()