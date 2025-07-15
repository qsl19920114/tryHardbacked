from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base

class Script(Base):
    """
    剧本数据模型
    存储视觉小说游戏的剧本信息，包括标题、封面、角色等
    """
    __tablename__ = "scripts"

    id = Column(String, primary_key=True, index=True)  # 剧本唯一标识符
    title = Column(String, index=True)  # 剧本标题
    cover = Column(String)  # 封面图片路径
    category = Column(String)  # 剧本分类（如：悬疑、恋爱等）
    tags = Column(JSON)  # 剧本标签列表，存储为JSON格式
    players = Column(String)  # 玩家人数描述（如："6人 (3男3女)"）
    difficulty = Column(Integer)  # 难度等级（1-5）
    duration = Column(String)  # 游戏时长描述（如："约4小时"）
    description = Column(String)  # 剧本简介
    author = Column(String)  # 剧本作者
    characters = Column(JSON)  # 角色信息列表，存储为JSON格式
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 更新时间

class GameSession(Base):
    """
    游戏会话数据模型
    记录用户的游戏进度、对话历史和游戏状态
    """
    __tablename__ = "game_sessions"

    session_id = Column(String, primary_key=True, index=True)  # 会话唯一标识符
    script_id = Column(String, index=True)  # 关联的剧本ID
    user_id = Column(String, nullable=True)  # 用户ID（可选）
    current_scene_index = Column(Integer, default=0)  # 当前场景索引
    dialogue_history = Column(JSON, default=[])  # 对话历史记录，存储为JSON格式
    game_state = Column(JSON, default={})  # 游戏状态数据，存储为JSON格式
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 更新时间