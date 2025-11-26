"""Unit tests for the AIClient implementations."""

from unittest.mock import patch, MagicMock

import pytest
from pydantic import ValidationError
from langchain_core.exceptions import OutputParserException

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
            return "sk-test_api_key_1234567890"
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
    assert "Unsupported AI provider" in str(excinfo.value)


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_analyze_content(mock_getenv):
    """Test that LangChainClient.analyze_content returns structured Analysis object."""

    def side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return "sk-test_api_key_1234567890"
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


# Validation Tests - API Key


@pytest.mark.unit
def test_langchain_client_invalid_api_key_format():
    """Test that LangChainClient rejects API keys not starting with 'sk-'."""
    with pytest.raises(ValueError) as exc:
        LangChainClient(provider="openai", api_key="invalid-key-format")
    assert "OPENAI_API_KEY must start with 'sk-'" in str(exc.value)
    assert "Verify your API key is correct" in str(exc.value)


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_missing_api_key(mock_getenv):
    """Test that LangChainClient raises clear error when OPENAI_API_KEY is missing."""
    mock_getenv.return_value = None
    with pytest.raises(ValueError) as exc:
        LangChainClient(provider="openai")
    assert "OPENAI_API_KEY is required" in str(exc.value)
    assert "environment variable" in str(exc.value).lower()


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_valid_api_key_format(mock_getenv):
    """Test that LangChainClient accepts properly formatted API keys."""

    def side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return "sk-test_valid_key_12345"
        if key == "AI_MODEL":
            return "gpt-4o-mini"
        return default

    mock_getenv.side_effect = side_effect

    with patch("src.ai.client.ChatOpenAI"):
        client = LangChainClient(provider="openai")
        assert client is not None
        assert client.provider == "openai"


# Validation Tests - Ollama URL


@pytest.mark.unit
def test_langchain_client_invalid_ollama_url():
    """Test that LangChainClient rejects non-http/https Ollama URLs."""
    invalid_urls = [
        "file:///etc/passwd",
        "ftp://localhost:11434",
        "javascript:alert(1)",
        "localhost:11434",  # Missing protocol
    ]
    for url in invalid_urls:
        with pytest.raises(ValueError) as exc:
            LangChainClient(provider="ollama", base_url=url, model="test:latest")
        assert "must start with http://" in str(exc.value)
        assert "OLLAMA_BASE_URL" in str(exc.value)


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_valid_ollama_urls(mock_getenv):
    """Test that LangChainClient accepts both http:// and https:// URLs."""
    mock_getenv.return_value = None

    valid_urls = [
        "http://localhost:11434",
        "https://localhost:11434",
        "http://192.168.1.100:11434",
        "https://ollama.example.com",
    ]

    with patch("src.ai.client.ChatOllama"):
        for url in valid_urls:
            client = LangChainClient(
                provider="ollama", base_url=url, model="test:latest"
            )
            assert client is not None
            assert client.provider == "ollama"


# Factory Function Tests


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_create_ai_client_default_openai(mock_getenv):
    """Test that create_ai_client defaults to OpenAI with LangChain."""

    def side_effect(key, default=None):
        if key == "AI_PROVIDER":
            return "openai"
        if key == "OPENAI_API_KEY":
            return "sk-test_api_key_1234567890"
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


