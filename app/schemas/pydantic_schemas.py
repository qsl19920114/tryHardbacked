from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime

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

class DialogueResponse(BaseModel):
    """AI对话响应模型"""
    response_id: str  # 响应唯一标识符
    session_id: str  # 游戏会话ID
    question: str  # 用户的问题
    answer: str  # AI的回答
    response_time: float  # 响应时间（秒）
    created_at: datetime  # 创建时间
