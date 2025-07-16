"""
Unit tests for Dify integration tools.

Tests the LangChain custom tools that wrap Dify workflows,
including input validation, error handling, and tool execution.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pydantic import ValidationError

from app.langchain.tools.dify_tools import (
    DifyMonologueTool, DifyQnATool, MonologueInput, QnAInput,
    create_dify_tools, get_tool_by_name
)
from app.services.dify_service import DifyServiceError


class TestMonologueInput:
    """Test cases for MonologueInput schema."""
    
    def test_valid_input(self):
        """Test valid MonologueInput creation."""
        input_data = MonologueInput(
            char_id="test_char",
            act_num=2,
            model_name="gpt-4",
            user_id="test_user"
        )
        
        assert input_data.char_id == "test_char"
        assert input_data.act_num == 2
        assert input_data.model_name == "gpt-4"
        assert input_data.user_id == "test_user"
    
    def test_default_model_name(self):
        """Test default model name."""
        input_data = MonologueInput(
            char_id="test_char",
            act_num=1,
            user_id="test_user"
        )
        
        assert input_data.model_name == "gpt-3.5-turbo"
    
    def test_invalid_act_num(self):
        """Test validation of act_num."""
        with pytest.raises(ValidationError):
            MonologueInput(
                char_id="test_char",
                act_num=0,  # Invalid: must be >= 1
                user_id="test_user"
            )
        
        with pytest.raises(ValidationError):
            MonologueInput(
                char_id="test_char",
                act_num=4,  # Invalid: must be <= 3
                user_id="test_user"
            )
    
    def test_empty_char_id(self):
        """Test validation of char_id."""
        with pytest.raises(ValidationError):
            MonologueInput(
                char_id="",  # Invalid: empty string
                act_num=1,
                user_id="test_user"
            )
        
        with pytest.raises(ValidationError):
            MonologueInput(
                char_id="   ",  # Invalid: whitespace only
                act_num=1,
                user_id="test_user"
            )
    
    def test_char_id_trimming(self):
        """Test char_id trimming."""
        input_data = MonologueInput(
            char_id="  test_char  ",
            act_num=1,
            user_id="test_user"
        )
        
        assert input_data.char_id == "test_char"


class TestQnAInput:
    """Test cases for QnAInput schema."""
    
    def test_valid_input(self):
        """Test valid QnAInput creation."""
        input_data = QnAInput(
            char_id="test_char",
            act_num=2,
            query="What is your name?",
            model_name="gpt-4",
            user_id="test_user"
        )
        
        assert input_data.char_id == "test_char"
        assert input_data.act_num == 2
        assert input_data.query == "What is your name?"
        assert input_data.model_name == "gpt-4"
        assert input_data.user_id == "test_user"
    
    def test_empty_query(self):
        """Test validation of query."""
        with pytest.raises(ValidationError):
            QnAInput(
                char_id="test_char",
                act_num=1,
                query="",  # Invalid: empty string
                user_id="test_user"
            )
        
        with pytest.raises(ValidationError):
            QnAInput(
                char_id="test_char",
                act_num=1,
                query="   ",  # Invalid: whitespace only
                user_id="test_user"
            )
    
    def test_query_too_long(self):
        """Test validation of query length."""
        long_query = "x" * 1001  # Too long
        
        with pytest.raises(ValidationError):
            QnAInput(
                char_id="test_char",
                act_num=1,
                query=long_query,
                user_id="test_user"
            )
    
    def test_query_trimming(self):
        """Test query trimming."""
        input_data = QnAInput(
            char_id="test_char",
            act_num=1,
            query="  What is your name?  ",
            user_id="test_user"
        )
        
        assert input_data.query == "What is your name?"


class TestDifyMonologueTool:
    """Test cases for DifyMonologueTool."""
    
    def test_tool_properties(self):
        """Test tool basic properties."""
        tool = DifyMonologueTool()
        
        assert tool.name == "dify_monologue"
        assert "character monologue" in tool.description.lower()
        assert tool.args_schema == MonologueInput
        assert tool.return_direct is False
    
    @patch('app.langchain.tools.dify_tools.call_monologue_workflow')
    def test_successful_run(self, mock_call_workflow):
        """Test successful tool execution."""
        # Setup mock
        mock_call_workflow.return_value = "I am a mysterious character with a dark past."
        
        tool = DifyMonologueTool()
        
        # Execute tool
        result = tool._run(
            char_id="test_char",
            act_num=1,
            model_name="gpt-3.5-turbo",
            user_id="test_user"
        )
        
        # Verify
        assert result == "I am a mysterious character with a dark past."
        mock_call_workflow.assert_called_once_with(
            char_id="test_char",
            act_num=1,
            model_name="gpt-3.5-turbo",
            user_id="test_user"
        )
    
    @patch('app.langchain.tools.dify_tools.call_monologue_workflow')
    def test_dify_service_error(self, mock_call_workflow):
        """Test handling of DifyServiceError."""
        # Setup mock to raise error
        mock_call_workflow.side_effect = DifyServiceError("API error")
        
        tool = DifyMonologueTool()
        
        # Execute tool
        result = tool._run(
            char_id="test_char",
            act_num=1,
            model_name="gpt-3.5-turbo",
            user_id="test_user"
        )
        
        # Verify error handling
        assert "暂时无法进行自我介绍" in result
        assert "test_char" in result
    
    @patch('app.langchain.tools.dify_tools.call_monologue_workflow')
    def test_unexpected_error(self, mock_call_workflow):
        """Test handling of unexpected errors."""
        # Setup mock to raise unexpected error
        mock_call_workflow.side_effect = Exception("Unexpected error")
        
        tool = DifyMonologueTool()
        
        # Execute tool
        result = tool._run(
            char_id="test_char",
            act_num=1,
            model_name="gpt-3.5-turbo",
            user_id="test_user"
        )
        
        # Verify error handling
        assert "发生了错误" in result
        assert "test_char" in result
    
    @patch('app.langchain.tools.dify_tools.call_monologue_workflow')
    def test_with_callback_manager(self, mock_call_workflow):
        """Test tool execution with callback manager."""
        mock_call_workflow.return_value = "Test monologue"
        
        # Create mock callback manager
        mock_callback = Mock()
        
        tool = DifyMonologueTool()
        
        # Execute tool with callback
        result = tool._run(
            char_id="test_char",
            act_num=1,
            model_name="gpt-3.5-turbo",
            user_id="test_user",
            run_manager=mock_callback
        )
        
        # Verify callback calls
        assert result == "Test monologue"
        mock_callback.on_tool_start.assert_called_once()
        mock_callback.on_tool_end.assert_called_once_with("Test monologue")


class TestDifyQnATool:
    """Test cases for DifyQnATool."""
    
    def test_tool_properties(self):
        """Test tool basic properties."""
        tool = DifyQnATool()
        
        assert tool.name == "dify_qna"
        assert "question" in tool.description.lower()
        assert tool.args_schema == QnAInput
        assert tool.return_direct is False
    
    @patch('app.langchain.tools.dify_tools.call_qna_workflow')
    def test_successful_run(self, mock_call_workflow):
        """Test successful tool execution."""
        # Setup mock
        mock_call_workflow.return_value = "My name is Detective Smith."
        
        tool = DifyQnATool()
        
        # Execute tool
        result = tool._run(
            char_id="test_char",
            act_num=1,
            query="What is your name?",
            model_name="gpt-3.5-turbo",
            user_id="test_user"
        )
        
        # Verify
        assert result == "My name is Detective Smith."
        mock_call_workflow.assert_called_once_with(
            char_id="test_char",
            act_num=1,
            query="What is your name?",
            model_name="gpt-3.5-turbo",
            user_id="test_user"
        )
    
    @patch('app.langchain.tools.dify_tools.call_qna_workflow')
    def test_dify_service_error(self, mock_call_workflow):
        """Test handling of DifyServiceError."""
        # Setup mock to raise error
        mock_call_workflow.side_effect = DifyServiceError("API error")
        
        tool = DifyQnATool()
        
        # Execute tool
        result = tool._run(
            char_id="test_char",
            act_num=1,
            query="What is your name?",
            model_name="gpt-3.5-turbo",
            user_id="test_user"
        )
        
        # Verify error handling
        assert "暂时无法回答这个问题" in result
        assert "test_char" in result
    
    @patch('app.langchain.tools.dify_tools.call_qna_workflow')
    def test_unexpected_error(self, mock_call_workflow):
        """Test handling of unexpected errors."""
        # Setup mock to raise unexpected error
        mock_call_workflow.side_effect = Exception("Unexpected error")
        
        tool = DifyQnATool()
        
        # Execute tool
        result = tool._run(
            char_id="test_char",
            act_num=1,
            query="What is your name?",
            model_name="gpt-3.5-turbo",
            user_id="test_user"
        )
        
        # Verify error handling
        assert "发生了错误" in result
        assert "test_char" in result


class TestToolUtilities:
    """Test cases for tool utility functions."""
    
    def test_create_dify_tools(self):
        """Test create_dify_tools function."""
        tools = create_dify_tools()
        
        assert len(tools) == 2
        assert any(tool.name == "dify_monologue" for tool in tools)
        assert any(tool.name == "dify_qna" for tool in tools)
    
    def test_get_tool_by_name(self):
        """Test get_tool_by_name function."""
        # Test existing tools
        monologue_tool = get_tool_by_name("dify_monologue")
        assert monologue_tool is not None
        assert isinstance(monologue_tool, DifyMonologueTool)
        
        qna_tool = get_tool_by_name("dify_qna")
        assert qna_tool is not None
        assert isinstance(qna_tool, DifyQnATool)
        
        # Test non-existing tool
        unknown_tool = get_tool_by_name("unknown_tool")
        assert unknown_tool is None


if __name__ == "__main__":
    pytest.main([__file__])
