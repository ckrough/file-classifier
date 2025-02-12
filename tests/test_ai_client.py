import pytest
from unittest.mock import patch, MagicMock
from src.ai_file_classifier.ai_client import OpenAIClient
from src.ai_file_classifier.models import Analysis


@patch("os.getenv")
def test_openai_client_init_no_api_key(mock_getenv):
    """
    Test that OpenAIClient raises a ValueError when the OPENAI_API_KEY environment variable is not set.
    """
    mock_getenv.return_value = None
    with pytest.raises(ValueError) as excinfo:
        OpenAIClient()
    assert "OPENAI_API_KEY environment variable not set." in str(excinfo.value)


@patch("os.getenv")
def test_openai_client_init_success(mock_getenv):
    """
    Test that OpenAIClient initializes successfully when the OPENAI_API_KEY environment variable is set.
    """
    mock_getenv.return_value = "test_api_key"
    client = OpenAIClient()
    assert client is not None


@patch("openai.beta.chat.completions.parse")
def test_analyze_content_success(mock_parse):
    """
    Test that analyze_content successfully returns an Analysis object with correct data.
    """
    mock_response = MagicMock()
    mock_analysis = Analysis(
        category="Document",
        vendor="OpenAI",
        description="An analysis of the document content.",
        date="2023-10-01"  # Optional: Include if necessary
    )
    mock_response.choices = [MagicMock(message=MagicMock(parsed=mock_analysis))]
    mock_parse.return_value = mock_response

    client = OpenAIClient()
    analysis = client.analyze_content("system prompt", "user prompt", "model-name")
    mock_parse.assert_called_once()
    assert analysis == mock_analysis


@patch("openai.beta.chat.completions.parse", side_effect=Exception("API Error"))
def test_analyze_content_exception(_mock_parse):
    client = OpenAIClient()
    with pytest.raises(RuntimeError) as excinfo:
        client.analyze_content("system prompt", "user prompt", "model-name")
    assert "Error communicating with OpenAI API: API Error" in str(excinfo.value)
