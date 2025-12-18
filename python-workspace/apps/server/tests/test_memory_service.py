import pytest
from unittest.mock import MagicMock, patch
from blog_agent.services.memory import MemoryService
from blog_agent.storage.models import ConversationMessage

@pytest.mark.asyncio
async def test_extract_facts_empty():
    service = MemoryService()
    facts = await service.extract_facts([])
    assert facts == ""

@pytest.mark.asyncio
@patch("blog_agent.services.memory.SummaryIndex")
@patch("blog_agent.services.memory.Document")
async def test_extract_facts_with_content(mock_doc, mock_index):
    # Setup mocks
    mock_query_engine = MagicMock()
    mock_query_engine.aquery.return_value = "Extracted facts summary"
    
    mock_index_instance = MagicMock()
    mock_index_instance.as_query_engine.return_value = mock_query_engine
    mock_index.from_documents.return_value = mock_index_instance
    
    service = MemoryService()
    messages = [
        ConversationMessage(role="user", content="Hello, tell me about Python."),
        ConversationMessage(role="assistant", content="Python is a programming language."),
    ]
    
    facts = await service.extract_facts(messages, max_characters=100)
    
    assert facts == "Extracted facts summary"
    mock_index.from_documents.assert_called_once()
    mock_query_engine.aquery.assert_called_once()

@pytest.mark.asyncio
async def test_extract_facts_fallback_on_error():
    # Test fallback to truncation when LlamaIndex fails
    with patch("blog_agent.services.memory.SummaryIndex.from_documents", side_effect=Exception("LLM error")):
        service = MemoryService()
        messages = [
            ConversationMessage(role="user", content="Some very long content that should be truncated"),
        ]
        
        facts = await service.extract_facts(messages, max_characters=10)
        assert facts == "User: Some" # Role + content truncated

