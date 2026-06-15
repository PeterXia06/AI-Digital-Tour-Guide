"""
统计服务
- 数据大屏聚合查询
- 情感报告查询
"""
from datetime import date, datetime, timedelta
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func

from models import Conversation, Stat, Knowledge


def get_today_stats(db: Session) -> dict:
    """获取今日服务人次"""
    today = date.today()
    stat = db.query(Stat).filter(Stat.date == today).first()
    return {
        "date": today.isoformat(),
        "service_count": stat.service_count if stat else 0,
    }


def get_week_service_trend(db: Session) -> list:
    """获取最近7天服务趋势"""
    today = date.today()
    start = today - timedelta(days=6)
    stats = db.query(Stat).filter(
        Stat.date >= start,
        Stat.date <= today
    ).order_by(Stat.date.asc()).all()

    # 补齐缺失日期
    result = []
    stat_map = {s.date: s for s in stats}
    for i in range(7):
        d = start + timedelta(days=i)
        s = stat_map.get(d)
        result.append({
            "date": d.isoformat(),
            "service_count": s.service_count if s else 0,
            "positive_count": s.positive_count if s else 0,
            "negative_count": s.negative_count if s else 0,
            "neutral_count": s.neutral_count if s else 0,
        })
    return result


def get_emotion_trend(db: Session, start_date: str = None, end_date: str = None) -> list:
    """获取情感趋势数据（按天汇总）"""
    if not start_date:
        start_date = (date.today() - timedelta(days=6)).isoformat()
    if not end_date:
        end_date = date.today().isoformat()

    results = db.query(
        func.date(Conversation.create_time).label("day"),
        Conversation.emotion,
        func.count(Conversation.id).label("cnt")
    ).filter(
        func.date(Conversation.create_time) >= start_date,
        func.date(Conversation.create_time) <= end_date,
    ).group_by("day", Conversation.emotion).all()

    # 整理为按天的结构
    day_map = {}
    for row in results:
        d = row.day.isoformat() if isinstance(row.day, date) else str(row.day)
        if d not in day_map:
            day_map[d] = {"date": d, "positive": 0, "negative": 0, "neutral": 0}
        day_map[d][row.emotion] = row.cnt

    return sorted(day_map.values(), key=lambda x: x["date"])


def get_hot_questions(db: Session, limit: int = 5) -> list:
    """获取热门问题 TOP-N（按相同 user_input 出现次数统计）"""
    results = db.query(
        Conversation.user_input,
        func.count(Conversation.id).label("cnt")
    ).group_by(Conversation.user_input).order_by(
        func.count(Conversation.id).desc()
    ).limit(limit).all()

    return [{"question": r[0], "count": r[1]} for r in results]


def get_tag_distribution(db: Session) -> list:
    """获取知识库标签分布（饼图数据）"""
    results = db.query(
        Knowledge.tag,
        func.count(Knowledge.id).label("cnt")
    ).group_by(Knowledge.tag).all()

    return [{"name": r[0] or "未分类", "value": r[1]} for r in results]


def get_dashboard_data(db: Session) -> dict:
    """聚合数据大屏所需全部数据"""
    return {
        "today": get_today_stats(db),
        "week_trend": get_week_service_trend(db),
        "emotion_trend": get_emotion_trend(db),
        "hot_questions": get_hot_questions(db),
        "tag_distribution": get_tag_distribution(db),
    }


def get_report_data(db: Session, start_date: str = None, end_date: str = None) -> dict:
    """获取情感报告数据"""
    if not start_date:
        start_date = (date.today() - timedelta(days=6)).isoformat()
    if not end_date:
        end_date = date.today().isoformat()

    # 情感趋势
    trend = get_emotion_trend(db, start_date, end_date)

    # 最近对话记录
    recent_convs = db.query(Conversation).filter(
        func.date(Conversation.create_time) >= start_date,
        func.date(Conversation.create_time) <= end_date,
    ).order_by(Conversation.create_time.desc()).limit(20).all()

    # 汇总计数
    positive = sum(1 for c in recent_convs if c.emotion == "positive")
    negative = sum(1 for c in recent_convs if c.emotion == "negative")
    neutral = sum(1 for c in recent_convs if c.emotion == "neutral")

    return {
        "summary": {
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
        },
        "trend": trend,
        "recent_conversations": [c.to_dict() for c in recent_convs],
    }
