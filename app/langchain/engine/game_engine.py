"""
Main game engine class for murder mystery game orchestration.

This module provides the GameEngine class that serves as the central coordinator
for the murder mystery game, managing state, orchestrating AI tools, and
handling the game flow through LangGraph.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.langchain.state.models import GameState, PlayerState, CharacterState, GamePhase
from app.langchain.state.manager import StateManager
from app.langchain.tools.dify_tools import DifyMonologueTool, DifyQnATool
from app.langchain.engine.graph import create_game_graph, GameGraphState
from app.models.database_models import Script
from app.database import get_db

logger = logging.getLogger(__name__)


class GameEngineError(Exception):
    """Custom exception for game engine errors."""
    pass


class GameEngine:
    """
    Main game engine for murder mystery orchestration.
    
    This class coordinates the entire game flow, managing state persistence,
    AI tool invocation, and player interactions through a LangGraph workflow.
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize the game engine.
        
        Args:
            db_session: Optional database session for state persistence
        """
        self.db_session = db_session
        self.state_manager = StateManager(db_session)
        self.graph = create_game_graph()
        self.monologue_tool = DifyMonologueTool()
        self.qna_tool = DifyQnATool()
        
        logger.info("GameEngine initialized")
    
    def start_new_game(self, script_id: str, user_id: Optional[str] = None) -> GameState:
        """
        Start a new game session.
        
        Args:
            script_id: ID of the script to use for the game
            user_id: Optional user ID for the game session
            
        Returns:
            Initial game state
            
        Raises:
            GameEngineError: If game creation fails
        """
        try:
            # Generate unique IDs
            session_id = f"session_{uuid.uuid4()}"
            game_id = f"game_{uuid.uuid4()}"
            
            logger.info(f"Starting new game: {game_id} with script: {script_id}")
            
            # Load script information
            script = self._load_script(script_id)
            if not script:
                raise GameEngineError(f"Script not found: {script_id}")
            
            # Create initial game state
            game_state = GameState(
                game_id=game_id,
                script_id=script_id,
                session_id=session_id,
                current_phase=GamePhase.INITIALIZATION,
                started_at=datetime.now(timezone.utc)
            )
            
            # Initialize characters from script
            self._initialize_characters(game_state, script)
            
            # Save initial state
            if not self.state_manager.save_game_state(game_state):
                raise GameEngineError("Failed to save initial game state")
            
            # Add initial log entry
            game_state.add_public_log_entry(
                "game_created",
                f"新游戏创建：{script.title}"
            )
            
            logger.info(f"Game {game_id} started successfully")
            return game_state
            
        except Exception as e:
            logger.error(f"Failed to start new game: {e}")
            raise GameEngineError(f"Failed to start new game: {e}")
    
    def load_game(self, session_id: str) -> Optional[GameState]:
        """
        Load an existing game session.
        
        Args:
            session_id: Session ID to load
            
        Returns:
            Game state if found, None otherwise
        """
        try:
            game_state = self.state_manager.load_game_state(session_id)
            if game_state:
                logger.info(f"Loaded game {game_state.game_id}")
            else:
                logger.warning(f"Game not found for session {session_id}")
            return game_state
            
        except Exception as e:
            logger.error(f"Failed to load game for session {session_id}: {e}")
            return None
    
    def add_player(self, session_id: str, player_id: str, character_id: Optional[str] = None) -> bool:
        """
        Add a player to the game.
        
        Args:
            session_id: Game session ID
            player_id: Unique player identifier
            character_id: Optional character to assign to the player
            
        Returns:
            True if successful, False otherwise
        """
        try:
            game_state = self.load_game(session_id)
            if not game_state:
                return False
            
            # Create player state
            player_state = PlayerState(
                player_id=player_id,
                character_id=character_id
            )
            
            # Add to game state
            game_state.players[player_id] = player_state
            game_state.turn_order.append(player_id)
            
            # Add log entry
            game_state.add_public_log_entry(
                "player_joined",
                f"玩家 {player_id} 加入游戏",
                related_player_id=player_id
            )
            
            # Save updated state
            success = self.state_manager.save_game_state(game_state)
            if success:
                logger.info(f"Player {player_id} added to game {game_state.game_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add player {player_id} to session {session_id}: {e}")
            return False
    
    def process_action(self, session_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a player action through the game engine.
        
        Args:
            session_id: Game session ID
            action: Action dictionary containing action details
            
        Returns:
            Result dictionary with response and updated state info
        """
        try:
            # Load current game state
            game_state = self.load_game(session_id)
            if not game_state:
                return {"error": "Game session not found"}
            
            logger.info(f"Processing action for game {game_state.game_id}: {action.get('action_type', 'unknown')}")
            
            # Prepare graph state
            graph_state = GameGraphState({
                "game_state": game_state,
                "messages": [],
                "current_action": action,
                "error_message": "",
                "next_phase": game_state.current_phase
            })
            
            # Process action based on type
            action_type = action.get("action_type")
            
            if action_type == "monologue":
                result = self._process_monologue_action(graph_state, action)
            elif action_type == "qna":
                result = self._process_qna_action(graph_state, action)
            elif action_type == "mission_submit":
                result = self._process_mission_action(graph_state, action)
            elif action_type == "advance_phase":
                result = self._process_phase_advance(graph_state, action)
            else:
                result = {"error": f"Unknown action type: {action_type}"}
            
            # Save updated game state
            if "error" not in result:
                self.state_manager.save_game_state(graph_state["game_state"])
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process action for session {session_id}: {e}")
            return {"error": f"Failed to process action: {e}"}
    
    def _process_monologue_action(self, graph_state: GameGraphState, action: Dict[str, Any]) -> Dict[str, Any]:
        """Process a character monologue action."""
        try:
            character_id = action.get("character_id")
            if not character_id:
                return {"error": "Character ID required for monologue"}
            
            game_state = graph_state["game_state"]
            
            # Generate monologue using Dify tool
            monologue = self.monologue_tool._run(
                char_id=character_id,
                act_num=game_state.current_act,
                model_name=action.get("model_name", "gpt-3.5-turbo"),
                user_id=action.get("user_id", "system")
            )
            
            # Add to public log
            game_state.add_public_log_entry(
                "monologue",
                f"【{character_id}】{monologue}",
                related_character_id=character_id
            )
            
            return {
                "success": True,
                "monologue": monologue,
                "character_id": character_id,
                "current_phase": game_state.current_phase.value
            }
            
        except Exception as e:
            logger.error(f"Failed to process monologue action: {e}")
            return {"error": f"Failed to generate monologue: {e}"}
    
    def _process_qna_action(self, graph_state: GameGraphState, action: Dict[str, Any]) -> Dict[str, Any]:
        """Process a Q&A action."""
        try:
            character_id = action.get("character_id")
            question = action.get("question")
            questioner_id = action.get("questioner_id")
            
            if not all([character_id, question, questioner_id]):
                return {"error": "Character ID, question, and questioner ID required for Q&A"}
            
            game_state = graph_state["game_state"]
            
            # Check if Q&A is allowed for this character in current act
            if not game_state.can_ask_question(character_id, game_state.current_act):
                return {"error": f"已达到角色 {character_id} 在第{game_state.current_act}幕的提问上限"}
            
            # Generate answer using Dify tool
            answer = self.qna_tool._run(
                char_id=character_id,
                act_num=game_state.current_act,
                query=question,
                model_name=action.get("model_name", "gpt-3.5-turbo"),
                user_id=action.get("user_id", "system")
            )
            
            # Add Q&A entry to game state
            qna_entry = game_state.add_qna_entry(
                questioner_id=questioner_id,
                target_character_id=character_id,
                question=question,
                answer=answer,
                is_public=action.get("is_public", True)
            )
            
            # Add to public log if public
            if qna_entry.is_public:
                game_state.add_public_log_entry(
                    "qna",
                    f"【问】{question}\n【{character_id}答】{answer}",
                    related_player_id=questioner_id,
                    related_character_id=character_id
                )
            
            return {
                "success": True,
                "question": question,
                "answer": answer,
                "character_id": character_id,
                "questioner_id": questioner_id,
                "qna_id": qna_entry.id,
                "remaining_questions": game_state.max_qna_per_character_per_act - game_state.get_qna_count_for_character_act(character_id, game_state.current_act),
                "current_phase": game_state.current_phase.value
            }
            
        except Exception as e:
            logger.error(f"Failed to process Q&A action: {e}")
            return {"error": f"Failed to process Q&A: {e}"}
    
    def _process_mission_action(self, graph_state: GameGraphState, action: Dict[str, Any]) -> Dict[str, Any]:
        """Process a mission submission action."""
        try:
            player_id = action.get("player_id")
            mission_type = action.get("mission_type", "general")
            content = action.get("content")
            
            if not all([player_id, content]):
                return {"error": "Player ID and content required for mission submission"}
            
            game_state = graph_state["game_state"]
            
            # Add mission submission
            submission = game_state.add_mission_submission(player_id, mission_type, content)
            
            # Add to public log
            game_state.add_public_log_entry(
                "mission_submission",
                f"玩家提交了{mission_type}任务",
                related_player_id=player_id
            )
            
            return {
                "success": True,
                "submission_id": submission.id,
                "mission_type": mission_type,
                "player_id": player_id,
                "current_phase": game_state.current_phase.value
            }
            
        except Exception as e:
            logger.error(f"Failed to process mission action: {e}")
            return {"error": f"Failed to process mission: {e}"}
    
    def _process_phase_advance(self, graph_state: GameGraphState, action: Dict[str, Any]) -> Dict[str, Any]:
        """Process phase advancement."""
        try:
            game_state = graph_state["game_state"]
            target_phase = action.get("target_phase")
            
            if target_phase:
                try:
                    new_phase = GamePhase(target_phase)
                    game_state.current_phase = new_phase
                    
                    # Add log entry
                    game_state.add_public_log_entry(
                        "phase_change",
                        f"游戏阶段变更为：{new_phase.value}"
                    )
                    
                    return {
                        "success": True,
                        "new_phase": new_phase.value,
                        "current_act": game_state.current_act
                    }
                    
                except ValueError:
                    return {"error": f"Invalid phase: {target_phase}"}
            else:
                return {"error": "Target phase required for phase advancement"}
                
        except Exception as e:
            logger.error(f"Failed to process phase advance: {e}")
            return {"error": f"Failed to advance phase: {e}"}
    
    def _load_script(self, script_id: str) -> Optional[Script]:
        """Load script from database."""
        try:
            db = self.db_session or next(get_db())
            return db.query(Script).filter(Script.id == script_id).first()
        except Exception as e:
            logger.error(f"Failed to load script {script_id}: {e}")
            return None
    
    def _initialize_characters(self, game_state: GameState, script: Script) -> None:
        """Initialize characters from script data."""
        try:
            if script.characters:
                for char_data in script.characters:
                    character_state = CharacterState(
                        character_id=char_data.get("name", "unknown"),
                        name=char_data.get("name", "Unknown"),
                        avatar=char_data.get("avatar", ""),
                        description=char_data.get("description", "")
                    )
                    game_state.characters[character_state.character_id] = character_state
                    
                logger.info(f"Initialized {len(game_state.characters)} characters for game {game_state.game_id}")
                
        except Exception as e:
            logger.error(f"Failed to initialize characters: {e}")
    
    def get_game_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current game status summary.
        
        Args:
            session_id: Game session ID
            
        Returns:
            Status dictionary or None if game not found
        """
        try:
            summary = self.state_manager.get_game_state_summary(session_id)
            if summary:
                game_state = self.load_game(session_id)
                if game_state:
                    summary.update({
                        "turn_order": game_state.turn_order,
                        "current_turn_index": game_state.current_turn_index,
                        "public_log_count": len(game_state.public_log),
                        "qna_count": len(game_state.qna_history),
                        "mission_count": len(game_state.mission_submissions)
                    })
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get game status for session {session_id}: {e}")
            return None