# Error Injection Tests


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_handles_connection_error(mock_getenv):
    """Test that connection errors are handled gracefully."""

    def side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return "sk-test_api_key_1234567890"
        if key == "AI_MODEL":
            return "gpt-4o-mini"
        return default

    mock_getenv.side_effect = side_effect

    with patch("src.ai.client.ChatOpenAI") as mock_chat_openai:
        from langchain_core.prompts import ChatPromptTemplate

        mock_llm_instance = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.side_effect = ConnectionError("Network error")
        mock_llm_instance.with_structured_output.return_value = mock_structured_llm
        mock_chat_openai.return_value = mock_llm_instance

        mock_prompt = ChatPromptTemplate.from_messages(
            [("system", "system prompt"), ("human", "user prompt")]
        )

        client = LangChainClient(provider="openai")

        with pytest.raises(RuntimeError) as exc:
            client.analyze_content(mock_prompt, {})

        assert "Network error" in str(exc.value)
        assert "internet connection" in str(exc.value).lower()


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_handles_validation_error(mock_getenv):
    """Test that Pydantic validation errors are handled."""

    def side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return "sk-test_api_key_1234567890"
        if key == "AI_MODEL":
            return "gpt-4o-mini"
        return default

    mock_getenv.side_effect = side_effect

    with patch("src.ai.client.ChatOpenAI") as mock_chat_openai:
        from langchain_core.prompts import ChatPromptTemplate

        mock_llm_instance = MagicMock()
        mock_structured_llm = MagicMock()

        # Create a validation error
        try:
            Analysis(
                category=123,  # Invalid type
                vendor="TestVendor",
                description="Test",
                date="2023-10-01",
            )
        except ValidationError as ve:
            mock_structured_llm.invoke.side_effect = ve

        mock_llm_instance.with_structured_output.return_value = mock_structured_llm
        mock_chat_openai.return_value = mock_llm_instance

        mock_prompt = ChatPromptTemplate.from_messages(
            [("system", "system prompt"), ("human", "user prompt")]
        )

        client = LangChainClient(provider="openai")

        with pytest.raises(RuntimeError) as exc:
            client.analyze_content(mock_prompt, {})

        assert "invalid" in str(exc.value).lower()
        assert "Analysis" in str(exc.value)


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_handles_output_parser_error(mock_getenv):
    """Test that LangChain output parser errors are handled."""

    def side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return "sk-test_api_key_1234567890"
        if key == "AI_MODEL":
            return "gpt-4o-mini"
        return default

    mock_getenv.side_effect = side_effect

    with patch("src.ai.client.ChatOpenAI") as mock_chat_openai:
        from langchain_core.prompts import ChatPromptTemplate

        mock_llm_instance = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.side_effect = OutputParserException(
            "Failed to parse output"
        )
        mock_llm_instance.with_structured_output.return_value = mock_structured_llm
        mock_chat_openai.return_value = mock_llm_instance

        mock_prompt = ChatPromptTemplate.from_messages(
            [("system", "system prompt"), ("human", "user prompt")]
        )

        client = LangChainClient(provider="openai")

        with pytest.raises(RuntimeError) as exc:
            client.analyze_content(mock_prompt, {})

        assert "parse" in str(exc.value).lower()
        assert "Analysis" in str(exc.value)


# Schema Caching Tests


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_pre_caches_common_schemas(mock_getenv):
    """Test that client pre-caches commonly used schemas at initialization."""
    from src.analysis.models import (
        RawMetadata,
        NormalizedMetadata,
    )

    def side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return "sk-test_api_key_1234567890"
        if key == "AI_MODEL":
            return "gpt-4o-mini"
        return default

    mock_getenv.side_effect = side_effect

    with patch("src.ai.client.ChatOpenAI") as mock_chat_openai:
        mock_llm_instance = MagicMock()
        mock_chat_openai.return_value = mock_llm_instance

        client = LangChainClient(provider="openai")

        # Verify that with_structured_output was called for each pre-cached
        # schema. Expected: Analysis + 2 multi-agent schemas
        # (RawMetadata, NormalizedMetadata) = 3 calls
        # Note: PathMetadata is now a simple dataclass, not Pydantic
        # ResolvedMetadata removed - conflict resolution agent eliminated
        assert mock_llm_instance.with_structured_output.call_count == 3

        # Verify schema cache is populated
        assert len(client._schema_cache) == 3
        assert Analysis in client._schema_cache
        assert RawMetadata in client._schema_cache
        assert NormalizedMetadata in client._schema_cache


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_lazy_caches_new_schemas(mock_getenv):
    """Test that client lazily caches schemas not pre-cached."""
    from pydantic import BaseModel

    # Define a custom schema not in pre-cache
    class CustomSchema(BaseModel):
        """Custom test schema."""

        field1: str
        field2: int

    def side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return "sk-test_api_key_1234567890"
        if key == "AI_MODEL":
            return "gpt-4o-mini"
        return default

    mock_getenv.side_effect = side_effect

    with patch("src.ai.client.ChatOpenAI") as mock_chat_openai:
        from langchain_core.prompts import ChatPromptTemplate

        mock_llm_instance = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = CustomSchema(field1="test", field2=42)
        mock_llm_instance.with_structured_output.return_value = mock_structured_llm
        mock_chat_openai.return_value = mock_llm_instance

        client = LangChainClient(provider="openai")

        # Reset call count after initialization
        mock_llm_instance.with_structured_output.reset_mock()

        # Use custom schema - should trigger lazy caching
        mock_prompt = ChatPromptTemplate.from_messages(
            [("system", "system"), ("human", "user")]
        )
        result = client.analyze_content(mock_prompt, {}, schema=CustomSchema)

        # Verify schema was cached (1 call for new schema)
        assert mock_llm_instance.with_structured_output.call_count == 1
        assert CustomSchema in client._schema_cache
        assert isinstance(result, CustomSchema)


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_reuses_cached_schemas(mock_getenv):
    """Test that client reuses cached schemas instead of recreating them."""

    def side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return "sk-test_api_key_1234567890"
        if key == "AI_MODEL":
            return "gpt-4o-mini"
        return default

    mock_getenv.side_effect = side_effect

    with patch("src.ai.client.ChatOpenAI") as mock_chat_openai:
        from langchain_core.prompts import ChatPromptTemplate

        mock_llm_instance = MagicMock()
        mock_structured_llm = MagicMock()
        mock_structured_llm.invoke.return_value = Analysis(
            category="Test", vendor="Test", description="Test", date="2023-01-01"
        )
        mock_llm_instance.with_structured_output.return_value = mock_structured_llm
        mock_chat_openai.return_value = mock_llm_instance

        client = LangChainClient(provider="openai")

        # Reset mock to ignore pre-caching calls
        mock_llm_instance.with_structured_output.reset_mock()

        # Call analyze_content multiple times with default Analysis schema
        mock_prompt = ChatPromptTemplate.from_messages(
            [("system", "system"), ("human", "user")]
        )

        for _ in range(3):
            client.analyze_content(mock_prompt, {})

        # Verify with_structured_output was NOT called again (cache hit)
        assert mock_llm_instance.with_structured_output.call_count == 0


