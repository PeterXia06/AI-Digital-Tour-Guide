#!/bin/bash
# Render 启动脚本
set -e

echo "[Init] 初始化数据库..."
python -c "from database import init_db; init_db()"

echo "[Init] 检查是否需要预置数据..."
python -c "
from database import SessionLocal
from models import AvatarConfig
db = SessionLocal()
exists = db.query(AvatarConfig).first()
db.close()
if exists:
    print('[Init] 数据已存在，跳过 seed')
else:
    print('[Init] 开始预置数据...')
    import subprocess
    subprocess.run(['python', 'data/seed_data.py'])
"

echo "[Start] 启动 FastAPI 服务..."
uvicorn app:app --host 0.0.0.0 --port "${PORT:-8000}"
