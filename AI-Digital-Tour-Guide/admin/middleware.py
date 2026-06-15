"""
Admin 鉴权中间件
"""
from fastapi import Request, HTTPException
from config import ADMIN_SECRET_KEY


async def admin_auth_middleware(request: Request):
    """
    简易 Token 鉴权中间件。
    所有 /api/admin/* 路径需要在 Header 中携带 X-Admin-Token。
    通过 FastAPI middleware 注册。
    """
    # 只拦截 /api/admin 路径
    if request.url.path.startswith("/api/admin"):
        token = request.headers.get("X-Admin-Token", "")
        if token != ADMIN_SECRET_KEY:
            raise HTTPException(status_code=403, detail="Forbidden: Invalid admin token")