# Configuration Validation Tests


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_warns_unknown_openai_model(mock_getenv, caplog):
    """Test that client logs warning for unrecognized OpenAI models."""
    import logging

    def side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return "sk-test_api_key_1234567890"
        if key == "AI_MODEL":
            return "gpt-5-ultra"  # Non-existent model
        return default

    mock_getenv.side_effect = side_effect

    with patch("src.ai.client.ChatOpenAI"):
        with caplog.at_level(logging.WARNING):
            client = LangChainClient(provider="openai")
            assert client is not None

            # Verify warning was logged
            assert any(
                "Unrecognized OpenAI model" in record.message
                for record in caplog.records
            )
            assert any("gpt-5-ultra" in record.message for record in caplog.records)


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_warns_invalid_ollama_model_format(mock_getenv, caplog):
    """Test that client logs warning for invalid Ollama model format."""
    import logging

    def side_effect(key, default=None):
        if key == "OLLAMA_BASE_URL":
            return "http://localhost:11434"
        if key == "OLLAMA_MODEL":
            return "invalid-model-format"  # Missing :tag
        return default

    mock_getenv.side_effect = side_effect

    with patch("src.ai.client.ChatOllama"):
        with caplog.at_level(logging.WARNING):
            client = LangChainClient(provider="ollama", model="invalid-model-format")
            assert client is not None

            # Verify warning was logged
            assert any(
                "Invalid Ollama model format" in record.message
                for record in caplog.records
            )
            assert any(
                "invalid-model-format" in record.message for record in caplog.records
            )


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_langchain_client_accepts_valid_ollama_model_formats(mock_getenv, caplog):
    """Test that client accepts valid Ollama model formats including dots."""
    import logging

    def side_effect(key, default=None):
        if key == "OLLAMA_BASE_URL":
            return "http://localhost:11434"
        return default

    mock_getenv.side_effect = side_effect

    # Test various valid Ollama model formats
    valid_models = [
        "llama3.2:latest",  # With dot in name
        "qwen2.5:7b",  # With dot and version tag
        "deepseek-r1:latest",  # With dash
        "llama2:13b-chat",  # With dash in tag
        "mistral:7b-instruct-v0.2",  # Complex tag with dots and dashes
    ]

    with patch("src.ai.client.ChatOllama"):
        for model in valid_models:
            caplog.clear()
            with caplog.at_level(logging.WARNING):
                client = LangChainClient(provider="ollama", model=model)
                assert client is not None

                # Verify NO warning was logged for valid model format
                assert not any(
                    "Invalid Ollama model format" in record.message
                    for record in caplog.records
                ), f"Model {model} should be valid but triggered a warning"
