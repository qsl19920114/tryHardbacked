"""
Unit tests for the GameEngine class.

Tests the main game orchestration logic, including game creation,
player management, action processing, and state persistence.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone

from app.langchain.engine.game_engine import GameEngine, GameEngineError
from app.langchain.state.models import GameState, GamePhase, PlayerState
from app.models.database_models import Script


class TestGameEngine:
    """Test cases for GameEngine class."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.mock_db = Mock()
        self.game_engine = GameEngine(self.mock_db)
    
    @patch('app.langchain.engine.game_engine.get_db')
    def test_game_engine_initialization(self, mock_get_db):
        """Test GameEngine initialization."""
        mock_get_db.return_value = self.mock_db
        
        engine = GameEngine()
        
        assert engine.state_manager is not None
        assert engine.graph is not None
        assert engine.monologue_tool is not None
        assert engine.qna_tool is not None
    
    def test_start_new_game_success(self):
        """Test successful game creation."""
        # Mock script
        mock_script = Mock(spec=Script)
        mock_script.id = "test_script"
        mock_script.title = "Test Mystery"
        mock_script.characters = [
            {"name": "Detective", "avatar": "/img/detective.jpg", "description": "A skilled detective"},
            {"name": "Suspect", "avatar": "/img/suspect.jpg", "description": "A suspicious character"}
        ]
        
        # Mock database query
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_script
        
        # Mock state manager
        self.game_engine.state_manager.save_game_state = Mock(return_value=True)
        
        # Start new game
        game_state = self.game_engine.start_new_game("test_script", "test_user")
        
        # Verify
        assert game_state.script_id == "test_script"
        assert game_state.current_phase == GamePhase.INITIALIZATION
        assert len(game_state.characters) == 2
        assert "Detective" in game_state.characters
        assert "Suspect" in game_state.characters
        assert game_state.started_at is not None
        
        # Verify state manager was called
        self.game_engine.state_manager.save_game_state.assert_called_once()
    
    def test_start_new_game_script_not_found(self):
        """Test game creation with non-existent script."""
        # Mock database query to return None
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Attempt to start game
        with pytest.raises(GameEngineError, match="Script not found"):
            self.game_engine.start_new_game("nonexistent_script")
    
    def test_start_new_game_save_failure(self):
        """Test game creation with save failure."""
        # Mock script
        mock_script = Mock(spec=Script)
        mock_script.id = "test_script"
        mock_script.title = "Test Mystery"
        mock_script.characters = []
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_script
        
        # Mock state manager to fail save
        self.game_engine.state_manager.save_game_state = Mock(return_value=False)
        
        # Attempt to start game
        with pytest.raises(GameEngineError, match="Failed to save initial game state"):
            self.game_engine.start_new_game("test_script")
    
    def test_load_game_success(self):
        """Test successful game loading."""
        # Mock game state
        mock_game_state = Mock(spec=GameState)
        mock_game_state.game_id = "test_game"
        
        self.game_engine.state_manager.load_game_state = Mock(return_value=mock_game_state)
        
        # Load game
        result = self.game_engine.load_game("test_session")
        
        # Verify
        assert result == mock_game_state
        self.game_engine.state_manager.load_game_state.assert_called_once_with("test_session")
    
    def test_load_game_not_found(self):
        """Test loading non-existent game."""
        self.game_engine.state_manager.load_game_state = Mock(return_value=None)
        
        # Load game
        result = self.game_engine.load_game("nonexistent_session")
        
        # Verify
        assert result is None
    
    def test_add_player_success(self):
        """Test successful player addition."""
        # Mock game state
        mock_game_state = GameState(
            game_id="test_game",
            script_id="test_script",
            session_id="test_session"
        )
        
        self.game_engine.load_game = Mock(return_value=mock_game_state)
        self.game_engine.state_manager.save_game_state = Mock(return_value=True)
        
        # Add player
        success = self.game_engine.add_player("test_session", "player1", "char1")
        
        # Verify
        assert success is True
        assert "player1" in mock_game_state.players
        assert mock_game_state.players["player1"].character_id == "char1"
        assert "player1" in mock_game_state.turn_order
        assert len(mock_game_state.public_log) > 0
    
    def test_add_player_game_not_found(self):
        """Test adding player to non-existent game."""
        self.game_engine.load_game = Mock(return_value=None)
        
        # Add player
        success = self.game_engine.add_player("nonexistent_session", "player1")
        
        # Verify
        assert success is False
    
    def test_process_monologue_action(self):
        """Test processing monologue action."""
        # Mock game state
        mock_game_state = GameState(
            game_id="test_game",
            script_id="test_script",
            session_id="test_session"
        )
        
        self.game_engine.load_game = Mock(return_value=mock_game_state)
        self.game_engine.state_manager.save_game_state = Mock(return_value=True)
        
        # Mock monologue tool
        self.game_engine.monologue_tool._run = Mock(return_value="I am a mysterious character.")
        
        # Process action
        action = {
            "action_type": "monologue",
            "character_id": "test_char",
            "model_name": "gpt-3.5-turbo",
            "user_id": "test_user"
        }
        
        result = self.game_engine.process_action("test_session", action)
        
        # Verify
        assert result["success"] is True
        assert result["monologue"] == "I am a mysterious character."
        assert result["character_id"] == "test_char"
        assert len(mock_game_state.public_log) > 0
        
        # Verify tool was called
        self.game_engine.monologue_tool._run.assert_called_once_with(
            char_id="test_char",
            act_num=1,
            model_name="gpt-3.5-turbo",
            user_id="test_user"
        )
    
    def test_process_qna_action(self):
        """Test processing Q&A action."""
        # Mock game state
        mock_game_state = GameState(
            game_id="test_game",
            script_id="test_script",
            session_id="test_session"
        )
        
        # Add player
        player = PlayerState(player_id="player1")
        mock_game_state.players["player1"] = player
        
        self.game_engine.load_game = Mock(return_value=mock_game_state)
        self.game_engine.state_manager.save_game_state = Mock(return_value=True)
        
        # Mock Q&A tool
        self.game_engine.qna_tool._run = Mock(return_value="I am Detective Smith.")
        
        # Process action
        action = {
            "action_type": "qna",
            "character_id": "test_char",
            "question": "What is your name?",
            "questioner_id": "player1",
            "model_name": "gpt-3.5-turbo",
            "user_id": "test_user"
        }
        
        result = self.game_engine.process_action("test_session", action)
        
        # Verify
        assert result["success"] is True
        assert result["question"] == "What is your name?"
        assert result["answer"] == "I am Detective Smith."
        assert result["character_id"] == "test_char"
        assert result["questioner_id"] == "player1"
        assert len(mock_game_state.qna_history) == 1
        assert len(mock_game_state.public_log) > 0
        
        # Verify player stats updated
        assert mock_game_state.players["player1"].qna_count_current_act == 1
        assert mock_game_state.players["player1"].total_qna_count == 1
    
    def test_process_qna_action_limit_reached(self):
        """Test Q&A action when limit is reached."""
        # Mock game state with Q&A limit reached
        mock_game_state = GameState(
            game_id="test_game",
            script_id="test_script",
            session_id="test_session",
            max_qna_per_character_per_act=1
        )
        
        # Set Q&A count to limit
        mock_game_state.qna_counts = {"test_char": {"1": 1}}
        
        self.game_engine.load_game = Mock(return_value=mock_game_state)
        
        # Process action
        action = {
            "action_type": "qna",
            "character_id": "test_char",
            "question": "What is your name?",
            "questioner_id": "player1"
        }
        
        result = self.game_engine.process_action("test_session", action)
        
        # Verify
        assert result["success"] is False
        assert "提问上限" in result["error"]
    
    def test_process_mission_action(self):
        """Test processing mission submission action."""
        # Mock game state
        mock_game_state = GameState(
            game_id="test_game",
            script_id="test_script",
            session_id="test_session"
        )
        
        # Add player
        player = PlayerState(player_id="player1")
        mock_game_state.players["player1"] = player
        
        self.game_engine.load_game = Mock(return_value=mock_game_state)
        self.game_engine.state_manager.save_game_state = Mock(return_value=True)
        
        # Process action
        action = {
            "action_type": "mission_submit",
            "player_id": "player1",
            "mission_type": "evidence",
            "content": "Found a bloody knife in the garden."
        }
        
        result = self.game_engine.process_action("test_session", action)
        
        # Verify
        assert result["success"] is True
        assert result["mission_type"] == "evidence"
        assert result["player_id"] == "player1"
        assert len(mock_game_state.mission_submissions) == 1
        assert len(mock_game_state.public_log) > 0
        
        # Verify player's submission list updated
        assert len(mock_game_state.players["player1"].mission_submissions) == 1
    
    def test_process_unknown_action(self):
        """Test processing unknown action type."""
        mock_game_state = GameState(
            game_id="test_game",
            script_id="test_script",
            session_id="test_session"
        )
        
        self.game_engine.load_game = Mock(return_value=mock_game_state)
        
        # Process unknown action
        action = {"action_type": "unknown_action"}
        
        result = self.game_engine.process_action("test_session", action)
        
        # Verify
        assert "error" in result
        assert "Unknown action type" in result["error"]
    
    def test_get_game_status(self):
        """Test getting game status."""
        # Mock state manager
        mock_summary = {
            "game_id": "test_game",
            "script_id": "test_script",
            "current_act": 1,
            "current_phase": "qna",
            "player_count": 2,
            "character_count": 3
        }
        
        mock_game_state = GameState(
            game_id="test_game",
            script_id="test_script",
            session_id="test_session"
        )
        mock_game_state.turn_order = ["player1", "player2"]
        mock_game_state.public_log = [Mock(), Mock(), Mock()]
        mock_game_state.qna_history = [Mock(), Mock()]
        mock_game_state.mission_submissions = [Mock()]
        
        self.game_engine.state_manager.get_game_state_summary = Mock(return_value=mock_summary)
        self.game_engine.load_game = Mock(return_value=mock_game_state)
        
        # Get status
        status = self.game_engine.get_game_status("test_session")
        
        # Verify
        assert status is not None
        assert status["game_id"] == "test_game"
        assert status["turn_order"] == ["player1", "player2"]
        assert status["public_log_count"] == 3
        assert status["qna_count"] == 2
        assert status["mission_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__])
