"""
Unit tests for LangChain state models.

Tests the Pydantic models used for game state management,
including validation, serialization, and business logic methods.
"""

import pytest
from datetime import datetime, timezone
from app.langchain.state.models import (
    GameState, PlayerState, CharacterState, GamePhase,
    QnAEntry, MissionSubmission, PublicLogEntry,
    PlayerRole, MissionStatus
)


class TestGameState:
    """Test cases for GameState model."""
    
    def test_game_state_creation(self):
        """Test basic GameState creation."""
        game_state = GameState(
            game_id="test_game_1",
            script_id="test_script_1",
            session_id="test_session_1"
        )
        
        assert game_state.game_id == "test_game_1"
        assert game_state.script_id == "test_script_1"
        assert game_state.session_id == "test_session_1"
        assert game_state.current_act == 1
        assert game_state.current_phase == GamePhase.INITIALIZATION
        assert game_state.max_acts == 3
        assert len(game_state.players) == 0
        assert len(game_state.characters) == 0
        assert len(game_state.turn_order) == 0
    
    def test_game_state_with_players(self):
        """Test GameState with players."""
        game_state = GameState(
            game_id="test_game_1",
            script_id="test_script_1",
            session_id="test_session_1"
        )
        
        # Add players
        player1 = PlayerState(player_id="player1", character_id="char1")
        player2 = PlayerState(player_id="player2", character_id="char2")
        
        game_state.players["player1"] = player1
        game_state.players["player2"] = player2
        game_state.turn_order = ["player1", "player2"]
        
        assert len(game_state.players) == 2
        assert game_state.turn_order == ["player1", "player2"]
        
        # Test current player
        current_player = game_state.get_current_player()
        assert current_player is not None
        assert current_player.player_id == "player1"
        
        # Test advance turn
        game_state.advance_turn()
        current_player = game_state.get_current_player()
        assert current_player.player_id == "player2"
        
        # Test wrap around
        game_state.advance_turn()
        current_player = game_state.get_current_player()
        assert current_player.player_id == "player1"
    
    def test_qna_count_management(self):
        """Test Q&A count tracking."""
        game_state = GameState(
            game_id="test_game_1",
            script_id="test_script_1",
            session_id="test_session_1"
        )
        
        # Test initial count
        count = game_state.get_qna_count_for_character_act("char1", 1)
        assert count == 0
        
        # Test can ask question
        can_ask = game_state.can_ask_question("char1", 1)
        assert can_ask is True
        
        # Increment count
        game_state.increment_qna_count("char1", 1)
        count = game_state.get_qna_count_for_character_act("char1", 1)
        assert count == 1
        
        # Test multiple increments
        game_state.increment_qna_count("char1", 1)
        game_state.increment_qna_count("char1", 1)
        count = game_state.get_qna_count_for_character_act("char1", 1)
        assert count == 3
        
        # Test limit reached
        can_ask = game_state.can_ask_question("char1", 1)
        assert can_ask is False
        
        # Test different act
        can_ask = game_state.can_ask_question("char1", 2)
        assert can_ask is True
    
    def test_add_qna_entry(self):
        """Test adding Q&A entries."""
        game_state = GameState(
            game_id="test_game_1",
            script_id="test_script_1",
            session_id="test_session_1"
        )
        
        # Add player
        player1 = PlayerState(player_id="player1")
        game_state.players["player1"] = player1
        
        # Add Q&A entry
        entry = game_state.add_qna_entry(
            questioner_id="player1",
            target_character_id="char1",
            question="Test question?",
            answer="Test answer."
        )
        
        assert len(game_state.qna_history) == 1
        assert entry.questioner_id == "player1"
        assert entry.target_character_id == "char1"
        assert entry.question == "Test question?"
        assert entry.answer == "Test answer."
        assert entry.act_number == 1
        assert entry.is_public is True
        
        # Check counts updated
        count = game_state.get_qna_count_for_character_act("char1", 1)
        assert count == 1
        
        player = game_state.players["player1"]
        assert player.qna_count_current_act == 1
        assert player.total_qna_count == 1
    
    def test_add_mission_submission(self):
        """Test adding mission submissions."""
        game_state = GameState(
            game_id="test_game_1",
            script_id="test_script_1",
            session_id="test_session_1"
        )
        
        # Add player
        player1 = PlayerState(player_id="player1")
        game_state.players["player1"] = player1
        
        # Add mission submission
        submission = game_state.add_mission_submission(
            player_id="player1",
            mission_type="evidence",
            content="Found a clue!"
        )
        
        assert len(game_state.mission_submissions) == 1
        assert submission.player_id == "player1"
        assert submission.mission_type == "evidence"
        assert submission.content == "Found a clue!"
        assert submission.status == MissionStatus.PENDING
        assert submission.act_number == 1
        
        # Check player's submission list updated
        player = game_state.players["player1"]
        assert len(player.mission_submissions) == 1
        assert player.mission_submissions[0] == submission.id
    
    def test_public_log_entry(self):
        """Test adding public log entries."""
        game_state = GameState(
            game_id="test_game_1",
            script_id="test_script_1",
            session_id="test_session_1"
        )
        
        # Add log entry
        entry = game_state.add_public_log_entry(
            entry_type="test",
            content="Test log entry",
            related_player_id="player1"
        )
        
        assert len(game_state.public_log) == 1
        assert entry.entry_type == "test"
        assert entry.content == "Test log entry"
        assert entry.act_number == 1
        assert entry.related_player_id == "player1"


