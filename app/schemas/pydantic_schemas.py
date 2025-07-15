from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime

class CharacterInfo(BaseModel):
    name: str
    avatar: str
    description: str

class ScriptBase(BaseModel):
    id: str
    title: str
    cover: str
    category: str
    tags: List[str]
    players: str
    difficulty: int
    duration: str
    description: str
    author: str
    characters: List[CharacterInfo]

class Script(ScriptBase):
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class ScriptListResponse(BaseModel):
    scripts: List[Script]

class GameSessionCreate(BaseModel):
    script_id: str
    user_id: Optional[str] = None

class GameSession(BaseModel):
    session_id: str
    script_id: str
    user_id: Optional[str] = None
    current_scene_index: int
    dialogue_history: List[Dict]
    game_state: Dict
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class DialogueRequest(BaseModel):
    session_id: str
    question: str

class DialogueResponse(BaseModel):
    response_id: str
    session_id: str
    question: str
    answer: str
    response_time: float
    created_at: datetime