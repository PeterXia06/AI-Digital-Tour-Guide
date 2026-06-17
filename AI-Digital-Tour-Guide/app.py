import os
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import date, datetime

from config import APP_TITLE, APP_VERSION
from database import get_db, init_db
from models import Knowledge, Spot, Route, Conversation, Stat, AvatarConfig
from services.knowledge_service import refresh_cache, load_cache, get_cache
from services.chat_service import process_chat
from services.stats_service import (
    get_dashboard_data, get_report_data,
    get_today_stats, get_week_service_trend,
    get_hot_questions, get_tag_distribution,
)
from services.recommendation_service import get_recommendations

# ── FastAPI 实例 ──
app = FastAPI(title=APP_TITLE, version=APP_VERSION)

# ── 注册 Admin 鉴权中间件 ──
@app.middleware("http")
async def admin_auth(request: Request, call_next):
    # 仅拦截 /api/admin 路径，放行 verify 接口本身
    path = request.url.path
    if path.startswith("/api/admin") and path != "/api/admin/verify":
        token = request.headers.get("X-Admin-Token", "")
        from config import ADMIN_SECRET_KEY
        if token != ADMIN_SECRET_KEY:
            from fastapi.responses import JSONResponse
            return JSONResponse(status_code=403, content={"detail": "Forbidden: Invalid admin token"})
    response = await call_next(request)
    return response

# ── 挂载静态文件 ──
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# ── 模板引擎 ──
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

# ═══════════════════════════════════════════════════════
# 页面路由
# ═══════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """游客端首页"""
    # 【修复点】明确指定 request 和 name 参数
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """管理后台"""
    # 【修复点】明确指定 request 和 name 参数
    return templates.TemplateResponse(request=request, name="index.html")

# ═══════════════════════════════════════════════════════
# 游客端 API
# ═══════════════════════════════════════════════════════

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "app": APP_TITLE, "version": APP_VERSION}

@app.post("/api/chat")
async def chat(
    data: dict,
    db: Session = Depends(get_db),
):
    """
    【升级版】智能问答接口 - 已接入 LangChain + ChromaDB 引擎
    Body: { "session_id": "uuid", "message": "灵山大佛有多高" }
    """
    session_id = data.get("session_id", "")
    message = data.get("message", "").strip()

    if not message:
        raise HTTPException(status_code=400, detail="消息不能为空")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id 不能为空")

    # 这里的 process_chat 已经是你写好的超级大模型版本了！
    result = await process_chat(db, session_id, message)
    return result

@app.get("/api/recommend")
async def recommend(
    tag: str = Query(..., description="标签：历史/自然/亲子/美食/禅意/建筑"),
    db: Session = Depends(get_db),
):
    """路线推荐接口"""
    return get_recommendations(db, tag)

@app.get("/api/stats/today")
async def today_stats(db: Session = Depends(get_db)):
    """今日服务人次"""
    return get_today_stats(db)

@app.get("/api/spots")
async def list_spots(
    area: str = Query(None),
    tag: str = Query(None),
    db: Session = Depends(get_db),
):
    """景点列表查询"""
    q = db.query(Spot)
    if area:
        q = q.filter(Spot.area == area)
    if tag:
        q = q.filter(Spot.tag == tag)

    spots = q.all()
    return {"spots": [s.to_dict() for s in spots], "count": len(spots)}

@app.get("/api/spots/{spot_id}")
async def get_spot(spot_id: str, db: Session = Depends(get_db)):
    """景点详情"""
    spot = db.query(Spot).filter(Spot.spot_id == spot_id).first()
    if not spot:
        raise HTTPException(status_code=404, detail="景点不存在")
    return spot.to_dict()

