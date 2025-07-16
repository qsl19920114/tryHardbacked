from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime
import math

class CharacterInfo(BaseModel):
    """角色信息模型"""
    name: str  # 角色名称
    avatar: str  # 角色头像图片路径
    description: str  # 角色描述

class ScriptBase(BaseModel):
    """剧本基础信息模型（用于创建剧本，不包含cover字段，会自动生成）"""
    id: str  # 剧本唯一标识符
    title: str  # 剧本标题
    category: str  # 剧本分类
    tags: List[str]  # 标签列表
    players: str  # 玩家人数描述
    difficulty: int  # 难度等级（1-5）
    duration: str  # 游戏时长
    description: str  # 剧本简介
    author: str  # 作者
    characters: List[CharacterInfo]  # 角色信息列表

class Script(ScriptBase):
    """完整的剧本信息模型（包含时间戳和自动生成的cover字段）"""
    cover: str  # 封面图片路径（自动生成）
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

class DialogueResponse(BaseModel):
    """AI对话响应模型"""
    response_id: str  # 响应唯一标识符
    session_id: str  # 游戏会话ID
    question: str  # 用户的问题
    answer: str  # AI的回答
    response_time: float  # 响应时间（秒）
    created_at: datetime  # 创建时间
class ScriptListResponse(BaseModel):
    """剧本列表响应模型"""
    scripts: List[Script]  # 剧本列表
    total: int
    page: int
    page_size: int
    total_pages:int

# LangChain Game Engine Schemas

class GameStartRequest(BaseModel):
    """启动新游戏的请求模型"""
    script_id: str = Field(..., description="剧本ID")
    user_id: Optional[str] = Field(None, description="用户ID")

class GameActionRequest(BaseModel):
    """游戏动作请求模型"""
    action_type: str = Field(..., description="动作类型: monologue, qna, mission_submit, advance_phase")
    player_id: Optional[str] = Field(None, description="执行动作的玩家ID")
    character_id: Optional[str] = Field(None, description="目标角色ID")
    question: Optional[str] = Field(None, description="问题内容 (用于qna动作)")
    content: Optional[str] = Field(None, description="内容 (用于mission_submit动作)")
    mission_type: Optional[str] = Field("general", description="任务类型")
    target_phase: Optional[str] = Field(None, description="目标阶段 (用于advance_phase动作)")
    model_name: Optional[str] = Field("gpt-3.5-turbo", description="AI模型名称")
    user_id: Optional[str] = Field("system", description="用户ID")
    is_public: Optional[bool] = Field(True, description="是否公开 (用于qna动作)")

class PlayerJoinRequest(BaseModel):
    """玩家加入游戏请求模型"""
    player_id: str = Field(..., description="玩家ID")
    character_id: Optional[str] = Field(None, description="分配的角色ID")

class GameStateResponse(BaseModel):
    """游戏状态响应模型"""
    game_id: str
    script_id: str
    session_id: str
    current_act: int
    current_phase: str
    max_acts: int
    player_count: int
    character_count: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class GameActionResponse(BaseModel):
    """游戏动作响应模型"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    game_state: Optional[GameStateResponse] = None

class QnAEntryResponse(BaseModel):
    """问答条目响应模型"""
    id: str
    questioner_id: str
    target_character_id: str
    question: str
    answer: str
    act_number: int
    timestamp: datetime
    is_public: bool

class MissionSubmissionResponse(BaseModel):
    """任务提交响应模型"""
    id: str
    player_id: str
    mission_type: str
    content: str
    status: str
    act_number: int
    timestamp: datetime
    review_notes: str

class PublicLogEntryResponse(BaseModel):
    """公开日志条目响应模型"""
    id: str
    entry_type: str
    content: str
    act_number: int
    timestamp: datetime
    related_player_id: Optional[str] = None
    related_character_id: Optional[str] = None

class GameProgressResponse(BaseModel):
    """游戏进度响应模型"""
    overall_progress: float
    act_progress: float
    qna_progress: float
    current_act: int
    total_acts: int
    current_phase: str
    total_qna_current_act: int
    max_qna_current_act: int

class AvailableActionResponse(BaseModel):
    """可用动作响应模型"""
    action_type: str
    description: str
    character_id: Optional[str] = None
    target_phase: Optional[str] = None
    remaining_questions: Optional[int] = None

class GameStatusResponse(BaseModel):
    """游戏状态总览响应模型"""
    game_state: GameStateResponse
    progress: GameProgressResponse
    available_actions: List[AvailableActionResponse]
    recent_log_entries: List[PublicLogEntryResponse]
    qna_history: List[QnAEntryResponse]
    mission_submissions: List[MissionSubmissionResponse]
