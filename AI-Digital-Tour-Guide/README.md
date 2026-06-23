# 🏯 灵山胜境 AI 数字人导游

基于 FastAPI + Live2D + DeepSeek 的智能景区导览系统。

## 技术栈

| 层级 | 技术                                    |
|------|---------------------------------------|
| 后端 | Python / FastAPI                      |
| 数据库 | Chroma/SQLite（本地）/ MySQL（生产）          |
| 前端 | TailwindCSS / ECharts / 原生 JS         |
| 数字人 | easy-live2d（Live2D 渲染 + 口型同步）         |
| 语音 | Web Speech API（识别）+ SpeechSynthesis（合成） |
| 大模型 | DeepSeek API（RAG 兜底）/阿里               |
| 分词 |  LangChain 的 RecursiveCharacterTextSplitter                                       |
| 部署 | Render.com                            |

## 快速开始

```bash
# 1. 虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 环境配置
cp .env.example .env
# 编辑 .env，填写 DEEPSEEK_API_KEY

# 4. 初始化数据库并预置数据
python -c "from database import init_db; init_db()"
python data/seed_data.py

# 5. 启动
uvicorn app:app --reload --port 8000
```

## 访问地址

| 页面 | URL |
|------|-----|
| 游客端 | http://localhost:8000/ |
| 管理后台 | http://localhost:8000/admin |
| API 文档 | http://localhost:8000/docs |

## 管理后台 Token

默认：`lingshan-admin-2026`（通过环境变量 `ADMIN_SECRET_KEY` 修改）

## 项目结构

```
├── app.py                  # FastAPI 主应用
├── models.py               # ORM 模型（Spot/Knowledge/Route/Conversation/Stat/AvatarConfig）
├── database.py             # 数据库连接 + 会话管理
├── config.py               # 环境变量配置
├── requirements.txt        # Python 依赖
├── start.sh                # Render 启动脚本
├── render.yaml             # Render 部署配置
├── services/
│   ├── knowledge_service.py    # 知识库检索（jieba + 内存缓存）
│   ├── chat_service.py         # 双阶段问答 + 情感分析
│   ├── stats_service.py        # 统计数据查询
│   └── recommendation_service.py # 路线推荐
├── admin/
│   ├── __init__.py
│   └── middleware.py       # Admin Token 鉴权
├── data/
│   └── seed_data.py        # 预置数据初始化
├── templates/
│   ├── index.html          # 游客端
│   └── admin.html          # 管理后台
└── static/
    ├── css/style.css
    ├── js/
    │   ├── chat.js         # 游客端 JS
    │   └── admin.js        # 管理后台 JS
    ├── models/             # Live2D 模型目录
    └── images/             # 静态图片
```

## API 概览

### 游客端
- `POST /api/chat` — 智能问答
- `GET /api/recommend?tag=xxx` — 路线推荐
- `GET /api/spots` — 景点列表
- `GET /api/spots/{spot_id}` — 景点详情
- `GET /api/stats/today` — 今日服务人次
- `POST /api/init` — 预置数据初始化

### 管理后台（需 Token）
- `GET /api/admin/dashboard` — 数据大屏
- `GET /api/admin/knowledge` — 知识库管理
- `GET /api/admin/report` — 情感报告
- `GET/PUT /api/admin/avatar` — 数字人配置

## 部署到 Render

1. Fork 本项目到 GitHub
2. 在 Render 创建 Web Service，连接仓库
3. Render 自动识别 `render.yaml` 配置
4. 设置环境变量 `DEEPSEEK_API_KEY` 和 `ADMIN_SECRET_KEY`
5. 部署完成后访问 `POST /api/init` 预置数据

## 验收标准

- [x] 双阶段问答（知识库 + DeepSeek 兜底）
- [x] 语音输入/输出（Web Speech API）
- [x] Live2D 数字人展示
- [x] 路线推荐（3条路线 × 22个景点）
- [x] 管理后台 CRUD
- [x] 数据大屏（ECharts 图表）
- [x] 情感分析报告
- [x] SQLite / MySQL 双环境兼容
- [x] Render 一键部署
