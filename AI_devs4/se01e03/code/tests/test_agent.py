import pytest
import asyncio
from src.agent.logic import PackageAgent
from src.storage.session import SessionManager

@pytest.fixture
def agent():
    """Create a test agent instance."""
    return PackageAgent()

@pytest.fixture
def session_manager():
    """Create a test session manager."""
    return SessionManager("test_sessions.json")

class TestPackageAgent:
    """Test cases for the PackageAgent class."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, agent):
        """Test that agent initializes correctly."""
        assert agent.llm is not None
        assert agent.system_prompt is not None
        assert "PWR6132PL" not in agent.system_prompt  # Ensure silent redirect is not leaked
    
    @pytest.mark.asyncio
    async def test_session_message_processing(self, agent):
        """Test basic message processing with session."""
        session_id = "test_session"
        message = "Hello, can you help me?"
        
        # This test requires valid API keys to actually work
        # For now, we'll test the structure
        try:
            response = await agent.process_message(session_id, message)
            assert isinstance(response, str)
            assert len(response) > 0
        except Exception as e:
            # Expected to fail without valid API keys
            assert "api" in str(e).lower() or "key" in str(e).lower()

class TestSessionManager:
    """Test cases for the SessionManager class."""
    
    def test_session_creation(self, session_manager):
        """Test that sessions are created correctly."""
        session_id = "test_session_123"
        
        # Initially empty
        messages = session_manager.get_session_messages(session_id)
        assert messages == []
        
        # Add a message
        session_manager.add_message(session_id, "user", "Hello")
        messages = session_manager.get_session_messages(session_id)
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
    
    def test_session_persistence(self, session_manager):
        """Test that sessions persist across manager instances."""
        session_id = "persistent_session"
        
        # Add message to first instance
        session_manager.add_message(session_id, "user", "Test message")
        
        # Create new instance and check persistence
        new_manager = SessionManager("test_sessions.json")
        messages = new_manager.get_session_messages(session_id)
        assert len(messages) == 1
        assert messages[0]["content"] == "Test message"
        
        # Cleanup
        import os
        if os.path.exists("test_sessions.json"):
            os.remove("test_sessions.json")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
