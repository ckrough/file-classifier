"""Shared test fixtures for AI module tests."""

import pytest


@pytest.fixture
def mock_openai_api_key():
    """Return a valid mock OpenAI API key for testing."""
    return "sk-test_api_key_1234567890"


@pytest.fixture
def mock_openai_env(monkeypatch, mock_openai_api_key):
    """Mock OpenAI environment variables."""
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", mock_openai_api_key)
    monkeypatch.setenv("AI_MODEL", "gpt-4o-mini")
    return {
        "provider": "openai",
        "api_key": mock_openai_api_key,
        "model": "gpt-4o-mini",
    }


@pytest.fixture
def mock_ollama_env(monkeypatch):
    """Mock Ollama environment variables."""
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "deepseek-r1:latest")
    return {
        "provider": "ollama",
        "base_url": "http://localhost:11434",
        "model": "deepseek-r1:latest",
    }
