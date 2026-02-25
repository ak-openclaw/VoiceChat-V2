import pytest
from unittest.mock import AsyncMock, patch

from app.services.gpt import GPTService


class TestGPTService:
    """Test GPT chat service"""
    
    @pytest.fixture
    def gpt_service(self):
        return GPTService(api_key="test-key", model="gpt-4o-mini")
    
    @pytest.mark.asyncio
    async def test_chat_success(self, gpt_service, sample_gpt_response):
        """Test successful chat completion"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = AsyncMock(return_value=sample_gpt_response)
            mock_response.raise_for_status = AsyncMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            context = [{"role": "user", "content": "Hello"}]
            result = await gpt_service.chat(context, "How are you?")
            
            assert result == "The weather is looking great today!"
    
    @pytest.mark.asyncio
    async def test_chat_with_context(self, gpt_service, sample_gpt_response):
        """Test that context is properly included"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json = AsyncMock(return_value=sample_gpt_response)
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            context = [
                {"role": "user", "content": "My name is Ak"},
                {"role": "assistant", "content": "Nice to meet you Ak!"},
            ]
            
            await gpt_service.chat(context, "What's my name?")
            
            # Verify context was included in API call
            call_args = mock_client_instance.post.call_args
            sent_messages = call_args[1]["json"]["messages"]
            
            assert len(sent_messages) == 4  # System + 2 context + current
            assert sent_messages[1]["content"] == "My name is Ak"
            assert sent_messages[2]["content"] == "Nice to meet you Ak!"
    
    @pytest.mark.asyncio
    async def test_chat_timeout(self, gpt_service):
        """Test timeout handling"""
        with patch('httpx.AsyncClient') as mock_client:
            import httpx
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await gpt_service.chat([], "Hello")
            
            assert "taking a bit long" in result.lower()
