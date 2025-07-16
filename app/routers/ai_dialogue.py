import time
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db, SessionLocal
from app.schemas import pydantic_schemas as schemas
from app.services.dify_service import call_dify_chatflow, call_dify_workflow, generate_character_response
from app.services.script_service import script_manifest_service
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


def broadcast_to_other_characters(
    session_id: str,
    current_character_id: str,
    question: str,
    answer: str,
    db_session_factory
):
    """
    异步广播任务：将对话内容更新到其他AI角色的记忆中

    Args:
        session_id: 游戏会话ID
        current_character_id: 当前对话的角色ID
        question: 玩家的问题
        answer: AI的回答
        db_session_factory: 数据库会话工厂
    """
    from app.database import SessionLocal

    # 创建新的数据库会话用于后台任务
    db = SessionLocal()
    try:
        # 1. 获取游戏会话
        session = db.query(models.GameSession).filter(
            models.GameSession.session_id == session_id
        ).first()
        if not session:
            return

        # 2. 获取当前场景的可用角色列表
        available_characters = script_manifest_service.get_available_characters(
            session.script_id,
            session.current_scene_index
        )

        # 3. 为每个其他角色更新记忆
        for character in available_characters:
            character_id = character.get("character_id")
            if character_id == current_character_id:
                continue  # 跳过当前对话的角色

            # 4. 获取角色对应的工作流ID
            workflow_id = character.get("dify_workflow_id")
            if not workflow_id:
                continue

            # 5. 构建记忆更新的输入
            memory_update_inputs = {
                "event_type": "dialogue_witnessed",
                "player_question": question,
                "character_response": answer,
                "responding_character": current_character_id,
                "context": "其他角色的对话被观察到"
            }

            # 6. 调用Dify工作流更新角色记忆（使用唯一的conversation_id）
            conversation_id = f"{session_id}_{character_id}"
            try:
                call_dify_workflow(
                    workflow_id=workflow_id,
                    inputs=memory_update_inputs,
                    user_id=session_id,
                    conversation_id=conversation_id
                )
                print(f"成功更新角色 {character_id} 的记忆")
            except Exception as e:
                print(f"更新角色 {character_id} 记忆失败: {e}")

    except Exception as e:
        print(f"广播任务执行失败: {e}")
    finally:
        db.close()

