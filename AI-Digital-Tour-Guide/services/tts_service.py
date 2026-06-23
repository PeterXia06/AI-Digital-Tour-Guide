"""
TTS 语音合成服务 — 阿里云百炼 CosyVoice 超拟人语音
纯血 tts_v2 引擎：CosyVoice 专属 WebSocket 通道，免疫 begin_time 解析 Bug。
🎭 多模态中枢版：根据全局 CURRENT_CHARACTER 动态选择音色。
"""
import os
import uuid
import dashscope
import config
from dashscope.audio.tts_v2 import SpeechSynthesizer

dashscope.api_key = config.DASHSCOPE_API_KEY

_OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "audio")


def generate_aliyun_tts(text: str) -> str:
    """
    tts_v2 引擎：自动处理 WebSocket 协议，返回纯净 MP3 字节流。
    🎭 动态读取当前激活角色的专属音色参数。
    """
    os.makedirs(_OUTPUT_DIR, exist_ok=True)

    # 🚨 动态拦截：抓取当前激活角色的专属 TTS 参数
    active_id = config.CURRENT_CHARACTER
    profile = config.CHARACTER_PROFILES.get(active_id, config.CHARACTER_PROFILES["hiyori"])
    tts_model = profile["tts_model"]
    tts_voice = profile["tts_voice"]
    char_name = profile["name"]

    file_name = f"response_{uuid.uuid4().hex[:8]}.mp3"
    file_path = os.path.join(_OUTPUT_DIR, file_name)

    print(f"[TTS] 🎭 当前角色 {char_name} → 音色 {tts_voice} | 模型 {tts_model}")
    print(f"[TTS] 🚀 合成文本: {text[:30]}...")

    try:
        synthesizer = SpeechSynthesizer(model=tts_model, voice=tts_voice)
        audio_bytes = synthesizer.call(text)

        with open(file_path, 'wb') as f:
            f.write(audio_bytes)

        audio_url = f"/static/audio/{file_name}"
        print(f"[TTS] ✅ 已落盘: {file_name} ({len(audio_bytes)} bytes)")
        return audio_url

    except Exception as e:
        print(f"[TTS] ❌ 合成失败: {e}")
        raise RuntimeError(f"百炼 TTS 调用失败: {e}")
