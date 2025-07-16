"""
Integration tests for the LangChain game engine.

These tests verify end-to-end functionality including API endpoints,
database integration, and game flow orchestration.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, Mock

from app.main import app
from app.database import get_db, Base
from app.models.database_models import Script
from app.schemas.pydantic_schemas import GameStartRequest, GameActionRequest, PlayerJoinRequest


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def setup_database():
    """Setup test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_script():
    """Create a sample script for testing."""
    db = TestingSessionLocal()
    try:
        script = Script(
            id="test_mystery_001",
            title="The Mansion Murder",
            category="Mystery",
            tags=["murder", "mansion", "detective"],
            players="6人 (3男3女)",
            difficulty=3,
            duration="约4小时",
            description="A classic murder mystery set in a Victorian mansion.",
            author="Test Author",
            characters=[
                {
                    "name": "Detective_Holmes",
                    "avatar": "/static/images/detective.jpg",
                    "description": "A brilliant detective with keen observation skills."
                },
                {
                    "name": "Butler_James",
                    "avatar": "/static/images/butler.jpg", 
                    "description": "The loyal butler who knows all the mansion's secrets."
                },
                {
                    "name": "Lady_Victoria",
                    "avatar": "/static/images/lady.jpg",
                    "description": "The elegant lady of the house with a mysterious past."
                }
            ]
        )
        db.add(script)
        db.commit()
        db.refresh(script)
        return script
    finally:
        db.close()


