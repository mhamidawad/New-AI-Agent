"""Tests for the main CodingAgent class."""

import pytest
from unittest.mock import Mock, AsyncMock
from ai_coding_agent.core.agent import CodingAgent
from ai_coding_agent.core.config import Config


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    config = Config()
    config.openai_api_key = "test_key"
    config.model.name = "gpt-4"
    return config


@pytest.fixture
def mock_agent(mock_config):
    """Create a mock agent for testing."""
    agent = CodingAgent(mock_config)
    agent.provider = AsyncMock()
    return agent


@pytest.mark.asyncio
async def test_chat_functionality(mock_agent):
    """Test basic chat functionality."""
    # Mock provider response
    mock_agent.provider.generate_response.return_value = Mock(
        content="Hello! I'm here to help with coding tasks."
    )
    
    response = await mock_agent.chat("Hello")
    
    assert response == "Hello! I'm here to help with coding tasks."
    mock_agent.provider.generate_response.assert_called_once()


@pytest.mark.asyncio
async def test_code_generation(mock_agent):
    """Test code generation functionality."""
    # Mock provider response
    mock_agent.provider.generate_code.return_value = Mock(
        content="def hello_world():\n    print('Hello, World!')"
    )
    
    code = await mock_agent.generate_code("Create a hello world function", "python")
    
    assert "hello_world" in code
    assert "print" in code
    mock_agent.provider.generate_code.assert_called_once()


def test_language_detection(mock_agent):
    """Test programming language detection."""
    assert mock_agent._detect_language("test.py") == "python"
    assert mock_agent._detect_language("test.js") == "javascript"
    assert mock_agent._detect_language("test.java") == "java"
    assert mock_agent._detect_language("test.unknown") == "text"


def test_agent_status(mock_agent):
    """Test agent status reporting."""
    status = mock_agent.get_status()
    
    assert "model" in status
    assert "provider" in status
    assert "context" in status
    assert "config" in status