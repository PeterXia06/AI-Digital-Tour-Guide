"""
ORM 模型定义
6张表：Spot / Knowledge / Route / Conversation / Stat / AvatarConfig
所有字段类型兼容 SQLite 和 MySQL。
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Text, Float, Date, DateTime,
    Boolean, JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# ──────────────────────────────────────────────
# 1. Spot — 景点表（22条灵山+拈花湾景点数据）
# ──────────────────────────────────────────────
class Spot(Base):
    __tablename__ = "spot"

    id = Column(Integer, primary_key=True, autoincrement=True)
    spot_id = Column(String(10), unique=True, nullable=False, index=True)  # LS-001, NH-001
    name = Column(String(100), nullable=False)
    area = Column(String(50), nullable=False)            # 灵山胜境 / 拈花湾禅意小镇
    location = Column(Text)
    scale_params = Column(Text)                          # 建筑/景观参数
    core_function = Column(Text)                         # 核心功能
    culture = Column(Text)                               # 文化内涵
    detail = Column(Text)                                # 详细介绍
    photo_spots = Column(Text)                           # 最佳打卡点
    visit_info = Column(Text)                            # 参观时间/注意事项
    tag = Column(String(50), index=True)
    route_name = Column(String(100), index=True)
    create_time = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ──────────────────────────────────────────────
# 2. Knowledge — 知识库 FAQ 表
# ──────────────────────────────────────────────
class Knowledge(Base):
    __tablename__ = "knowledge"

    id = Column(Integer, primary_key=True, autoincrement=True)
    spot_id = Column(String(10), index=True)             # 关联 Spot.spot_id
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    tag = Column(String(50), index=True)
    route_name = Column(String(100), index=True)
    source = Column(String(255))                         # 答案来源标注
    create_time = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ──────────────────────────────────────────────
# 3. Route — 游览路线表（3条官方路线）
# ──────────────────────────────────────────────
class Route(Base):
    __tablename__ = "route"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    type = Column(String(50), nullable=False)            # 历史 / 自然 / 亲子
    duration = Column(String(20))                        # 预计时长
    description = Column(Text)                           # 路线概述
    stop_order = Column(JSON)                            # 景点序列 ["LS-001",...]
    highlights = Column(JSON)                            # 每个停靠点的讲解重点
    create_time = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ──────────────────────────────────────────────
# 4. Conversation — 对话记录
# ──────────────────────────────────────────────
class Conversation(Base):
    __tablename__ = "conversation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), index=True)
    user_input = Column(Text, nullable=False)
    bot_answer = Column(Text, nullable=False)
    source = Column(String(50))                          # knowledge_base / deepseek
    emotion = Column(String(20))                         # positive / negative / neutral
    create_time = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ──────────────────────────────────────────────
# 5. Stat — 每日统计
# ──────────────────────────────────────────────
class Stat(Base):
    __tablename__ = "stat"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False)
    service_count = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)

    def to_dict(self):
        return {c.name: (
            getattr(self, c.name).isoformat()
            if isinstance(getattr(self, c.name), date)
            else getattr(self, c.name)
        ) for c in self.__table__.columns}


# ──────────────────────────────────────────────
# 6. AvatarConfig — 数字人配置（单行）
# ──────────────────────────────────────────────
class AvatarConfig(Base):
    __tablename__ = "avatar_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_name = Column(String(50))
    model_url = Column(String(255))
    voice_name = Column(String(100))
    greeting = Column(String(255))
    scale = Column(Float, default=1.0)
    is_active = Column(Boolean, default=True)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# ──────────────────────────────────────────────
# 复合索引（优化查询）
# ──────────────────────────────────────────────
Index("idx_conv_session_time", Conversation.session_id, Conversation.create_time)
Index("idx_conv_emotion_time", Conversation.emotion, Conversation.create_time)
Index("idx_stat_date", Stat.date)
