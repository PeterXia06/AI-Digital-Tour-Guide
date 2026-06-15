"""
Admin 鉴权中间件
校验请求 Header 中的 X-Admin-Token
"""


def verify_admin_token(token: str) -> bool:
    """验证管理后台 Token"""
    from config import ADMIN_SECRET_KEY
    return token == ADMIN_SECRET_KEY
