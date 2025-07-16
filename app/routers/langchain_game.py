"""
LangChain-based game router for murder mystery game.

This module provides FastAPI endpoints that integrate with the LangChain game engine,
offering a new API layer for advanced game orchestration while maintaining
compatibility with the existing frontend.
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import pydantic_schemas as schemas
from app.langchain.engine.game_engine import GameEngine, GameEngineError
from app.langchain.state.models import GamePhase
from app.langchain.engine.nodes import GamePhaseNodes

logger = logging.getLogger(__name__)

# 创建 LangChain 游戏路由器
router = APIRouter(
    prefix="/api/v1/langchain-game",
    tags=["LangChain Game Engine"],
)


@router.post("/start", response_model=schemas.GameActionResponse, status_code=201)
def start_new_game(
    request: schemas.GameStartRequest,
    db: Session = Depends(get_db)
):
    """
    启动新的游戏会话
    
    Args:
        request: 游戏启动请求，包含剧本ID和用户ID
        db: 数据库会话（依赖注入）
    
    Returns:
        GameActionResponse: 包含新游戏状态的响应
        
    Raises:
        HTTPException: 当游戏创建失败时返回400错误
    """
    try:
        logger.info(f"Starting new LangChain game with script {request.script_id}")
        
        # 创建游戏引擎实例
        game_engine = GameEngine(db)
        
        # 启动新游戏
        game_state = game_engine.start_new_game(
            script_id=request.script_id,
            user_id=request.user_id
        )
        
        # 构建响应
        game_state_response = schemas.GameStateResponse(
            game_id=game_state.game_id,
            script_id=game_state.script_id,
            session_id=game_state.session_id,
            current_act=game_state.current_act,
            current_phase=game_state.current_phase.value,
            max_acts=game_state.max_acts,
            player_count=len(game_state.players),
            character_count=len(game_state.characters),
            created_at=game_state.created_at,
            updated_at=game_state.updated_at,
            started_at=game_state.started_at,
            completed_at=game_state.completed_at
        )
        
        response = schemas.GameActionResponse(
            success=True,
            message=f"游戏 {game_state.game_id} 创建成功",
            data={
                "session_id": game_state.session_id,
                "available_characters": list(game_state.characters.keys())
            },
            game_state=game_state_response
        )
        
        logger.info(f"Successfully started game {game_state.game_id}")
        return response
        
    except GameEngineError as e:
        logger.error(f"Game engine error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error starting game: {e}")
        raise HTTPException(status_code=500, detail="Failed to start game")


@router.post("/session/{session_id}/join", response_model=schemas.GameActionResponse)
def join_game(
    session_id: str = Path(..., description="游戏会话ID"),
    request: schemas.PlayerJoinRequest = ...,
    db: Session = Depends(get_db)
):
    """
    玩家加入游戏会话
    
    Args:
        session_id: 游戏会话ID
        request: 玩家加入请求
        db: 数据库会话（依赖注入）
    
    Returns:
        GameActionResponse: 加入结果响应
    """
    try:
        logger.info(f"Player {request.player_id} joining game session {session_id}")
        
        game_engine = GameEngine(db)
        
        # 加载游戏状态
        game_state = game_engine.load_game(session_id)
        if not game_state:
            raise HTTPException(status_code=404, detail="Game session not found")
        
        # 添加玩家
        success = game_engine.add_player(
            session_id=session_id,
            player_id=request.player_id,
            character_id=request.character_id
        )
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to add player to game")
        
        # 重新加载更新后的游戏状态
        updated_game_state = game_engine.load_game(session_id)
        
        response = schemas.GameActionResponse(
            success=True,
            message=f"玩家 {request.player_id} 成功加入游戏",
            data={
                "player_id": request.player_id,
                "character_id": request.character_id,
                "turn_order": updated_game_state.turn_order
            }
        )
        
        logger.info(f"Player {request.player_id} successfully joined game {session_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error adding player to game: {e}")
        raise HTTPException(status_code=500, detail="Failed to join game")


@router.post("/session/{session_id}/action", response_model=schemas.GameActionResponse)
def process_game_action(
    session_id: str = Path(..., description="游戏会话ID"),
    request: schemas.GameActionRequest = ...,
    db: Session = Depends(get_db)
):
    """
    处理游戏动作
    
    Args:
        session_id: 游戏会话ID
        request: 游戏动作请求
        db: 数据库会话（依赖注入）
    
    Returns:
        GameActionResponse: 动作处理结果响应
    """
    try:
        logger.info(f"Processing action {request.action_type} for session {session_id}")
        
        game_engine = GameEngine(db)
        
        # 构建动作字典
        action = {
            "action_type": request.action_type,
            "player_id": request.player_id,
            "character_id": request.character_id,
            "question": request.question,
            "content": request.content,
            "mission_type": request.mission_type,
            "target_phase": request.target_phase,
            "model_name": request.model_name,
            "user_id": request.user_id,
            "is_public": request.is_public
        }
        
        # 处理动作
        result = game_engine.process_action(session_id, action)
        
        if "error" in result:
            return schemas.GameActionResponse(
                success=False,
                error=result["error"]
            )
        
        # 获取更新后的游戏状态
        updated_game_state = game_engine.load_game(session_id)
        if updated_game_state:
            game_state_response = schemas.GameStateResponse(
                game_id=updated_game_state.game_id,
                script_id=updated_game_state.script_id,
                session_id=updated_game_state.session_id,
                current_act=updated_game_state.current_act,
                current_phase=updated_game_state.current_phase.value,
                max_acts=updated_game_state.max_acts,
                player_count=len(updated_game_state.players),
                character_count=len(updated_game_state.characters),
                created_at=updated_game_state.created_at,
                updated_at=updated_game_state.updated_at,
                started_at=updated_game_state.started_at,
                completed_at=updated_game_state.completed_at
            )
        else:
            game_state_response = None
        
        response = schemas.GameActionResponse(
            success=True,
            message=f"动作 {request.action_type} 处理成功",
            data=result,
            game_state=game_state_response
        )
        
        logger.info(f"Successfully processed action {request.action_type} for session {session_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error processing action for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process action: {e}")


@router.get("/session/{session_id}/status", response_model=schemas.GameStatusResponse)
def get_game_status(
    session_id: str = Path(..., description="游戏会话ID"),
    include_history: bool = Query(True, description="是否包含历史记录"),
    max_log_entries: int = Query(20, description="最大日志条目数", ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    获取游戏状态总览
    
    Args:
        session_id: 游戏会话ID
        include_history: 是否包含历史记录
        max_log_entries: 最大日志条目数
        db: 数据库会话（依赖注入）
    
    Returns:
        GameStatusResponse: 游戏状态总览响应
    """
    try:
        logger.info(f"Getting status for game session {session_id}")
        
        game_engine = GameEngine(db)
        
        # 加载游戏状态
        game_state = game_engine.load_game(session_id)
        if not game_state:
            raise HTTPException(status_code=404, detail="Game session not found")
        
        # 构建基本游戏状态响应
        game_state_response = schemas.GameStateResponse(
            game_id=game_state.game_id,
            script_id=game_state.script_id,
            session_id=game_state.session_id,
            current_act=game_state.current_act,
            current_phase=game_state.current_phase.value,
            max_acts=game_state.max_acts,
            player_count=len(game_state.players),
            character_count=len(game_state.characters),
            created_at=game_state.created_at,
            updated_at=game_state.updated_at,
            started_at=game_state.started_at,
            completed_at=game_state.completed_at
        )
        
        # 计算游戏进度
        progress_data = GamePhaseNodes.calculate_game_progress(game_state)
        progress_response = schemas.GameProgressResponse(**progress_data)
        
        # 获取可用动作
        available_actions_data = GamePhaseNodes.get_available_actions(game_state)
        available_actions = [
            schemas.AvailableActionResponse(**action) for action in available_actions_data
        ]
        
        # 构建历史记录（如果需要）
        recent_log_entries = []
        qna_history = []
        mission_submissions = []
        
        if include_history:
            # 最近的日志条目
            recent_logs = game_state.public_log[-max_log_entries:] if game_state.public_log else []
            recent_log_entries = [
                schemas.PublicLogEntryResponse(
                    id=entry.id,
                    entry_type=entry.entry_type,
                    content=entry.content,
                    act_number=entry.act_number,
                    timestamp=entry.timestamp,
                    related_player_id=entry.related_player_id,
                    related_character_id=entry.related_character_id
                ) for entry in recent_logs
            ]
            
            # Q&A历史
            qna_history = [
                schemas.QnAEntryResponse(
                    id=entry.id,
                    questioner_id=entry.questioner_id,
                    target_character_id=entry.target_character_id,
                    question=entry.question,
                    answer=entry.answer,
                    act_number=entry.act_number,
                    timestamp=entry.timestamp,
                    is_public=entry.is_public
                ) for entry in game_state.qna_history
            ]
            
            # 任务提交
            mission_submissions = [
                schemas.MissionSubmissionResponse(
                    id=submission.id,
                    player_id=submission.player_id,
                    mission_type=submission.mission_type,
                    content=submission.content,
                    status=submission.status.value,
                    act_number=submission.act_number,
                    timestamp=submission.timestamp,
                    review_notes=submission.review_notes
                ) for submission in game_state.mission_submissions
            ]
        
        response = schemas.GameStatusResponse(
            game_state=game_state_response,
            progress=progress_response,
            available_actions=available_actions,
            recent_log_entries=recent_log_entries,
            qna_history=qna_history,
            mission_submissions=mission_submissions
        )
        
        logger.info(f"Successfully retrieved status for game session {session_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game status for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get game status")


@router.get("/session/{session_id}/summary")
def get_game_summary(
    session_id: str = Path(..., description="游戏会话ID"),
    db: Session = Depends(get_db)
):
    """
    获取游戏摘要信息
    
    Args:
        session_id: 游戏会话ID
        db: 数据库会话（依赖注入）
    
    Returns:
        Dict: 游戏摘要信息
    """
    try:
        game_engine = GameEngine(db)
        
        # 获取游戏状态摘要
        summary = game_engine.get_game_status(session_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Game session not found")
        
        # 加载完整游戏状态以获取格式化摘要
        game_state = game_engine.load_game(session_id)
        if game_state:
            formatted_summary = GamePhaseNodes.format_game_summary(game_state)
            summary["formatted_summary"] = formatted_summary
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting game summary for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get game summary")
