"""
数据库连接与初始化模块
- 本地开发：SQLite（sqlite:///./app.db）
- 生产环境：MySQL（通过 DATABASE_URL 注入）
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from config import DATABASE_URL

# ── 引擎创建 ──
# SQLite 需要 connect_args 和 poolclass 以确保跨线程安全
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    # SQLite 外键约束需要手动启用
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # MySQL / PostgreSQL 等
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_recycle=3600,
        echo=False,
    )

# ── 会话工厂 ──
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    FastAPI 依赖注入：获取数据库会话。
    请求结束后自动关闭。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    创建所有表（首次运行时调用）。
    安全操作：如果表已存在则跳过。
    """
    from models import Base
    Base.metadata.create_all(bind=engine)
    print(f"[DB] 数据库初始化完成 → {DATABASE_URL}")
