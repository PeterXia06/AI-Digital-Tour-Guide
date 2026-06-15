"""
预置数据初始化脚本
从 seed_data.json 读取数据并写入数据库。
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from sqlalchemy.orm import Session
from models import Spot, Knowledge, Route, Stat, AvatarConfig


def seed_all(db: Session):
    """执行全部预置数据插入"""
    json_path = os.path.join(os.path.dirname(__file__), "seed_data.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ── 景点 ──
    for s in data.get("spots", []):
        exists = db.query(Spot).filter(Spot.spot_id == s["spot_id"]).first()
        if not exists:
            db.add(Spot(**s))
    print(f"[Seed] 景点: {len(data.get('spots', []))} 条")

    # ── 路线 ──
    for r in data.get("routes", []):
        exists = db.query(Route).filter(Route.name == r["name"]).first()
        if not exists:
            db.add(Route(**r))
    print(f"[Seed] 路线: {len(data.get('routes', []))} 条")

    # ── 知识库 ──
    for k in data.get("knowledge", []):
        db.add(Knowledge(**k))
    print(f"[Seed] 知识库: {len(data.get('knowledge', []))} 条")

    # ── 统计数据 ──
    from datetime import date as date_type
    for s in data.get("stats", []):
        # Convert string date to Python date object
        s["date"] = date_type.fromisoformat(s["date"])
        exists = db.query(Stat).filter(Stat.date == s["date"]).first()
        if not exists:
            db.add(Stat(**s))
    print(f"[Seed] 统计: {len(data.get('stats', []))} 天")

    # ── 数字人配置 ──
    cfg = data.get("avatar_config")
    if cfg and not db.query(AvatarConfig).first():
        db.add(AvatarConfig(**cfg))
    print(f"[Seed] 数字人配置: 1 条")

    db.commit()
    print("[Seed] 全部预置数据写入完成!")


if __name__ == "__main__":
    from database import SessionLocal, init_db
    init_db()
    db = SessionLocal()
    try:
        seed_all(db)
        print("[Done] OK")
    finally:
        db.close()
