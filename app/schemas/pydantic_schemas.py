from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import math

class SceneType(str, Enum):
    """场景类型枚举"""
    STORY = "story"  # 故事模式 - 视觉小说式推进
    INVESTIGATION = "investigation"  # 调查模式 - 自由问答

class CharacterInfo(BaseModel):
    """角色信息模型"""
    name: str  # 角色名称
    avatar: str  # 角色头像图片路径
    description: str  # 角色描述

class ScriptBase(BaseModel):
    """剧本基础信息模型"""
    id: str  # 剧本唯一标识符
    title: str  # 剧本标题
    cover: str  # 封面图片路径
    category: str  # 剧本分类
    tags: List[str]  # 标签列表
    players: str  # 玩家人数描述
    difficulty: int  # 难度等级（1-5）
    duration: str  # 游戏时长
    description: str  # 剧本简介
    author: str  # 作者
    characters: List[CharacterInfo]  # 角色信息列表

class Script(ScriptBase):
    """完整的剧本信息模型（包含时间戳）"""
    created_at: datetime  # 创建时间
    updated_at: Optional[datetime] = None  # 更新时间（可选）
    
    model_config = ConfigDict(from_attributes=True)  # 允许从数据库对象创建

class ScriptListResponse(BaseModel):
    """剧本列表响应模型"""
    scripts: List[Script]  # 剧本列表

class GameSessionCreate(BaseModel):
    """创建游戏会话的请求模型"""
    script_id: str  # 要开始的剧本ID
    user_id: Optional[str] = None  # 用户ID（可选）

class GameSession(BaseModel):
    """游戏会话信息模型"""
    session_id: str  # 会话唯一标识符
    script_id: str  # 关联的剧本ID
    user_id: Optional[str] = None  # 用户ID（可选）
    current_scene_index: int  # 当前场景索引
    dialogue_history: List[Dict]  # 对话历史记录
    game_state: Dict  # 游戏状态数据
    created_at: datetime  # 创建时间
    updated_at: Optional[datetime] = None  # 更新时间（可选）

    model_config = ConfigDict(from_attributes=True)  # 允许从数据库对象创建

class DialogueRequest(BaseModel):
    """AI对话请求模型"""
    session_id: str  # 游戏会话ID
    question: str  # 用户提出的问题
    character_id: Optional[str] = None  # 目标角色ID（调查模式使用）
    scene_id: Optional[int] = None  # 场景ID（可选，用于指定特定场景）

class DebugInfo(BaseModel):
    """调试信息模型"""
    scene_config: Optional[Dict[str, Any]] = None  # 场景配置信息
    workflow_id: Optional[str] = None  # 使用的工作流ID
    character_info: Optional[Dict[str, Any]] = None  # 角色信息
    processing_steps: List[str] = []  # 处理步骤记录

class SceneContext(BaseModel):
    """场景上下文信息模型"""
    scene_id: int  # 场景ID
    scene_type: SceneType  # 场景类型
    title: str  # 场景标题
    description: Optional[str] = None  # 场景描述
    available_characters: List[Dict[str, Any]] = []  # 可用角色列表
    scene_metadata: Optional[Dict[str, Any]] = None  # 场景元数据

class AvailableAction(BaseModel):
    """可用操作模型"""
    action_type: str  # 操作类型：dialogue, advance, investigate
    action_name: str  # 操作名称
    description: str  # 操作描述
    parameters: Optional[Dict[str, Any]] = None  # 操作参数

class DialogueResponse(BaseModel):
    """AI对话响应模型"""
    response_id: str  # 响应唯一标识符
    session_id: str  # 游戏会话ID
    question: str  # 用户的问题
    answer: str  # AI的回答
    response_time: float  # 响应时间（秒）
    created_at: datetime  # 创建时间
    # 新增调试和上下文信息
    debug_info: Optional[DebugInfo] = None  # 调试信息
    scene_context: Optional[SceneContext] = None  # 场景上下文
    available_actions: List[AvailableAction] = []  # 可用操作列表
class ScriptListResponse(BaseModel):
    """剧本列表响应模型"""
    scripts: List[Script]  # 剧本列表
    total: int
    page: int
    page_size: int
    total_pages:int

# 场景相关模型
class ScriptSceneBase(BaseModel):
    """剧本场景基础信息模型"""
    script_id: str  # 关联的剧本ID
    scene_index: int  # 场景在剧本中的顺序索引
    scene_type: SceneType  # 场景类型
    title: str  # 场景标题
    description: Optional[str] = None  # 场景描述
    dify_workflow_id: Optional[str] = None  # 对应的Dify工作流ID
    scene_config: Optional[Dict[str, Any]] = None  # 场景配置数据

class ScriptScene(ScriptSceneBase):
    """完整的剧本场景信息模型（包含ID和时间戳）"""
    id: int  # 场景唯一标识符
    created_at: datetime  # 创建时间
    updated_at: Optional[datetime] = None  # 更新时间（可选）

    model_config = ConfigDict(from_attributes=True)

# 场景推进相关模型
class SceneAdvanceRequest(BaseModel):
    """场景推进请求模型"""
    session_id: str  # 游戏会话ID
    action: Optional[str] = "next"  # 操作类型，默认为"next"

class SceneContent(BaseModel):
    """场景内容模型"""
    scene_id: int  # 场景ID
    scene_type: SceneType  # 场景类型
    title: str  # 场景标题
    content: str  # AI生成的场景内容
    characters: Optional[List[str]] = None  # 当前场景涉及的角色列表
    choices: Optional[List[str]] = None  # 可选择项（如果有）
    is_final: bool = False  # 是否为最终场景

class SceneAdvanceResponse(BaseModel):
    """场景推进响应模型"""
    session_id: str  # 游戏会话ID
    current_scene_index: int  # 当前场景索引
    scene_content: SceneContent  # 场景内容
    response_time: float  # 响应时间（秒）
    created_at: datetime  # 创建时间
    # 新增调试和上下文信息
    debug_info: Optional[DebugInfo] = None  # 调试信息
    scene_context: Optional[SceneContext] = None  # 场景上下文
    available_actions: List[AvailableAction] = []  # 可用操作列表
