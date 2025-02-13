"""Configuration for pytest fixtures used across all test modules."""

import pytest

@pytest.fixture(autouse=True)
def mock_openai_api_key(monkeypatch):
    """Mock the OPENAI_API_KEY environment variable for all tests."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
