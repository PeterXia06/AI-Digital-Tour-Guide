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

# ── 阿里云百炼 CosyVoice TTS ──
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
TTS_MODEL = os.getenv("TTS_MODEL", "cosyvoice-v1")
TTS_VOICE = os.getenv("TTS_VOICE", "longxiaochun")  # 龙小淳：超拟人元气女声（默认）

# ── 👥 多模态角色资产字典 ──
# 绑定 Live2D 模型路径与专属 TTS 音色，支持秒级热切换
CHARACTER_PROFILES = {
    "hiyori": {
        "name": "小灵 (元气女声)",
        "model_url": "/resources/live2d/hiyori/hiyori_free_t08.model3.json",
        "tts_model": "cosyvoice-v1",
        "tts_voice": "longxiaochun",       # 龙小淳：超拟人元气女声
        "scale": 0.18,                      # 自适应缩放倍率（会被引擎按画布高度微调）
        "y_offset": 100,                    # Y 轴偏移 px
    },
    "chitose": {
        "name": "千岁 (清朗男声)",
        "model_url": "/resources/live2d/chitose/chitose.model3.json",
        "tts_model": "cosyvoice-v1",
        "tts_voice": "longxiaocheng",       # 龙小诚：清亮阳光男声
        "scale": 0.12,
        "y_offset": 80,
    },
}

# 🚨 运行时状态：当前激活的角色 ID（默认 hiyori）
CURRENT_CHARACTER = os.getenv("CURRENT_CHARACTER", "hiyori")

# ── 应用设置 ──
APP_TITLE = "灵山胜境 AI 数字人导游"
APP_VERSION = "1.0.0"
