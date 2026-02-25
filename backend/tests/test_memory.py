import pytest
from unittest.mock import Mock, patch
import json
import time

from app.core.memory import ConversationMemory


class TestConversationMemory:
    """Test conversation memory functionality"""
    
    @pytest.fixture
    def memory(self, mock_redis):
        """Create memory instance with mocked Redis"""
        with patch('redis.from_url', return_value=mock_redis):
            return ConversationMemory("redis://localhost:6379")
    
    def test_add_message(self, memory, mock_redis):
        """Test storing a message"""
        session_id = "test-session-123"
        memory.add_message(session_id, "user", "Hello!")
        
        # Verify Redis lpush was called
        mock_redis.lpush.assert_called_once()
        call_args = mock_redis.lpush.call_args
        assert call_args[0][0] == f"conversation:{session_id}"
        
        # Verify message structure
        message = json.loads(call_args[0][1])
        assert message["role"] == "user"
        assert message["content"] == "Hello!"
        assert "timestamp" in message
    
    def test_add_message_with_metadata(self, memory, mock_redis):
        """Test storing message with metadata"""
        metadata = {"skill": "weather", "location": "Pune"}
        memory.add_message("session-1", "assistant", "It's sunny!", metadata)
        
        call_args = mock_redis.lpush.call_args
        message = json.loads(call_args[0][1])
        assert message["metadata"] == metadata
    
    def test_add_message_trims_to_20(self, memory, mock_redis):
        """Test that only last 20 messages are kept"""
        memory.add_message("session-1", "user", "Message 1")
        
        # Verify ltrim was called with correct parameters
        mock_redis.ltrim.assert_called_once_with(f"conversation:session-1", 0, 19)
    
    def test_add_message_sets_expiry(self, memory, mock_redis):
        """Test that messages expire after 24 hours"""
        memory.add_message("session-1", "user", "Hello")
        
        mock_redis.expire.assert_called_once_with(f"conversation:session-1", 86400)
    
    def test_get_context_empty(self, memory, mock_redis):
        """Test retrieving context from empty session"""
        mock_redis.lrange.return_value = []
        
        context = memory.get_context("empty-session")
        
        assert context == []
    
    def test_get_context_with_messages(self, memory, mock_redis):
        """Test retrieving context with messages"""
        messages = [
            json.dumps({"role": "user", "content": "Hello", "timestamp": time.time()}),
            json.dumps({"role": "assistant", "content": "Hi!", "timestamp": time.time()}),
        ]
        mock_redis.lrange.return_value = messages
        
        context = memory.get_context("session-with-messages")
        
        assert len(context) == 2
        assert context[0]["role"] == "user"
        assert context[0]["content"] == "Hello"
        assert context[1]["role"] == "assistant"
        assert context[1]["content"] == "Hi!"
    
    def test_get_context_returns_only_role_and_content(self, memory, mock_redis):
        """Test that get_context returns only role and content for GPT"""
        messages = [
            json.dumps({
                "role": "user",
                "content": "Hello",
                "timestamp": time.time(),
                "metadata": {"extra": "data"}
            }),
        ]
        mock_redis.lrange.return_value = messages
        
        context = memory.get_context("session-1")
        
        assert "timestamp" not in context[0]
        assert "metadata" not in context[0]
        assert "role" in context[0]
        assert "content" in context[0]
    
    def test_get_context_order(self, memory, mock_redis):
        """Test that messages are returned in chronological order"""
        # Redis stores newest first, so lrange returns [newest, ..., oldest]
        messages = [
            json.dumps({"role": "assistant", "content": "Last"}),
            json.dumps({"role": "user", "content": "First"}),
        ]
        mock_redis.lrange.return_value = messages
        
        context = memory.get_context("session-1")
        
        # Should be reversed to chronological order
        assert context[0]["content"] == "First"
        assert context[1]["content"] == "Last"
    
    def test_clear_session(self, memory, mock_redis):
        """Test clearing a session"""
        memory.clear_session("session-to-clear")
        
        mock_redis.delete.assert_called_once_with("conversation:session-to-clear")
