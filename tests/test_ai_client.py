"""Unit tests for the AIClient implementations."""

import json
from unittest.mock import patch, MagicMock

import pytest
from openai import OpenAIError

from src.ai_file_classifier.ai_client import OpenAIClient, LangChainClient, create_ai_client
from src.ai_file_classifier.models import Analysis


@patch("src.config.logging_config.os.getenv")
@patch("src.ai_file_classifier.ai_client.os.getenv")
def test_openai_client_init_no_api_key(mock_ai_getenv, mock_logging_getenv):
    """
    Test that OpenAIClient raises a ValueError when the OPENAI_API_KEY environment variable is not set.
    """
    def ai_side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return None
        return default

    def logging_side_effect(key, default=None):
        if key == "DEBUG_MODE":
            return "false"
        return default

    mock_ai_getenv.side_effect = ai_side_effect
    mock_logging_getenv.side_effect = logging_side_effect
    mock_logging_getenv.side_effect = logging_side_effect
    with pytest.raises(ValueError) as excinfo:
        OpenAIClient()
    assert "OPENAI_API_KEY must be provided." in str(excinfo.value)


@patch("src.config.logging_config.os.getenv")
@patch("src.ai_file_classifier.ai_client.os.getenv")
def test_openai_client_init_success(mock_ai_getenv, mock_logging_getenv):
    """
    Test that OpenAIClient initializes successfully when the OPENAI_API_KEY environment variable is set.
    """
    def ai_side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return "test_api_key"
        return default

    def logging_side_effect(key, default=None):
        if key == "DEBUG_MODE":
            return "false"
        return default

    mock_ai_getenv.side_effect = ai_side_effect
    mock_logging_getenv.side_effect = logging_side_effect
    client = OpenAIClient(api_key="test_api_key")
    assert client is not None


@patch("openai.resources.chat.Completions.create")
def test_analyze_content_success(mock_create):
    """
    Test that analyze_content successfully returns an Analysis object with correct data.
    """
    mock_response = MagicMock()
    # Create a mock message with a 'function_call' attribute that has 'arguments' as a JSON string
    mock_function_call = MagicMock()
    mock_function_call.arguments = json.dumps({
        "category": "Document",
        "vendor": "OpenAI",
        "description": "An analysis of the document content.",
        "date": "2023-10-01"
    })
    mock_message = MagicMock()
    mock_message.function_call = mock_function_call

    # Assign the mock message to choices
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_create.return_value = mock_response

    client = OpenAIClient(api_key="test_api_key")
    analysis = client.analyze_content("system prompt", "user prompt", "model-name")
    mock_create.assert_called_once()
    assert analysis.category == "Document"
    assert analysis.vendor == "OpenAI"
    assert analysis.description == "An analysis of the document content."
    assert analysis.date == "2023-10-01"


@patch("openai.resources.chat.Completions.create", side_effect=OpenAIError("API Error"))
def test_analyze_content_exception(_mock_create):
    """Test that analyze_content raises RuntimeError when OpenAI API fails."""
    client = OpenAIClient()
    with pytest.raises(RuntimeError) as excinfo:
        client.analyze_content("system prompt", "user prompt", "model-name")
    assert "Error communicating with OpenAI API." in str(excinfo.value)


# LangChainClient Tests

@patch("src.ai_file_classifier.ai_client.os.getenv")
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


@patch("src.ai_file_classifier.ai_client.os.getenv")
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


@patch("src.ai_file_classifier.ai_client.os.getenv")
def test_langchain_client_unsupported_provider(mock_getenv):
    """Test that LangChainClient raises ValueError for unsupported providers."""
    mock_getenv.return_value = None
    with pytest.raises(ValueError) as excinfo:
        LangChainClient(provider="unsupported_provider")
    assert "Unsupported provider" in str(excinfo.value)


@patch("src.ai_file_classifier.ai_client.os.getenv")
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
        date="2023-10-01"
    )

    with patch("src.ai_file_classifier.ai_client.ChatOpenAI") as mock_chat_openai:
        mock_llm_instance = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = mock_analysis
        mock_llm_instance.with_structured_output.return_value = mock_structured_llm
        mock_chat_openai.return_value = mock_llm_instance

        client = LangChainClient(provider="openai")
        result = client.analyze_content("system prompt", "user prompt", "gpt-4o-mini")

        assert result.category == "Document"
        assert result.vendor == "TestVendor"
        assert result.description == "Test description"
        assert result.date == "2023-10-01"
        mock_structured_llm.invoke.assert_called_once()


# Factory Function Tests

@patch("src.ai_file_classifier.ai_client.os.getenv")
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

    with patch("src.ai_file_classifier.ai_client.ChatOpenAI"):
        client = create_ai_client()
        assert isinstance(client, LangChainClient)


@patch("src.ai_file_classifier.ai_client.os.getenv")
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

    with patch("src.ai_file_classifier.ai_client.ChatOllama"):
        client = create_ai_client(provider="ollama")
        assert isinstance(client, LangChainClient)
        assert client.provider == "ollama"


@patch("src.ai_file_classifier.ai_client.os.getenv")
def test_create_ai_client_legacy_openai(mock_getenv):
    """Test that create_ai_client can create legacy OpenAIClient when requested."""
    def side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return "test_api_key"
        return default

    mock_getenv.side_effect = side_effect

    client = create_ai_client(use_langchain=False)
    assert isinstance(client, OpenAIClient)
