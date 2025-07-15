from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import DATABASE_URL

# 创建数据库引擎
# connect_args 参数解决 SQLite 多线程访问问题
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# 创建数据库会话工厂
# autocommit=False: 手动控制事务提交
# autoflush=False: 手动控制数据刷新到数据库
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建数据库模型基类
Base = declarative_base()

def get_db():
    """
    获取数据库会话的依赖注入函数
    用于 FastAPI 的 Depends 系统，确保每个请求都有独立的数据库会话
    """
    db = SessionLocal()
    try:
        yield db  # 返回数据库会话
    finally:
        db.close()  # 请求结束后关闭会话