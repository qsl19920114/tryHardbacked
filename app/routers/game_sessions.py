import uuid
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import database_models as models
from app.schemas import pydantic_schemas as schemas
from app.services.script_service import script_manifest_service
from app.services.dify_service import generate_story_content

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

@router.post("/sessions/{session_id}/advance", response_model=schemas.SceneAdvanceResponse)
def advance_scene(
    session_id: str,
    request: schemas.SceneAdvanceRequest,
    db: Session = Depends(get_db)
):
    """
    推进游戏场景（故事模式）
    增强功能：包含详细调试信息和场景上下文

    Args:
        session_id: 游戏会话ID
        request: 场景推进请求
        db: 数据库会话（依赖注入）

    Returns:
        SceneAdvanceResponse: 场景推进响应，包含新场景内容和调试信息

    Raises:
        HTTPException: 当会话不存在或场景配置错误时返回错误
    """
    start_time = time.time()
    processing_steps = []  # 记录处理步骤用于调试

    processing_steps.append("开始处理场景推进请求")
    print(f"🎬 场景推进请求: session_id={session_id}, action={request.action}")

    # 1. 获取游戏会话
    session = db.query(models.GameSession).filter(
        models.GameSession.session_id == session_id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Game session not found")

    processing_steps.append(f"找到游戏会话: {session.session_id}")
    print(f"📋 会话信息: script_id={session.script_id}, current_scene_index={session.current_scene_index}")

    # 2. 获取当前场景索引，如果是"next"操作则推进到下一场景
    current_scene_index = session.current_scene_index
    if request.action == "next":
        current_scene_index += 1

    processing_steps.append(f"确定目标场景索引: {current_scene_index}")
    print(f"🎯 目标场景索引: {current_scene_index}")

    # 3. 从剧本清单中获取场景配置
    scene_config = script_manifest_service.get_scene_config(session.script_id, current_scene_index)
    if not scene_config:
        raise HTTPException(status_code=404, detail=f"Scene {current_scene_index} not found")

    processing_steps.append(f"加载场景配置: {scene_config.get('title')} ({scene_config.get('scene_type')})")
    print(f"🎬 场景信息: {scene_config.get('title')} - {scene_config.get('scene_type')}")

    # 4. 检查场景类型，如果是调查模式则返回调查场景信息
    if scene_config.get("scene_type") == "investigation":
        processing_steps.append("处理调查模式场景")

        # 对于调查模式，返回场景信息但不生成故事内容
        available_characters = scene_config.get("scene_config", {}).get("available_characters", [])
        character_names = [char.get("name", char.get("character_id")) for char in available_characters]

        scene_content = schemas.SceneContent(
            scene_id=current_scene_index,
            scene_type=schemas.SceneType.INVESTIGATION,
            title=scene_config.get("title", ""),
            content=f"进入调查模式：{scene_config.get('description', '')}。你现在可以与场景中的角色进行对话来收集线索。\n\n可用角色：{', '.join(character_names)}",
            characters=[char.get("character_id") for char in available_characters],
            is_final=False
        )

        # 更新会话的当前场景索引
        session.current_scene_index = current_scene_index
        session.updated_at = datetime.now(timezone.utc)
        db.commit()
        processing_steps.append("更新会话场景索引")

        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        processing_steps.append(f"调查场景处理完成，耗时: {response_time}秒")

        # 构建调试信息
        debug_info = schemas.DebugInfo(
            scene_config=scene_config,
            workflow_id=None,
            character_info={"available_characters": available_characters},
            processing_steps=processing_steps
        )

        # 构建场景上下文信息
        scene_context_info = script_manifest_service.get_scene_context_info(session.script_id, current_scene_index)
        scene_context = schemas.SceneContext(**scene_context_info) if scene_context_info else None

        # 获取可用操作列表
        available_actions_data = script_manifest_service.get_available_actions_for_scene(
            session.script_id, current_scene_index, session.current_scene_index
        )
        available_actions = [schemas.AvailableAction(**action) for action in available_actions_data]

        response = schemas.SceneAdvanceResponse(
            session_id=session_id,
            current_scene_index=current_scene_index,
            scene_content=scene_content,
            response_time=response_time,
            created_at=datetime.now(timezone.utc),
            debug_info=debug_info,
            scene_context=scene_context,
            available_actions=available_actions
        )

        print(f"✅ 调查场景处理完成: {response_time}秒, 场景={current_scene_index}")
        return response

    # 5. 处理故事模式场景
    processing_steps.append("处理故事模式场景")

    # 6. 获取对话历史记录用于上下文
    dialogue_history = ""
    if session.dialogue_history:
        history_entries = session.dialogue_history[-10:]  # 获取最近10条记录
        dialogue_history = "\n".join([
            f"{entry.character_id}: {entry.content}"
            for entry in history_entries
        ])
    processing_steps.append(f"加载对话历史: {len(session.dialogue_history) if session.dialogue_history else 0}条记录")

    # 7. 获取工作流ID并生成故事内容
    workflow_id = script_manifest_service.get_scene_workflow_id(session.script_id, current_scene_index)
    processing_steps.append(f"获取工作流ID: {workflow_id}")
    print(f"⚙️ 工作流ID: {workflow_id}")

    story_content = generate_story_content(workflow_id, scene_config, session_id, dialogue_history)
    processing_steps.append(f"生成故事内容: {len(story_content)}字符")
    print(f"📖 故事内容: {story_content[:50]}...")

    # 8. 更新会话的当前场景索引
    session.current_scene_index = current_scene_index
    session.updated_at = datetime.now(timezone.utc)

    # 9. 将生成的故事内容保存到对话历史中
    story_entry = models.DialogueEntry(
        session_id=session_id,
        character_id="narrator",  # 叙述者
        role="ai",
        content=story_content,
        timestamp=datetime.now(timezone.utc)
    )
    db.add(story_entry)
    db.commit()
    db.refresh(session)
    processing_steps.append("保存故事内容到数据库")

    # 10. 检查是否为最终场景
    is_final = script_manifest_service.is_final_scene(session.script_id, current_scene_index)
    processing_steps.append(f"检查最终场景: {is_final}")

    # 11. 构建场景内容响应
    scene_content = schemas.SceneContent(
        scene_id=current_scene_index,
        scene_type=schemas.SceneType(scene_config.get("scene_type")),
        title=scene_config.get("title", ""),
        content=story_content,
        characters=scene_config.get("scene_config", {}).get("characters_present", []),
        is_final=is_final
    )

    end_time = time.time()
    response_time = round(end_time - start_time, 2)
    processing_steps.append(f"故事场景处理完成，耗时: {response_time}秒")

    # 12. 构建调试信息
    debug_info = schemas.DebugInfo(
        scene_config=scene_config,
        workflow_id=workflow_id,
        character_info={"characters_present": scene_config.get("scene_config", {}).get("characters_present", [])},
        processing_steps=processing_steps
    )

    # 13. 构建场景上下文信息
    scene_context_info = script_manifest_service.get_scene_context_info(session.script_id, current_scene_index)
    scene_context = schemas.SceneContext(**scene_context_info) if scene_context_info else None

    # 14. 获取可用操作列表
    available_actions_data = script_manifest_service.get_available_actions_for_scene(
        session.script_id, current_scene_index, session.current_scene_index
    )
    available_actions = [schemas.AvailableAction(**action) for action in available_actions_data]

    # 15. 构建完整响应
    response = schemas.SceneAdvanceResponse(
        session_id=session_id,
        current_scene_index=current_scene_index,
        scene_content=scene_content,
        response_time=response_time,
        created_at=datetime.now(timezone.utc),
        debug_info=debug_info,
        scene_context=scene_context,
        available_actions=available_actions
    )

    print(f"✅ 故事场景处理完成: {response_time}秒, 场景={current_scene_index}")
    return response