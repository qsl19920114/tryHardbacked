import time
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import pydantic_schemas as schemas
from app.services.dify_service import call_dify_chatflow
from app.models import database_models as models

# 创建 AI 对话路由器
router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI Dialogue"],
)

def format_history_for_prompt(history: list[models.DialogueEntry]) -> str:
    """
    将对话历史格式化为字符串，供 AI 模型使用。
    
    Args:
        history: 包含 DialogueEntry 的列表
        
    Returns:
        str: 格式化后的对话文本
    """
    prompt_lines = []
    for entry in history:
        role_name = "玩家" if entry.role == 'player' else f"角色 {entry.character_id}"
        prompt_lines.append(f"{role_name}: {entry.content}")
    return "\n".join(prompt_lines)


@router.post("/dialogue", response_model=schemas.DialogueResponse)
def post_dialogue(request: schemas.DialogueRequest, db: Session = Depends(get_db)):
    start_time = time.time()

    # 1. 获取游戏会话
    session = db.query(models.GameSession).filter(
        models.GameSession.session_id == request.session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")

    # 2. 获取历史对话记录并格式化为 prompt
    formatted_prompt = format_history_for_prompt(
        history=session.dialogue_entries  # 使用关联的 dialogue_entries
    )

    # 3. 调用 Dify AI 服务获取回答
    ai_answer = call_dify_chatflow(
        request,
        user_id=request.session_id,
        formatted_prompt=formatted_prompt  # 假设你已将 prompt 传入服务中
    )

    # 4. 创建新的对话记录 (DialogueEntry)
    player_entry = models.DialogueEntry(
        session_id=session.session_id,
        character_id="player",
        role="player",
        content=request.question,
        timestamp=datetime.now(timezone.utc)
    )

    ai_entry = models.DialogueEntry(
        session_id=session.session_id,
        character_id=request.character_id,
        role="ai",
        content=ai_answer,
        timestamp=datetime.now(timezone.utc)
    )

    # 5. 添加并提交新记录
    db.add(player_entry)
    db.add(ai_entry)
    db.commit()

    end_time = time.time()

    # 6. 构建响应
    response = schemas.DialogueResponse(
        response_id=f"resp_{uuid.uuid4()}",
        session_id=request.session_id,
        question=request.question,
        answer=ai_answer,
        response_time=round(end_time - start_time, 2),
        created_at=datetime.utcnow()
    )

    return response