import requests
import json


def test_stream():
    # 你的 FastAPI 本地服务地址
    url = "http://127.0.0.1:8000/api/chat/stream"

    # 模拟前端发送过来的数据
    payload = {
        "text": "你好，请问迎客松在哪里？我今天比较喜欢看自然风景。",
        "image_url": "",  # 暂时留空
        "interest_tag": "scenery"  # 触发你的“自然风光”个性化提示词
    }

    print("🚀 正在向 FastAPI 发送流式请求，请稍候...\n")

    # 核心：设置 stream=True，像接自来水一样接数据
    response = requests.post(url, json=payload, stream=True)

    # 逐行读取后端流式吐出来的字
    for line in response.iter_lines():
        if line:
            # 解码获取到的二进制数据
            decoded_line = line.decode('utf-8')

            # 过滤掉 SSE 协议自带的 "data: " 前缀
            if decoded_line.startswith("data: "):
                text_chunk = decoded_line.replace("data: ", "")

                # 像 ChatGPT 一样，不换行、实时打印蹦出来的每一个字
                print(text_chunk, end="", flush=True)


if __name__ == "__main__":
    test_stream()