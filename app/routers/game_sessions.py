import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import database_models as models
from app.schemas import pydantic_schemas as schemas

# 创建游戏会话管理路由器
router = APIRouter(
    prefix="/api/v1/game",  # 路由前缀
    tags=["Game Sessions"],  # 在 API 文档中的标签分组
)

@router.post("/sessions", response_model=schemas.GameSession, status_code=201)
def create_game_session(session_create: schemas.GameSessionCreate, db: Session = Depends(get_db)):
    """
    创建新的游戏会话
    
    Args:
        session_create: 创建会话的请求对象，包含剧本ID和用户ID
        db: 数据库会话（依赖注入）
    
    Returns:
        GameSession: 新创建的游戏会话对象
        
    Raises:
        HTTPException: 当指定的剧本不存在时返回404错误
    """
    # 验证剧本是否存在
    script = db.query(models.Script).filter(models.Script.id == session_create.script_id).first()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    
    # 生成唯一的会话ID
    session_id = f"session_{uuid.uuid4()}"
    
    # 创建新的游戏会话对象
    new_session = models.GameSession(
        session_id=session_id,
        script_id=session_create.script_id,
        user_id=session_create.user_id,
    )
    
    # 保存到数据库
    db.add(new_session)
    db.commit()  # 提交事务
    db.refresh(new_session)  # 刷新对象以获取数据库生成的字段
    return new_session