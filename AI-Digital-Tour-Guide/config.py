"""
应用配置模块
从环境变量读取所有配置项，提供默认值。
"""
import os
from pathlib import Path

# 自动加载项目根目录下的 .env 文件
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / ".env"
    load_dotenv(env_path)
except ImportError:
    pass

# ── 数据库 ──
# Render 部署时自动注入 DATABASE_URL（MySQL），本地留空则默认 SQLite
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./app.db"
)

# ── DeepSeek API ──
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv(
    "DEEPSEEK_BASE_URL",
    "https://api.deepseek.com/v1"
)
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# ── Admin 鉴权 ──
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", "lingshan-admin-2026")

# ── Azure TTS（可选） ──
AZURE_TTS_KEY = os.getenv("AZURE_TTS_KEY", "")
AZURE_TTS_REGION = os.getenv("AZURE_TTS_REGION", "eastasia")

# ── TTS 语音合成 ──
# TTS_PROVIDER: "edge" (免费微软 Edge TTS) 或 "dashscope" (百炼 CosyVoice)
TTS_PROVIDER = os.getenv("TTS_PROVIDER", "edge")
TTS_VOICE = os.getenv("TTS_VOICE", "zh-CN-XiaoxiaoNeural")  # 微软中文女声
TTS_MODEL = os.getenv("TTS_MODEL", "cosyvoice-v1")  # 仅 dashscope 模式使用
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

# ── 应用设置 ──
APP_TITLE = "灵山胜境 AI 数字人导游"
APP_VERSION = "1.0.0"
