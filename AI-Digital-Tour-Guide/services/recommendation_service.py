"""
路线推荐服务
根据标签匹配对应的游览路线及景点序列。
"""
from typing import Optional
from sqlalchemy.orm import Session

from models import Route, Spot


def get_recommendations(db: Session, tag: str) -> dict:
    """
    按标签获取路线推荐。

    参数：
        tag: 标签名（历史/自然/亲子/美食/禅意/建筑）

    返回：
        {
            "tag": str,
            "routes": [
                {
                    "name": str,
                    "type": str,
                    "duration": str,
                    "description": str,
                    "spots": [
                        {"spot_id": str, "name": str, "intro": str, "highlight": str}
                    ]
                }
            ]
        }
    """
    # 查找匹配的路线
    routes = db.query(Route).filter(Route.type == tag).all()

    # 如果按 type 没找到，尝试按 name 模糊匹配（如 tag="自然" 匹配 route_name 含 "自然"）
    if not routes:
        routes = db.query(Route).filter(Route.name.contains(tag)).all()

    result_routes = []
    for route in routes:
        route_dict = route.to_dict()
        spots_data = []

        # 按 stop_order 顺序获取景点信息
        stop_order = route_dict.get("stop_order", [])
        highlights = route_dict.get("highlights", {}) or {}

        for i, spot_id in enumerate(stop_order):
            spot = db.query(Spot).filter(Spot.spot_id == spot_id).first()
            if spot:
                spots_data.append({
                    "spot_id": spot.spot_id,
                    "name": spot.name,
                    "intro": (spot.detail or spot.culture or "")[:150] + "...",
                    "highlight": highlights.get(spot_id, highlights.get(str(i), "")),
                    "tag": spot.tag,
                })

        result_routes.append({
            "name": route_dict["name"],
            "type": route_dict["type"],
            "duration": route_dict["duration"],
            "description": route_dict["description"],
            "spots": spots_data,
        })

    # 如果没有匹配路线，按 tag 找相关景点作为fallback
    if not result_routes:
        spots = db.query(Spot).filter(Spot.tag == tag).limit(10).all()
        if spots:
            result_routes.append({
                "name": f"{tag}主题精选",
                "type": tag,
                "duration": "自由安排",
                "description": f"为您精选了{tag}相关的景点",
                "spots": [
                    {
                        "spot_id": s.spot_id,
                        "name": s.name,
                        "intro": (s.detail or s.culture or "")[:150] + "...",
                        "highlight": "",
                        "tag": s.tag,
                    }
                    for s in spots
                ],
            })

    return {
        "tag": tag,
        "routes": result_routes,
    }
