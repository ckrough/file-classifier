"""Unit tests for the AIClient implementations."""

from unittest.mock import patch, MagicMock

import pytest

from src.ai.client import LangChainClient
from src.ai.factory import create_ai_client
from src.analysis.models import Analysis


# LangChainClient Tests


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_init_openai(mock_getenv):
    """Test that LangChainClient initializes successfully with OpenAI provider."""

    def side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return "test_api_key"
        if key == "AI_MODEL":
            return "gpt-4o-mini"
        return default

    mock_getenv.side_effect = side_effect
    client = LangChainClient(provider="openai")
    assert client is not None
    assert client.provider == "openai"


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_init_ollama(mock_getenv):
    """Test that LangChainClient initializes successfully with Ollama provider."""

    def side_effect(key, default=None):
        if key == "OLLAMA_BASE_URL":
            return "http://localhost:11434"
        if key == "OLLAMA_MODEL":
            return "deepseek-r1:latest"
        return default

    mock_getenv.side_effect = side_effect
    client = LangChainClient(provider="ollama")
    assert client is not None
    assert client.provider == "ollama"


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_unsupported_provider(mock_getenv):
    """Test that LangChainClient raises ValueError for unsupported providers."""
    mock_getenv.return_value = None
    with pytest.raises(ValueError) as excinfo:
        LangChainClient(provider="unsupported_provider")
    assert "Unsupported provider" in str(excinfo.value)


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_analyze_content(mock_getenv):
    """Test that LangChainClient.analyze_content returns structured Analysis object."""

    def side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return "test_api_key"
        if key == "AI_MODEL":
            return "gpt-4o-mini"
        return default

    mock_getenv.side_effect = side_effect

    # Create mock LLM and structured output
    mock_analysis = Analysis(
        category="Document",
        vendor="TestVendor",
        description="Test description",
        date="2023-10-01",
    )

    with patch("src.ai.client.ChatOpenAI") as mock_chat_openai:
        from langchain_core.prompts import ChatPromptTemplate

        mock_llm_instance = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = mock_analysis
        mock_llm_instance.with_structured_output.return_value = mock_structured_llm
        mock_chat_openai.return_value = mock_llm_instance

        # Create a mock prompt template
        mock_prompt = ChatPromptTemplate.from_messages(
            [("system", "system prompt"), ("human", "user prompt")]
        )

        client = LangChainClient(provider="openai")
        result = client.analyze_content(mock_prompt, {})

        assert result.category == "Document"
        assert result.vendor == "TestVendor"
        assert result.description == "Test description"
        assert result.date == "2023-10-01"
        mock_structured_llm.invoke.assert_called_once()


# Factory Function Tests


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_create_ai_client_default_openai(mock_getenv):
    """Test that create_ai_client defaults to OpenAI with LangChain."""

    def side_effect(key, default=None):
        if key == "AI_PROVIDER":
            return "openai"
        if key == "OPENAI_API_KEY":
            return "test_api_key"
        if key == "AI_MODEL":
            return "gpt-4o-mini"
        return default

    mock_getenv.side_effect = side_effect

    with patch("src.ai.client.ChatOpenAI"):
        client = create_ai_client()
        assert isinstance(client, LangChainClient)


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_create_ai_client_ollama(mock_getenv):
    """Test that create_ai_client creates Ollama client when specified."""

    def side_effect(key, default=None):
        if key == "AI_PROVIDER":
            return "ollama"
        if key == "OLLAMA_BASE_URL":
            return "http://localhost:11434"
        if key == "OLLAMA_MODEL":
            return "deepseek-r1:latest"
        return default

    mock_getenv.side_effect = side_effect

    with patch("src.ai.client.ChatOllama"):
        client = create_ai_client(provider="ollama")
        assert isinstance(client, LangChainClient)
        assert client.provider == "ollama"
