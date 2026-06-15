import os
from langchain_community.document_loaders import Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 🎯 动态路径引擎：直接锁定 data/scene 专属文件夹
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCENE_DIR = os.path.normpath(os.path.join(CURRENT_DIR, "../data/scene"))


def load_and_process_scenic_docs(data_dir=SCENE_DIR):
    print(f"📂 正在扫描专属目标弹药库 [{data_dir}] ...")

    raw_word_docs = []

    # 1. 遍历文件夹，现在我们只认 Word 文档
    if not os.path.exists(data_dir):
        print(f"❌ 严重错误：找不到目录 {data_dir}")
        return []

    for filename in os.listdir(data_dir):
        file_path = os.path.join(data_dir, filename)

        if filename.endswith(".docx"):
            print(f"📝 成功锁定并读取 Word 文件: {filename}")
            loader = Docx2txtLoader(file_path)
            raw_word_docs.extend(loader.load())
        else:
            # 如果里面不小心混进了别的格式，直接忽略
            print(f"⚠️ 忽略非 Word 文件: {filename}")

    if not raw_word_docs:
        print("❌ 警告：在目标文件夹中没有找到任何 .docx 格式的资料！")
        return []

    # 2. 对提取出来的长文本进行防打断切片
    print("🔪 正在启动智能切片引擎...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=50,
        length_function=len,
        separators=["\n\n", "\n", "。", "！", "？", "，", "、", ""]
    )

    final_chunks = text_splitter.split_documents(raw_word_docs)

    print(f"🎯 数据处理彻底完成！")
    print(f"   - 共从 Word 文档中切分出 {len(final_chunks)} 张纯血统知识卡片")

    return final_chunks


if __name__ == "__main__":
    # 独立运行测试逻辑
    chunks = load_and_process_scenic_docs()

    print("\n---  成果抽样检查 ---")
    if chunks:
        print("【灵山专属知识卡片示例】")
        print(chunks[0].page_content)