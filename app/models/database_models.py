from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class SceneType(enum.Enum):
    """场景类型枚举"""
    STORY = "story"  # 故事模式 - 视觉小说式推进
    INVESTIGATION = "investigation"  # 调查模式 - 自由问答

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

    # 建立与 ScriptScene 的一对多关系
    scenes = relationship(
        "ScriptScene",
        back_populates="script",
        order_by="ScriptScene.scene_index",
        cascade="all, delete-orphan"  # 当删除剧本时，自动删除所有关联的场景
    )

class GameSession(Base):
    __tablename__ = "game_sessions"

    session_id = Column(String, primary_key=True, index=True)
    script_id = Column(String, index=True)
    user_id = Column(String, nullable=True, index=True)
    current_scene_index = Column(Integer, default=0)
    game_state = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 建立与 DialogueEntry 的一对多关系
    # 当我们访问一个 GameSession 对象的 .dialogue_history 属性时,
    # SQLAlchemy 会自动查询所有关联的 DialogueEntry 记录，并按时间排序。
    dialogue_history = relationship(
        "DialogueEntry",
        back_populates="session",
        order_by="DialogueEntry.timestamp",
        cascade="all, delete-orphan" # 当删除一个session时，自动删除所有关联的对话
    )
#新增的DialogueEntry 模型
class DialogueEntry(Base):
    __tablename__ = "dialogue_entries"

    id = Column(Integer, primary_key=True, index=True)
    
    # 定义外键，指向 game_sessions 表的 session_id 字段
    session_id = Column(String, ForeignKey("game_sessions.session_id"), nullable=False, index=True)
    
    character_id = Column(String, nullable=False)
    role = Column(String, nullable=False) # "player" 或 "ai"
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    diaglogue_metadata = Column(JSON, nullable=True)
    
    # 建立与 GameSession 的多对一关系
    session = relationship("GameSession", back_populates="dialogue_history")

class ScriptScene(Base):
    """
    剧本场景数据模型
    存储剧本中的各个场景信息，支持故事模式和调查模式
    """
    __tablename__ = "script_scenes"

    id = Column(Integer, primary_key=True, index=True)  # 场景唯一标识符
    script_id = Column(String, ForeignKey("scripts.id"), nullable=False, index=True)  # 关联的剧本ID
    scene_index = Column(Integer, nullable=False)  # 场景在剧本中的顺序索引
    scene_type = Column(Enum(SceneType), nullable=False)  # 场景类型：story 或 investigation
    title = Column(String, nullable=False)  # 场景标题
    description = Column(Text, nullable=True)  # 场景描述
    dify_workflow_id = Column(String, nullable=True)  # 对应的Dify工作流ID
    scene_config = Column(JSON, nullable=True)  # 场景配置数据（JSON格式）
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # 创建时间
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())  # 更新时间

    # 建立与 Script 的多对一关系
    script = relationship("Script", back_populates="scenes")