"""
TTS 语音合成服务
主方案：edge-tts（免费微软 Edge TTS，无需 API Key）
备方案：百炼 CosyVoice（需 DashScope 开通 HTTP TTS 权限）
"""
import os
import re
import io
import logging
import asyncio
from typing import Optional
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

logger = logging.getLogger(__name__)

TTS_PROVIDER = os.getenv("TTS_PROVIDER", "edge")  # "edge" 或 "dashscope"
TTS_VOICE = os.getenv("TTS_VOICE", "zh-CN-XiaoxiaoNeural")  # 微软中文女声，自然情感


def _clean_text(text: str) -> str:
    """清理文本，去除 markdown 符号"""
    text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)
    text = re.sub(r'[*#`\-_~>|]', '', text)
    text = re.sub(r'\n{2,}', '。', text)
    text = re.sub(r'\n', '。', text)
    text = re.sub(r'。{2,}', '。', text)
    return text.strip()


async def _edge_tts(text: str, voice: str) -> bytes:
    """使用 edge-tts 库合成语音"""
    import edge_tts

    clean = _clean_text(text)
    if not clean:
        raise RuntimeError("清理后文本为空")

    communicate = edge_tts.Communicate(clean, voice)
    chunks = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.append(chunk["data"])
    audio_bytes = b"".join(chunks)
    if not audio_bytes:
        raise RuntimeError("edge-tts 返回空音频")
    logger.info(f"edge-tts 合成成功，{len(audio_bytes)} bytes")
    return audio_bytes


async def _dashscope_tts(text: str, model: str, voice: str) -> bytes:
    """使用百炼 CosyVoice REST API 合成语音（需开通权限）"""
    import httpx

    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY 未配置")

    clean = _clean_text(text)
    payload = {
        "model": model,
        "input": {"text": clean},
        "parameters": {"voice": voice, "format": "mp3", "sample_rate": 22050},
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "https://dashscope.aliyuncs.com/api/v1/services/audio/tts/SpeechSynthesizer",
            json=payload,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        if resp.status_code != 200:
            raise RuntimeError(f"DashScope TTS 失败: HTTP {resp.status_code}")
        data = resp.json()
        audio_url = data.get("output", {}).get("audio_url")
        if not audio_url:
            raise RuntimeError(f"TTS 响应无 audio_url")
        dl = await client.get(audio_url)
        if dl.status_code != 200:
            raise RuntimeError(f"下载音频失败: HTTP {dl.status_code}")
        logger.info(f"DashScope TTS 合成成功，{len(dl.content)} bytes")
        return dl.content


async def text_to_speech(
    text: str,
    model: Optional[str] = None,
    voice: Optional[str] = None,
) -> bytes:
    """
    将文本转为 MP3 音频二进制数据。
    根据 TTS_PROVIDER 环境变量选择引擎（默认 edge-tts）。
    """
    provider = os.getenv("TTS_PROVIDER", TTS_PROVIDER)

    if provider == "dashscope":
        return await _dashscope_tts(
            text,
            model=model or os.getenv("TTS_MODEL", "cosyvoice-v1"),
            voice=voice or os.getenv("TTS_VOICE", "longxiaochun"),
        )
    else:
        return await _edge_tts(text, voice=voice or TTS_VOICE)