class TestPlayerState:
    """Test cases for PlayerState model."""
    
    def test_player_state_creation(self):
        """Test basic PlayerState creation."""
        player = PlayerState(player_id="test_player")
        
        assert player.player_id == "test_player"
        assert player.character_id is None
        assert player.role == PlayerRole.PLAYER
        assert player.is_active is True
        assert player.qna_count_current_act == 0
        assert player.total_qna_count == 0
        assert len(player.mission_submissions) == 0
        assert player.notes == ""
        assert isinstance(player.last_activity, datetime)
    
    def test_player_state_with_character(self):
        """Test PlayerState with assigned character."""
        player = PlayerState(
            player_id="test_player",
            character_id="test_character",
            role=PlayerRole.GAME_MASTER
        )
        
        assert player.character_id == "test_character"
        assert player.role == PlayerRole.GAME_MASTER


class TestCharacterState:
    """Test cases for CharacterState model."""
    
    def test_character_state_creation(self):
        """Test basic CharacterState creation."""
        character = CharacterState(
            character_id="test_char",
            name="Test Character",
            avatar="/images/test.jpg",
            description="A test character"
        )
        
        assert character.character_id == "test_char"
        assert character.name == "Test Character"
        assert character.avatar == "/images/test.jpg"
        assert character.description == "A test character"
        assert character.is_alive is True
        assert character.suspicion_level == 0
        assert len(character.secrets_revealed) == 0
        assert len(character.relationships) == 0
        assert len(character.custom_attributes) == 0
    
    def test_character_state_with_attributes(self):
        """Test CharacterState with custom attributes."""
        character = CharacterState(
            character_id="test_char",
            name="Test Character",
            avatar="/images/test.jpg",
            description="A test character",
            suspicion_level=50,
            secrets_revealed=["secret1", "secret2"],
            relationships={"char2": "friend", "char3": "enemy"},
            custom_attributes={"age": 30, "occupation": "detective"}
        )
        
        assert character.suspicion_level == 50
        assert len(character.secrets_revealed) == 2
        assert character.relationships["char2"] == "friend"
        assert character.custom_attributes["age"] == 30


class TestQnAEntry:
    """Test cases for QnAEntry model."""
    
    def test_qna_entry_creation(self):
        """Test QnAEntry creation."""
        entry = QnAEntry(
            questioner_id="player1",
            target_character_id="char1",
            question="Who are you?",
            answer="I am a character.",
            act_number=1
        )
        
        assert entry.questioner_id == "player1"
        assert entry.target_character_id == "char1"
        assert entry.question == "Who are you?"
        assert entry.answer == "I am a character."
        assert entry.act_number == 1
        assert entry.is_public is True
        assert isinstance(entry.timestamp, datetime)
        assert len(entry.id) > 0


class TestMissionSubmission:
    """Test cases for MissionSubmission model."""
    
    def test_mission_submission_creation(self):
        """Test MissionSubmission creation."""
        submission = MissionSubmission(
            player_id="player1",
            mission_type="evidence",
            content="Found a bloody knife",
            act_number=2
        )
        
        assert submission.player_id == "player1"
        assert submission.mission_type == "evidence"
        assert submission.content == "Found a bloody knife"
        assert submission.act_number == 2
        assert submission.status == MissionStatus.PENDING
        assert submission.review_notes == ""
        assert isinstance(submission.timestamp, datetime)
        assert len(submission.id) > 0


class TestPublicLogEntry:
    """Test cases for PublicLogEntry model."""
    
    def test_public_log_entry_creation(self):
        """Test PublicLogEntry creation."""
        entry = PublicLogEntry(
            entry_type="qna",
            content="Player asked a question",
            act_number=1,
            related_player_id="player1",
            related_character_id="char1"
        )
        
        assert entry.entry_type == "qna"
        assert entry.content == "Player asked a question"
        assert entry.act_number == 1
        assert entry.related_player_id == "player1"
        assert entry.related_character_id == "char1"
        assert isinstance(entry.timestamp, datetime)
        assert len(entry.id) > 0


class TestEnums:
    """Test cases for enum values."""

    def test_game_phase_enum(self):
        """Test GamePhase enum values."""
        assert GamePhase.INITIALIZATION == "initialization"
        assert GamePhase.MONOLOGUE == "monologue"
        assert GamePhase.QNA == "qna"
        assert GamePhase.MISSION_SUBMIT == "mission_submit"
        assert GamePhase.FINAL_CHOICE == "final_choice"
        assert GamePhase.COMPLETED == "completed"
        assert GamePhase.PAUSED == "paused"

    def test_player_role_enum(self):
        """Test PlayerRole enum values."""
        assert PlayerRole.PLAYER == "player"
        assert PlayerRole.GAME_MASTER == "game_master"
        assert PlayerRole.OBSERVER == "observer"

    def test_mission_status_enum(self):
        """Test MissionStatus enum values."""
        assert MissionStatus.PENDING == "pending"
        assert MissionStatus.SUBMITTED == "submitted"
        assert MissionStatus.REVIEWED == "reviewed"
        assert MissionStatus.ACCEPTED == "accepted"
        assert MissionStatus.REJECTED == "rejected"


if __name__ == "__main__":
    pytest.main([__file__])
