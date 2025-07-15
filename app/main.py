from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine
from app.models import database_models
from app.routers import scripts, game_sessions, ai_dialogue

# 创建数据库表（如果不存在）
database_models.Base.metadata.create_all(bind=engine)

# 创建 FastAPI 应用实例
app = FastAPI(
    title="Visual Novel Backend API",  # API 标题
    description="Backend API for Vue.js Visual Novel Game",  # API 描述
    version="1.0.0",  # API 版本
)

# 配置跨域资源共享（CORS）中间件
origins = [
    "http://localhost:3000","http://localhost:3001"
]
# 允许前端应用从不同域名访问 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许访问的源
    allow_credentials=True,  # 支持 cookie
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有标头
)

# 注册路由模块
app.include_router(scripts.router)  # 剧本管理相关路由
app.include_router(game_sessions.router)  # 游戏会话相关路由
app.include_router(ai_dialogue.router)  # AI对话相关路由

@app.get("/", tags=["Root"])
def read_root():
    """
    根路径端点
    返回 API 欢迎信息
    """
    return {"message": "Welcome to the Visual Novel Backend API!"}