@router.post("/dialogue", response_model=schemas.DialogueResponse)
def post_dialogue(
    request: schemas.DialogueRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    AI对话端点 - 支持同步响应和异步记忆广播
    增强功能：支持scene_id参数，自动识别场景类型和角色路由

    Args:
        request: 对话请求，包含会话ID、问题、角色ID和可选的场景ID
        background_tasks: FastAPI后台任务
        db: 数据库会话

    Returns:
        DialogueResponse: 对话响应（包含调试信息和场景上下文）
    """
    start_time = time.time()
    processing_steps = []  # 记录处理步骤用于调试

    processing_steps.append("开始处理对话请求")
    print(f"🎯 对话请求: session_id={request.session_id}, character_id={request.character_id}, scene_id={request.scene_id}")

    # 1. 获取游戏会话
    session = db.query(models.GameSession).filter(
        models.GameSession.session_id == request.session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")

    processing_steps.append(f"找到游戏会话: {session.session_id}")
    print(f"📋 会话信息: script_id={session.script_id}, current_scene_index={session.current_scene_index}")

    # 2. 确定使用的场景ID（优先使用请求中的scene_id，否则使用会话当前场景）
    target_scene_id = request.scene_id if request.scene_id is not None else session.current_scene_index
    processing_steps.append(f"确定目标场景ID: {target_scene_id}")

    # 3. 获取场景配置
    scene_config = script_manifest_service.get_scene_config(session.script_id, target_scene_id)
    if not scene_config:
        raise HTTPException(status_code=404, detail=f"Scene {target_scene_id} not found")

    processing_steps.append(f"加载场景配置: {scene_config.get('title')} ({scene_config.get('scene_type')})")
    print(f"🎬 场景信息: {scene_config.get('title')} - {scene_config.get('scene_type')}")

    # 4. 根据场景类型进行智能路由
    scene_type = scene_config.get("scene_type")
    if scene_type != "investigation":
        raise HTTPException(
            status_code=400,
            detail=f"Scene {target_scene_id} is not an investigation scene. Current scene type: {scene_type}"
        )

    # 5. 验证角色ID是否提供和有效
    if not request.character_id:
        # 如果没有提供角色ID，返回可用角色列表
        available_characters = script_manifest_service.get_available_characters(session.script_id, target_scene_id)
        character_names = [char.get('name', char.get('character_id')) for char in available_characters]
        raise HTTPException(
            status_code=400,
            detail=f"character_id is required for investigation scene. Available characters: {character_names}"
        )

    # 6. 验证角色是否在当前场景中可用
    available_characters = script_manifest_service.get_available_characters(session.script_id, target_scene_id)
    character_ids = [char.get('character_id') for char in available_characters]

    if request.character_id not in character_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Character {request.character_id} is not available in scene {target_scene_id}. Available: {character_ids}"
        )

    # 找到目标角色信息
    target_character = next((char for char in available_characters if char.get('character_id') == request.character_id), None)
    processing_steps.append(f"验证角色有效性: {target_character.get('name') if target_character else request.character_id}")
    print(f"👤 目标角色: {target_character.get('name') if target_character else request.character_id}")

    # 7. 获取角色对应的工作流ID
    character_workflow_id = script_manifest_service.get_character_workflow_id(
        session.script_id,
        target_scene_id,
        request.character_id
    )
    processing_steps.append(f"获取工作流ID: {character_workflow_id}")
    print(f"⚙️ 工作流ID: {character_workflow_id}")

    # 8. 获取历史对话记录用于上下文
    dialogue_history = ""
    if session.dialogue_history:
        history_entries = session.dialogue_history[-20:]  # 获取最近20条记录
        dialogue_history = "\n".join([
            f"{entry.character_id}: {entry.content}"
            for entry in history_entries
        ])
    processing_steps.append(f"加载对话历史: {len(session.dialogue_history) if session.dialogue_history else 0}条记录")

    # 9. 调用角色专用的Dify工作流获取回答
    if character_workflow_id and not character_workflow_id.endswith("_character_workflow"):
        # 构建角色对话的输入
        character_inputs = {
            "player_question": request.question,
            "dialogue_history": dialogue_history,
            "scene_context": scene_config.get("description", ""),
            "character_name": request.character_id
        }

        # 使用唯一的conversation_id格式
        conversation_id = f"{request.session_id}_{request.character_id}"
        processing_steps.append(f"调用Dify工作流: {character_workflow_id}")
        ai_answer = call_dify_workflow(
            workflow_id=character_workflow_id,
            inputs=character_inputs,
            user_id=request.session_id,
            conversation_id=conversation_id
        )
    else:
        # 使用模拟角色回答（用于测试）
        processing_steps.append("使用模拟角色回答")
        ai_answer = generate_character_response(
            character_id=request.character_id,
            question=request.question,
            scene_context=scene_config.get("description", "")
        )

    processing_steps.append(f"生成AI回答: {len(ai_answer)}字符")
    print(f"💬 AI回答: {ai_answer[:50]}...")

    # 10. 创建新的对话记录
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

    # 11. 保存对话记录到数据库
    db.add(player_entry)
    db.add(ai_entry)
    db.commit()
    processing_steps.append("保存对话记录到数据库")

    # 12. 添加异步广播任务到后台
    background_tasks.add_task(
        broadcast_to_other_characters,
        session_id=request.session_id,
        current_character_id=request.character_id,
        question=request.question,
        answer=ai_answer,
        db_session_factory=SessionLocal
    )
    processing_steps.append("添加异步广播任务")

    end_time = time.time()
    response_time = round(end_time - start_time, 2)
    processing_steps.append(f"处理完成，总耗时: {response_time}秒")

    # 13. 构建调试信息
    debug_info = schemas.DebugInfo(
        scene_config=scene_config,
        workflow_id=character_workflow_id,
        character_info=target_character,
        processing_steps=processing_steps
    )

    # 14. 构建场景上下文信息
    scene_context_info = script_manifest_service.get_scene_context_info(session.script_id, target_scene_id)
    scene_context = schemas.SceneContext(**scene_context_info) if scene_context_info else None

    # 15. 获取可用操作列表
    available_actions_data = script_manifest_service.get_available_actions_for_scene(
        session.script_id, target_scene_id, session.current_scene_index
    )
    available_actions = [schemas.AvailableAction(**action) for action in available_actions_data]

    # 16. 构建完整响应
    response = schemas.DialogueResponse(
        response_id=f"resp_{uuid.uuid4()}",
        session_id=request.session_id,
        question=request.question,
        answer=ai_answer,
        response_time=response_time,
        created_at=datetime.now(timezone.utc),
        debug_info=debug_info,
        scene_context=scene_context,
        available_actions=available_actions
    )

    print(f"✅ 对话处理完成: {response_time}秒, 场景={target_scene_id}, 角色={request.character_id}")
    return response