class TestLangChainGameIntegration:
    """Integration tests for LangChain game endpoints."""
    
    @pytest.mark.integration
    def test_complete_game_flow(self, client, setup_database, sample_script):
        """Test complete game flow from start to finish."""
        
        # Step 1: Start a new game
        start_request = {
            "script_id": sample_script.id,
            "user_id": "test_user_001"
        }
        
        response = client.post("/api/v1/langchain-game/start", json=start_request)
        assert response.status_code == 201
        
        start_data = response.json()
        assert start_data["success"] is True
        assert "session_id" in start_data["data"]
        
        session_id = start_data["data"]["session_id"]
        game_state = start_data["game_state"]
        
        assert game_state["script_id"] == sample_script.id
        assert game_state["current_phase"] == "initialization"
        assert game_state["current_act"] == 1
        assert game_state["character_count"] == 3
        
        # Step 2: Add players to the game
        players = [
            {"player_id": "player_001", "character_id": "Detective_Holmes"},
            {"player_id": "player_002", "character_id": "Butler_James"},
            {"player_id": "player_003", "character_id": "Lady_Victoria"}
        ]
        
        for player_data in players:
            response = client.post(
                f"/api/v1/langchain-game/session/{session_id}/join",
                json=player_data
            )
            assert response.status_code == 200
            
            join_data = response.json()
            assert join_data["success"] is True
            assert join_data["data"]["player_id"] == player_data["player_id"]
        
        # Step 3: Get game status
        response = client.get(f"/api/v1/langchain-game/session/{session_id}/status")
        assert response.status_code == 200
        
        status_data = response.json()
        assert status_data["game_state"]["player_count"] == 3
        assert len(status_data["available_actions"]) > 0
        
        # Step 4: Process character monologue (mocked)
        with patch('app.langchain.tools.dify_tools.call_monologue_workflow') as mock_monologue:
            mock_monologue.return_value = "I am Detective Holmes, here to solve this mysterious case."
            
            monologue_action = {
                "action_type": "monologue",
                "character_id": "Detective_Holmes",
                "model_name": "gpt-3.5-turbo",
                "user_id": "test_user_001"
            }
            
            response = client.post(
                f"/api/v1/langchain-game/session/{session_id}/action",
                json=monologue_action
            )
            assert response.status_code == 200
            
            action_data = response.json()
            assert action_data["success"] is True
            assert "monologue" in action_data["data"]
            assert action_data["data"]["character_id"] == "Detective_Holmes"
        
        # Step 5: Process Q&A action (mocked)
        with patch('app.langchain.tools.dify_tools.call_qna_workflow') as mock_qna:
            mock_qna.return_value = "I have been the butler here for over 20 years."
            
            qna_action = {
                "action_type": "qna",
                "character_id": "Butler_James",
                "question": "How long have you worked here?",
                "questioner_id": "player_001",
                "model_name": "gpt-3.5-turbo",
                "user_id": "test_user_001"
            }
            
            response = client.post(
                f"/api/v1/langchain-game/session/{session_id}/action",
                json=qna_action
            )
            assert response.status_code == 200
            
            action_data = response.json()
            assert action_data["success"] is True
            assert "question" in action_data["data"]
            assert "answer" in action_data["data"]
            assert action_data["data"]["character_id"] == "Butler_James"
        
        # Step 6: Submit a mission
        mission_action = {
            "action_type": "mission_submit",
            "player_id": "player_001",
            "mission_type": "evidence",
            "content": "Found a bloody knife hidden in the library."
        }
        
        response = client.post(
            f"/api/v1/langchain-game/session/{session_id}/action",
            json=mission_action
        )
        assert response.status_code == 200
        
        action_data = response.json()
        assert action_data["success"] is True
        assert action_data["data"]["mission_type"] == "evidence"
        assert action_data["data"]["player_id"] == "player_001"
        
        # Step 7: Advance game phase
        phase_action = {
            "action_type": "advance_phase",
            "target_phase": "qna"
        }
        
        response = client.post(
            f"/api/v1/langchain-game/session/{session_id}/action",
            json=phase_action
        )
        assert response.status_code == 200
        
        action_data = response.json()
        assert action_data["success"] is True
        assert action_data["game_state"]["current_phase"] == "qna"
        
        # Step 8: Get final game status with history
        response = client.get(
            f"/api/v1/langchain-game/session/{session_id}/status",
            params={"include_history": True, "max_log_entries": 10}
        )
        assert response.status_code == 200
        
        final_status = response.json()
        assert len(final_status["recent_log_entries"]) > 0
        assert len(final_status["qna_history"]) > 0
        assert len(final_status["mission_submissions"]) > 0
        
        # Verify game progress
        progress = final_status["progress"]
        assert progress["current_act"] == 1
        assert progress["current_phase"] == "qna"
        assert progress["overall_progress"] > 0
    
    @pytest.mark.integration
    def test_game_error_handling(self, client, setup_database):
        """Test error handling in game operations."""
        
        # Test starting game with non-existent script
        start_request = {
            "script_id": "nonexistent_script",
            "user_id": "test_user"
        }
        
        response = client.post("/api/v1/langchain-game/start", json=start_request)
        assert response.status_code == 400
        assert "Script not found" in response.json()["detail"]
        
        # Test joining non-existent game
        join_request = {
            "player_id": "player_001",
            "character_id": "some_character"
        }
        
        response = client.post(
            "/api/v1/langchain-game/session/nonexistent_session/join",
            json=join_request
        )
        assert response.status_code == 404
        assert "Game session not found" in response.json()["detail"]
        
        # Test getting status of non-existent game
        response = client.get("/api/v1/langchain-game/session/nonexistent_session/status")
        assert response.status_code == 404
        assert "Game session not found" in response.json()["detail"]
    
    @pytest.mark.integration
    def test_qna_limit_enforcement(self, client, setup_database, sample_script):
        """Test Q&A limit enforcement."""
        
        # Start a new game
        start_request = {
            "script_id": sample_script.id,
            "user_id": "test_user"
        }
        
        response = client.post("/api/v1/langchain-game/start", json=start_request)
        session_id = response.json()["data"]["session_id"]
        
        # Add a player
        join_request = {
            "player_id": "player_001",
            "character_id": "Detective_Holmes"
        }
        
        client.post(f"/api/v1/langchain-game/session/{session_id}/join", json=join_request)
        
        # Mock Q&A responses
        with patch('app.langchain.tools.dify_tools.call_qna_workflow') as mock_qna:
            mock_qna.return_value = "Test answer"
            
            # Ask questions up to the limit (default is 3)
            for i in range(3):
                qna_action = {
                    "action_type": "qna",
                    "character_id": "Detective_Holmes",
                    "question": f"Question {i+1}?",
                    "questioner_id": "player_001"
                }
                
                response = client.post(
                    f"/api/v1/langchain-game/session/{session_id}/action",
                    json=qna_action
                )
                assert response.status_code == 200
                assert response.json()["success"] is True
            
            # Try to ask one more question (should fail)
            qna_action = {
                "action_type": "qna",
                "character_id": "Detective_Holmes",
                "question": "One too many?",
                "questioner_id": "player_001"
            }
            
            response = client.post(
                f"/api/v1/langchain-game/session/{session_id}/action",
                json=qna_action
            )
            assert response.status_code == 200
            
            action_data = response.json()
            assert action_data["success"] is False
            assert "提问上限" in action_data["error"]
    
    @pytest.mark.integration
    def test_game_summary_endpoint(self, client, setup_database, sample_script):
        """Test game summary endpoint."""
        
        # Start a new game
        start_request = {
            "script_id": sample_script.id,
            "user_id": "test_user"
        }
        
        response = client.post("/api/v1/langchain-game/start", json=start_request)
        session_id = response.json()["data"]["session_id"]
        
        # Get game summary
        response = client.get(f"/api/v1/langchain-game/session/{session_id}/summary")
        assert response.status_code == 200
        
        summary = response.json()
        assert "game_id" in summary
        assert "script_id" in summary
        assert "formatted_summary" in summary
        assert sample_script.id in summary["formatted_summary"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
