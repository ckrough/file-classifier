"""Unit tests for AI client factory functions."""

from unittest.mock import patch

import pytest

from src.ai.factory import create_ai_client
from src.ai.client import LangChainClient


@pytest.mark.unit
def test_create_ai_client_invalid_provider():
    """Test that factory rejects providers not in allowlist."""
    invalid_providers = [
        "invalid_provider",
        "anthropic",  # Not yet supported
        "google",  # Not yet supported
        "azure",
        "",  # Empty string
    ]
    for provider in invalid_providers:
        with pytest.raises(ValueError) as exc:
            create_ai_client(provider=provider)
        assert "Invalid AI_PROVIDER" in str(exc.value)
        assert "openai" in str(exc.value).lower()  # Should show allowed providers
        assert "ollama" in str(exc.value).lower()


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_create_ai_client_case_insensitive_provider(mock_getenv):
    """Test that factory handles uppercase provider names correctly."""

    def side_effect(key, default=None):
        if key == "OPENAI_API_KEY":
            return "sk-test_api_key_1234567890"
        if key == "AI_MODEL":
            return "gpt-4o-mini"
        return default

    mock_getenv.side_effect = side_effect

    # Test uppercase variations
    providers_to_test = ["OPENAI", "OpenAI", "openai"]

    with patch("src.ai.client.ChatOpenAI"):
        for provider in providers_to_test:
            client = create_ai_client(provider=provider)
            assert isinstance(client, LangChainClient)
            assert client.provider == "openai"  # Should be normalized to lowercase


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_create_ai_client_env_var_fallback(mock_getenv):
    """Test that factory falls back to AI_PROVIDER environment variable."""

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
        # Call without provider parameter - should use env var
        client = create_ai_client()
        assert isinstance(client, LangChainClient)
        assert client.provider == "openai"


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_create_ai_client_openai_defaults(mock_getenv):
    """Test that factory uses correct OpenAI defaults when env vars not set."""

    def side_effect(key, default=None):
        if key == "AI_PROVIDER":
            return "openai"
        if key == "OPENAI_API_KEY":
            return "sk-test_api_key_1234567890"
        # For AI_MODEL, return the default value provided
        return default

    mock_getenv.side_effect = side_effect

    with patch("src.ai.client.ChatOpenAI") as mock_openai:
        client = create_ai_client()
        assert isinstance(client, LangChainClient)
        # Verify ChatOpenAI was called with default model
        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-mini"  # Default from os.getenv


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_create_ai_client_ollama_defaults(mock_getenv):
    """Test that factory uses correct Ollama defaults when env vars not set."""

    def side_effect(key, default=None):
        if key == "AI_PROVIDER":
            return "ollama"
        # For OLLAMA_BASE_URL and OLLAMA_MODEL, return the default value provided
        return default

    mock_getenv.side_effect = side_effect

    with patch("src.ai.client.ChatOllama") as mock_ollama:
        client = create_ai_client(provider="ollama")
        assert isinstance(client, LangChainClient)
        # Verify ChatOllama was called with defaults
        mock_ollama.assert_called_once()
        call_kwargs = mock_ollama.call_args.kwargs
        assert call_kwargs["base_url"] == "http://localhost:11434"  # Default
        assert call_kwargs["model"] == "deepseek-r1:latest"  # Default


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_create_ai_client_explicit_provider_overrides_env(mock_getenv):
    """Test that explicit provider parameter overrides AI_PROVIDER env var."""

    def side_effect(key, default=None):
        if key == "AI_PROVIDER":
            return "openai"  # Should be ignored when provider is passed explicitly
        if key == "OLLAMA_BASE_URL":
            return default
        if key == "OLLAMA_MODEL":
            return default
        return default

    mock_getenv.side_effect = side_effect

    with patch("src.ai.client.ChatOllama") as mock_ollama:
        client = create_ai_client(provider="ollama")
        assert isinstance(client, LangChainClient)
        assert client.provider == "ollama"
        mock_ollama.assert_called_once()


@pytest.mark.unit
@patch("src.ai.client.os.getenv")
def test_create_ai_client_explicit_model_overrides_env(mock_getenv):
    """Test that explicit model parameter overrides AI_MODEL env var."""

    def side_effect(key, default=None):
        if key == "AI_PROVIDER":
            return "openai"
        if key == "OPENAI_API_KEY":
            return "sk-test_api_key_1234567890"
        if key == "AI_MODEL":
            return "gpt-3.5-turbo"  # Should be ignored when model is passed explicitly
        return default

    mock_getenv.side_effect = side_effect

    with patch("src.ai.client.ChatOpenAI") as mock_openai:
        client = create_ai_client(provider="openai", model="gpt-4o")
        assert isinstance(client, LangChainClient)
        mock_openai.assert_called_once()
        call_kwargs = mock_openai.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o"  # Explicit model should win over env
