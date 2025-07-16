"""
State manager for handling game state persistence and retrieval.

This module provides the StateManager class that handles serialization/deserialization
of complex game state to/from the database, bridging the gap between the structured
Pydantic models and the existing database schema.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.database_models import GameSession
from app.database import get_db
from .models import GameState, PlayerState, CharacterState, GamePhase

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages game state persistence and retrieval.
    
    This class handles the conversion between the structured GameState model
    and the JSON storage format used in the database.
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize the state manager.
        
        Args:
            db_session: Optional database session. If not provided, will use dependency injection.
        """
        self.db_session = db_session
    
    def _get_db_session(self) -> Session:
        """Get database session, using dependency injection if not provided."""
        if self.db_session:
            return self.db_session
        return next(get_db())
    
    def save_game_state(self, game_state: GameState) -> bool:
        """
        Save game state to database.
        
        Args:
            game_state: The GameState object to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = self._get_db_session()
            
            # Find existing session or create new one
            session = db.query(GameSession).filter(
                GameSession.session_id == game_state.session_id
            ).first()
            
            if not session:
                # Create new session
                session = GameSession(
                    session_id=game_state.session_id,
                    script_id=game_state.script_id,
                    user_id=None,  # Will be set by the calling code if needed
                    current_scene_index=0,  # Legacy field, keeping for compatibility
                    game_state={}
                )
                db.add(session)
            
            # Convert GameState to JSON-serializable format
            state_dict = self._serialize_game_state(game_state)
            
            # Update session with new state
            session.game_state = state_dict
            session.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            logger.info(f"Successfully saved game state for session {game_state.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save game state for session {game_state.session_id}: {e}")
            if 'db' in locals():
                db.rollback()
            return False
    
    def load_game_state(self, session_id: str) -> Optional[GameState]:
        """
        Load game state from database.
        
        Args:
            session_id: The session ID to load
            
        Returns:
            GameState object if found, None otherwise
        """
        try:
            db = self._get_db_session()
            
            session = db.query(GameSession).filter(
                GameSession.session_id == session_id
            ).first()
            
            if not session:
                logger.warning(f"No session found with ID {session_id}")
                return None
            
            # If game_state is empty or not in new format, create default state
            if not session.game_state or 'game_id' not in session.game_state:
                logger.info(f"Creating new game state for session {session_id}")
                return self._create_default_game_state(session)
            
            # Deserialize game state
            game_state = self._deserialize_game_state(session.game_state, session)
            logger.info(f"Successfully loaded game state for session {session_id}")
            return game_state
            
        except Exception as e:
            logger.error(f"Failed to load game state for session {session_id}: {e}")
            return None
    
    def delete_game_state(self, session_id: str) -> bool:
        """
        Delete game state from database.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            db = self._get_db_session()
            
            session = db.query(GameSession).filter(
                GameSession.session_id == session_id
            ).first()
            
            if session:
                db.delete(session)
                db.commit()
                logger.info(f"Successfully deleted game state for session {session_id}")
                return True
            else:
                logger.warning(f"No session found with ID {session_id} to delete")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete game state for session {session_id}: {e}")
            if 'db' in locals():
                db.rollback()
            return False
    
    def _serialize_game_state(self, game_state: GameState) -> Dict[str, Any]:
        """
        Convert GameState object to JSON-serializable dictionary.
        
        Args:
            game_state: The GameState object to serialize
            
        Returns:
            Dictionary representation of the game state
        """
        # Use Pydantic's built-in serialization
        state_dict = game_state.dict()
        
        # Convert datetime objects to ISO format strings
        for key, value in state_dict.items():
            if isinstance(value, datetime):
                state_dict[key] = value.isoformat()
        
        # Handle nested datetime objects in lists and dicts
        state_dict = self._convert_datetimes_recursive(state_dict)
        
        return state_dict
    
    def _deserialize_game_state(self, state_dict: Dict[str, Any], session: GameSession) -> GameState:
        """
        Convert dictionary to GameState object.
        
        Args:
            state_dict: Dictionary representation of game state
            session: Database session object for additional context
            
        Returns:
            GameState object
        """
        # Convert ISO format strings back to datetime objects
        state_dict = self._convert_iso_strings_recursive(state_dict)
        
        # Ensure required fields are present
        if 'session_id' not in state_dict:
            state_dict['session_id'] = session.session_id
        if 'script_id' not in state_dict:
            state_dict['script_id'] = session.script_id
        
        # Create GameState object from dictionary
        return GameState(**state_dict)
    
    def _create_default_game_state(self, session: GameSession) -> GameState:
        """
        Create a default game state for a new session.
        
        Args:
            session: Database session object
            
        Returns:
            Default GameState object
        """
        return GameState(
            game_id=f"game_{session.session_id}",
            script_id=session.script_id,
            session_id=session.session_id,
            current_phase=GamePhase.INITIALIZATION
        )
    
    def _convert_datetimes_recursive(self, obj: Any) -> Any:
        """
        Recursively convert datetime objects to ISO format strings.
        
        Args:
            obj: Object to process
            
        Returns:
            Object with datetime objects converted to strings
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._convert_datetimes_recursive(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_datetimes_recursive(item) for item in obj]
        else:
            return obj
    
    def _convert_iso_strings_recursive(self, obj: Any) -> Any:
        """
        Recursively convert ISO format strings back to datetime objects.
        
        Args:
            obj: Object to process
            
        Returns:
            Object with ISO strings converted to datetime objects
        """
        if isinstance(obj, str):
            # Try to parse as ISO datetime
            try:
                if 'T' in obj and (obj.endswith('Z') or '+' in obj[-6:] or obj.endswith('+00:00')):
                    return datetime.fromisoformat(obj.replace('Z', '+00:00'))
            except ValueError:
                pass
            return obj
        elif isinstance(obj, dict):
            return {key: self._convert_iso_strings_recursive(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_iso_strings_recursive(item) for item in obj]
        else:
            return obj
    
    def update_game_state_field(self, session_id: str, field_updates: Dict[str, Any]) -> bool:
        """
        Update specific fields in the game state without loading the entire state.
        
        Args:
            session_id: The session ID to update
            field_updates: Dictionary of field names and their new values
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Load current state
            game_state = self.load_game_state(session_id)
            if not game_state:
                return False
            
            # Update specified fields
            for field, value in field_updates.items():
                if hasattr(game_state, field):
                    setattr(game_state, field, value)
                else:
                    logger.warning(f"Field {field} not found in GameState model")
            
            # Save updated state
            return self.save_game_state(game_state)
            
        except Exception as e:
            logger.error(f"Failed to update game state fields for session {session_id}: {e}")
            return False
    
    def get_game_state_summary(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of the game state without loading the full object.
        
        Args:
            session_id: The session ID to summarize
            
        Returns:
            Dictionary with summary information, None if not found
        """
        try:
            db = self._get_db_session()
            
            session = db.query(GameSession).filter(
                GameSession.session_id == session_id
            ).first()
            
            if not session or not session.game_state:
                return None
            
            state_dict = session.game_state
            
            return {
                'game_id': state_dict.get('game_id'),
                'script_id': state_dict.get('script_id'),
                'current_act': state_dict.get('current_act', 1),
                'current_phase': state_dict.get('current_phase', 'initialization'),
                'player_count': len(state_dict.get('players', {})),
                'character_count': len(state_dict.get('characters', {})),
                'created_at': state_dict.get('created_at'),
                'updated_at': state_dict.get('updated_at')
            }
            
        except Exception as e:
            logger.error(f"Failed to get game state summary for session {session_id}: {e}")
            return None
