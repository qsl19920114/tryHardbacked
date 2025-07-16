"""
Pydantic models for comprehensive game state management.

This module defines the data structures for managing the murder mystery game state,
replacing the simple JSON field approach with structured, validated models.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, validator
import uuid


class GamePhase(str, Enum):
    """Enumeration of possible game phases."""
    INITIALIZATION = "initialization"
    MONOLOGUE = "monologue"
    QNA = "qna"
    MISSION_SUBMIT = "mission_submit"
    FINAL_CHOICE = "final_choice"
    COMPLETED = "completed"
    PAUSED = "paused"


class PlayerRole(str, Enum):
    """Player roles in the game."""
    PLAYER = "player"
    GAME_MASTER = "game_master"
    OBSERVER = "observer"


class MissionStatus(str, Enum):
    """Status of mission submissions."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class CharacterState(BaseModel):
    """State information for a specific character."""
    character_id: str = Field(..., description="Unique character identifier")
    name: str = Field(..., description="Character name")
    avatar: str = Field(..., description="Character avatar image path")
    description: str = Field(..., description="Character description")
    is_alive: bool = Field(default=True, description="Whether character is alive")
    suspicion_level: int = Field(default=0, ge=0, le=100, description="Suspicion level (0-100)")
    secrets_revealed: List[str] = Field(default_factory=list, description="List of revealed secrets")
    relationships: Dict[str, str] = Field(default_factory=dict, description="Relationships with other characters")
    custom_attributes: Dict[str, Any] = Field(default_factory=dict, description="Custom character attributes")


class PlayerState(BaseModel):
    """State information for a specific player."""
    player_id: str = Field(..., description="Unique player identifier")
    character_id: Optional[str] = Field(None, description="Assigned character ID")
    role: PlayerRole = Field(default=PlayerRole.PLAYER, description="Player role in the game")
    is_active: bool = Field(default=True, description="Whether player is actively participating")
    qna_count_current_act: int = Field(default=0, ge=0, description="Q&A count for current act")
    total_qna_count: int = Field(default=0, ge=0, description="Total Q&A count across all acts")
    mission_submissions: List[str] = Field(default_factory=list, description="List of mission submission IDs")
    notes: str = Field(default="", description="Player's private notes")
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last activity timestamp")


class QnAEntry(BaseModel):
    """A single question and answer exchange."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique Q&A entry ID")
    questioner_id: str = Field(..., description="ID of the player asking the question")
    target_character_id: str = Field(..., description="ID of the character being questioned")
    question: str = Field(..., description="The question asked")
    answer: str = Field(..., description="The AI-generated answer")
    act_number: int = Field(..., ge=1, description="Act number when this Q&A occurred")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="When the Q&A occurred")
    is_public: bool = Field(default=True, description="Whether this Q&A is visible to all players")


class MissionSubmission(BaseModel):
    """A mission submission by a player."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique submission ID")
    player_id: str = Field(..., description="ID of the submitting player")
    mission_type: str = Field(..., description="Type of mission (e.g., 'accusation', 'evidence')")
    content: str = Field(..., description="Mission submission content")
    status: MissionStatus = Field(default=MissionStatus.PENDING, description="Submission status")
    act_number: int = Field(..., ge=1, description="Act number when submitted")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Submission timestamp")
    review_notes: str = Field(default="", description="Review notes from game master")