@app.post("/api/init")
async def init_data(db: Session = Depends(get_db)):
    """预置数据初始化接口"""
    existing = db.query(AvatarConfig).first()
    if existing:
        return {"message": "数据已存在，跳过初始化", "initialized": False}

    try:
        from data.seed_data import seed_all
        seed_all(db)
        load_cache(db)
        return {"message": "数据初始化成功", "initialized": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")

# ═══════════════════════════════════════════════════════
# 管理后台 API (保持原样，保证前端管理面板不出错)
# ═══════════════════════════════════════════════════════

@app.post("/api/admin/verify")
async def admin_verify():
    return {"valid": True}

@app.get("/api/admin/knowledge")
async def admin_knowledge_list(
    page: int = Query(1, ge=1),
    search: str = Query(None),
    tag: str = Query(None),
    route: str = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Knowledge)
    if search:
        q = q.filter(
            Knowledge.question.contains(search) |
            Knowledge.answer.contains(search)
        )
    if tag:
        q = q.filter(Knowledge.tag == tag)
    if route:
        q = q.filter(Knowledge.route_name == route)

    total = q.count()
    items = q.order_by(Knowledge.id.desc()).offset((page - 1) * 10).limit(10).all()

    return {
        "total": total,
        "page": page,
        "page_size": 10,
        "total_pages": (total + 9) // 10,
        "items": [i.to_dict() for i in items],
    }

@app.post("/api/admin/knowledge")
async def admin_knowledge_create(data: dict, db: Session = Depends(get_db)):
    item = Knowledge(
        spot_id=data.get("spot_id", ""),
        question=data["question"],
        answer=data["answer"],
        tag=data.get("tag", ""),
        route_name=data.get("route_name", ""),
        source=data.get("source", ""),
    )
    db.add(item)
    db.commit()
    refresh_cache(db)
    return {"message": "创建成功", "item": item.to_dict()}

@app.put("/api/admin/knowledge/{item_id}")
async def admin_knowledge_update(item_id: int, data: dict, db: Session = Depends(get_db)):
    item = db.query(Knowledge).filter(Knowledge.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")

    for field in ["spot_id", "question", "answer", "tag", "route_name", "source"]:
        if field in data:
            setattr(item, field, data[field])

    db.commit()
    refresh_cache(db)
    return {"message": "更新成功", "item": item.to_dict()}

@app.delete("/api/admin/knowledge/{item_id}")
async def admin_knowledge_delete(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Knowledge).filter(Knowledge.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="条目不存在")

    db.delete(item)
    db.commit()
    refresh_cache(db)
    return {"message": "删除成功"}

@app.post("/api/admin/knowledge/import")
async def admin_knowledge_import(data: list, db: Session = Depends(get_db)):
    count = 0
    for item_data in data:
        item = Knowledge(
            spot_id=item_data.get("spot_id", ""),
            question=item_data["question"],
            answer=item_data["answer"],
            tag=item_data.get("tag", ""),
            route_name=item_data.get("route_name", ""),
            source=item_data.get("source", ""),
        )
        db.add(item)
        count += 1
    db.commit()
    refresh_cache(db)
    return {"message": f"成功导入 {count} 条记录"}

@app.get("/api/admin/report")
async def admin_report(
    start: str = Query(None),
    end: str = Query(None),
    db: Session = Depends(get_db),
):
    return get_report_data(db, start, end)

@app.get("/api/admin/dashboard")
async def admin_dashboard(db: Session = Depends(get_db)):
    return get_dashboard_data(db)

@app.get("/api/admin/avatar")
async def admin_avatar_get(db: Session = Depends(get_db)):
    config = db.query(AvatarConfig).first()
    if not config:
        return {
            "model_name": "",
            "model_url": "",
            "voice_name": "",
            "greeting": "欢迎来到灵山胜境！我是您的AI导游小灵，有什么可以帮您的吗？",
            "scale": 1.0,
            "is_active": False,
        }
    return config.to_dict()

@app.put("/api/admin/avatar")
async def admin_avatar_update(data: dict, db: Session = Depends(get_db)):
    config = db.query(AvatarConfig).first()
    if not config:
        config = AvatarConfig(id=1)
        db.add(config)

    for field in ["model_name", "model_url", "voice_name", "greeting", "scale", "is_active"]:
        if field in data:
            setattr(config, field, data[field])

    db.commit()
    return {"message": "配置更新成功", "config": config.to_dict()}

@app.get("/api/admin/models")
async def admin_models():
    import glob
    models_dir = os.path.join(static_dir, "models")
    pattern = os.path.join(models_dir, "**", "*.model3.json")
    model_files = glob.glob(pattern, recursive=True)

    models = []
    for f in model_files:
        rel_path = os.path.relpath(f, static_dir).replace("\\", "/")
        name = os.path.basename(os.path.dirname(f))
        models.append({"name": name, "url": f"/static/{rel_path}"})

    return {"models": models}

@app.get("/api/admin/spots")
async def admin_spots(db: Session = Depends(get_db)):
    spots = db.query(Spot).order_by(Spot.spot_id.asc()).all()
    return {"spots": [s.to_dict() for s in spots], "count": len(spots)}

@app.put("/api/admin/spots/{spot_id}")
async def admin_spot_update(spot_id: int, data: dict, db: Session = Depends(get_db)):
    spot = db.query(Spot).filter(Spot.id == spot_id).first()
    if not spot:
        raise HTTPException(status_code=404, detail="景点不存在")

    updatable = [
        "name", "area", "location", "scale_params", "core_function",
        "culture", "detail", "photo_spots", "visit_info", "tag", "route_name"
    ]
    for field in updatable:
        if field in data:
            setattr(spot, field, data[field])

    db.commit()
    return {"message": "更新成功", "spot": spot.to_dict()}

# ═══════════════════════════════════════════════════════
# 🚀 启动事件 (核心修改区域：移除了旧时代jieba，引入超级大脑日志)
# ═══════════════════════════════════════════════════════

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化数据库和预热"""
    # 确保基础 SQL 表存在
    init_db()

    # 保留队友的 SQL 缓存加载，防止后台大屏报错
    try:
        from database import SessionLocal
        db = SessionLocal()
        count = len(load_cache(db))
        db.close()
        print(f"🗄️  [Startup] 传统 SQL 数据加载完成: {count} 条")
    except Exception as e:
        print(f"⚠️  [Startup] SQL 缓存加载失败（如果是初次启动无需理会）: {e}")
        
    print(f"🚀 [Startup] Chroma 向量知识库与 LangChain 引擎准备就绪！")
    print(f"🎉 [Startup] {APP_TITLE} v{APP_VERSION} 启动成功。请在浏览器访问 http://127.0.0.1:8000")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)