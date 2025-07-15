import time
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import pydantic_schemas as schemas
from app.services.dify_service import call_dify_chatflow
from app.models import database_models as models

# 创建 AI 对话路由器
router = APIRouter(
    prefix="/api/v1/ai",  # 路由前缀
    tags=["AI Dialogue"],  # 在 API 文档中的标签分组
)

@router.post("/dialogue", response_model=schemas.DialogueResponse)
def post_dialogue(request: schemas.DialogueRequest, db: Session = Depends(get_db)):
    """
    处理用户与 AI 的对话交互
    
    Args:
        request: 对话请求对象，包含会话ID和用户问题
        db: 数据库会话（依赖注入）
    
    Returns:
        DialogueResponse: 包含 AI 回答和响应时间的对话响应对象
        
    Raises:
        HTTPException: 当游戏会话不存在时返回404错误
    """
    start_time = time.time()  # 记录开始时间，用于计算响应时间

    # 验证游戏会话是否存在
    session = db.query(models.GameSession).filter(models.GameSession.session_id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")

    # 调用 Dify AI 服务获取回答
    ai_answer = call_dify_chatflow(request, user_id=request.session_id)
    
    end_time = time.time()  # 记录结束时间
    
    # 构建对话历史记录条目
    history_entry = {
        "question": request.question,  # 用户的问题
        "answer": ai_answer,  # AI 的回答
        "timestamp": datetime.utcnow().isoformat()  # 时间戳
    }
    
    # 更新游戏会话的对话历史
    current_history = session.dialogue_history or []  # 获取当前历史记录（如果为空则初始化为空列表）
    current_history.append(history_entry)  # 添加新的对话记录
    session.dialogue_history = current_history  # 更新会话的对话历史
    
    db.commit()  # 提交数据库事务

    # 构建响应对象
    response = schemas.DialogueResponse(
        response_id=f"resp_{uuid.uuid4()}",  # 生成唯一的响应ID
        session_id=request.session_id,  # 会话ID
        question=request.question,  # 用户的问题
        answer=ai_answer,  # AI 的回答
        response_time=round(end_time - start_time, 2),  # 响应时间（秒，保留2位小数）
        created_at=datetime.utcnow()  # 创建时间
    )

    return response