class PublicLogEntry(BaseModel):
    """An entry in the public game log."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique log entry ID")
    entry_type: str = Field(..., description="Type of log entry (e.g., 'qna', 'mission', 'phase_change')")
    content: str = Field(..., description="Log entry content")
    act_number: int = Field(..., ge=1, description="Act number when this occurred")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Log entry timestamp")
    related_player_id: Optional[str] = Field(None, description="Related player ID if applicable")
    related_character_id: Optional[str] = Field(None, description="Related character ID if applicable")


class GameState(BaseModel):
    """Comprehensive game state model for murder mystery game."""
    
    # Core game identification
    game_id: str = Field(..., description="Unique game identifier")
    script_id: str = Field(..., description="Associated script/scenario ID")
    session_id: str = Field(..., description="Associated session ID for database compatibility")
    
    # Game progression
    current_act: int = Field(default=1, ge=1, description="Current act number")
    current_phase: GamePhase = Field(default=GamePhase.INITIALIZATION, description="Current game phase")
    max_acts: int = Field(default=3, ge=1, description="Maximum number of acts in this game")
    
    # Player and character management
    players: Dict[str, PlayerState] = Field(default_factory=dict, description="Player states by player ID")
    characters: Dict[str, CharacterState] = Field(default_factory=dict, description="Character states by character ID")
    turn_order: List[str] = Field(default_factory=list, description="Player turn order")
    current_turn_index: int = Field(default=0, ge=0, description="Index of current player's turn")
    
    # Game content and history
    public_log: List[PublicLogEntry] = Field(default_factory=list, description="Public game log entries")
    qna_history: List[QnAEntry] = Field(default_factory=list, description="All Q&A exchanges")
    mission_submissions: List[MissionSubmission] = Field(default_factory=list, description="All mission submissions")
    
    # Game configuration and limits
    max_qna_per_character_per_act: int = Field(default=3, ge=1, description="Max Q&A per character per act")
    qna_counts: Dict[str, Dict[str, int]] = Field(
        default_factory=dict, 
        description="Q&A counts: {character_id: {act_number: count}}"
    )
    
    # Game metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Game creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    started_at: Optional[datetime] = Field(None, description="Game start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Game completion timestamp")
    
    # Custom game data
    custom_data: Dict[str, Any] = Field(default_factory=dict, description="Custom game-specific data")
    
    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v):
        """Always update the updated_at timestamp."""
        return datetime.now(timezone.utc)
    
    def get_current_player(self) -> Optional[PlayerState]:
        """Get the current player based on turn order."""
        if not self.turn_order or self.current_turn_index >= len(self.turn_order):
            return None
        current_player_id = self.turn_order[self.current_turn_index]
        return self.players.get(current_player_id)
    
    def advance_turn(self) -> None:
        """Advance to the next player's turn."""
        if self.turn_order:
            self.current_turn_index = (self.current_turn_index + 1) % len(self.turn_order)
    
    def get_qna_count_for_character_act(self, character_id: str, act_number: int) -> int:
        """Get Q&A count for a specific character in a specific act."""
        return self.qna_counts.get(character_id, {}).get(str(act_number), 0)
    
    def increment_qna_count(self, character_id: str, act_number: int) -> None:
        """Increment Q&A count for a character in an act."""
        if character_id not in self.qna_counts:
            self.qna_counts[character_id] = {}
        act_key = str(act_number)
        self.qna_counts[character_id][act_key] = self.qna_counts[character_id].get(act_key, 0) + 1
    
    def can_ask_question(self, character_id: str, act_number: int) -> bool:
        """Check if more questions can be asked to a character in an act."""
        current_count = self.get_qna_count_for_character_act(character_id, act_number)
        return current_count < self.max_qna_per_character_per_act
    
    def add_public_log_entry(self, entry_type: str, content: str, **kwargs) -> PublicLogEntry:
        """Add an entry to the public log."""
        entry = PublicLogEntry(
            entry_type=entry_type,
            content=content,
            act_number=self.current_act,
            **kwargs
        )
        self.public_log.append(entry)
        return entry
    
    def add_qna_entry(self, questioner_id: str, target_character_id: str, 
                      question: str, answer: str, is_public: bool = True) -> QnAEntry:
        """Add a Q&A entry and update counts."""
        entry = QnAEntry(
            questioner_id=questioner_id,
            target_character_id=target_character_id,
            question=question,
            answer=answer,
            act_number=self.current_act,
            is_public=is_public
        )
        self.qna_history.append(entry)
        self.increment_qna_count(target_character_id, self.current_act)
        
        # Update player's Q&A count
        if questioner_id in self.players:
            self.players[questioner_id].qna_count_current_act += 1
            self.players[questioner_id].total_qna_count += 1
        
        return entry
    
    def add_mission_submission(self, player_id: str, mission_type: str, content: str) -> MissionSubmission:
        """Add a mission submission."""
        submission = MissionSubmission(
            player_id=player_id,
            mission_type=mission_type,
            content=content,
            act_number=self.current_act
        )
        self.mission_submissions.append(submission)
        
        # Update player's submission list
        if player_id in self.players:
            self.players[player_id].mission_submissions.append(submission.id)
        
        return submission
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
