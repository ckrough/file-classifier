"""Unit tests for the ai_file_classifier.file_analyzer module."""

from unittest.mock import patch, Mock, MagicMock
import pytest
from langchain_core.prompts import ChatPromptTemplate
from src.ai_file_classifier.file_analyzer import (
    standardize_analysis,
    generate_filename,
    analyze_file_content
)
from src.ai_file_classifier.models import Analysis


def test_standardize_analysis():
    """Test that standardize_analysis correctly standardizes the Analysis object."""
    original_analysis = Analysis(
        category="Financial Report",
        vendor="Acme Corp",
        description="Annual Financial Overview",
        date="2023-10-01"
    )
    standardized = standardize_analysis(original_analysis)
    assert standardized.category == "financial-report"
    assert standardized.vendor == "acme-corp"
    assert standardized.description == "annual-financial-overview"
    assert standardized.date == "2023-10-01"


def test_generate_filename():
    """Test that generate_filename creates the correct filename based on Analysis data."""
    analysis = Analysis(
        category="financial-report",
        vendor="acme-corp",
        description="annual-financial-overview",
        date="2023-10-01"
    )
    filename = generate_filename(analysis)
    assert filename == "acme-corp-financial-report-annual-financial-overview-2023-10-01"


@patch('src.ai_file_classifier.file_analyzer.extract_text_from_txt')
@patch('src.ai_file_classifier.file_analyzer.get_file_analysis_prompt')
def test_analyze_file_content_txt(mock_get_prompt, mock_extract_txt):
    """Test analyze_file_content with a .txt file to ensure proper analysis and filename generation."""
    # Setup mocks for the .txt file
    mock_extract_txt.return_value = "Sample text content."

    # Mock the prompt template
    mock_prompt = MagicMock(spec=ChatPromptTemplate)
    mock_get_prompt.return_value = mock_prompt

    mock_ai_client = Mock()
    mock_ai_client.analyze_content.return_value = Analysis(
        category="documentation",
        vendor="openai",
        description="user-guide",
        date="2023-10-01"
    )

    # Test with a .txt file
    suggested_name, category, vendor, description, date = analyze_file_content(
        file_path="docs/user_guide.txt",
        client=mock_ai_client
    )

    assert suggested_name == "openai-documentation-user-guide-2023-10-01"
    assert category == "documentation"
    assert vendor == "openai"
    assert description == "user-guide"
    assert date == "2023-10-01"

    mock_extract_txt.assert_called_once_with("docs/user_guide.txt")
    mock_get_prompt.assert_called_once()

    # Verify analyze_content was called with prompt template and values
    mock_ai_client.analyze_content.assert_called_once()
    call_args = mock_ai_client.analyze_content.call_args
    assert call_args[1]['prompt_template'] == mock_prompt
    assert call_args[1]['prompt_values']['filename'] == "user_guide.txt"
    assert call_args[1]['prompt_values']['content'] == "Sample text content."


@patch('src.ai_file_classifier.file_analyzer.extract_text_from_pdf')
@patch('src.ai_file_classifier.file_analyzer.get_file_analysis_prompt')
def test_analyze_file_content_pdf(
    mock_get_prompt,
    mock_extract_pdf
):
    """Test analyze_file_content with a .pdf file to ensure proper analysis and filename generation."""
    # Setup mocks for the .pdf file
    mock_extract_pdf.return_value = "Sample PDF content."

    # Mock the prompt template
    mock_prompt = MagicMock(spec=ChatPromptTemplate)
    mock_get_prompt.return_value = mock_prompt

    mock_ai_client = Mock()
    mock_ai_client.analyze_content.return_value = Analysis(
        category="documentation",
        vendor="openai",
        description="annual-report",
        date="2023-10-01"
    )

    # Test with a .pdf file
    suggested_name, category, vendor, description, date = analyze_file_content(
        file_path="docs/report.pdf",
        client=mock_ai_client
    )

    assert suggested_name == "openai-documentation-annual-report-2023-10-01"
    assert category == "documentation"
    assert vendor == "openai"
    assert description == "annual-report"
    assert date == "2023-10-01"

    mock_extract_pdf.assert_called_once_with("docs/report.pdf")
    mock_get_prompt.assert_called_once()

    # Verify analyze_content was called with prompt template and values
    mock_ai_client.analyze_content.assert_called_once()
    call_args = mock_ai_client.analyze_content.call_args
    assert call_args[1]['prompt_template'] == mock_prompt
    assert call_args[1]['prompt_values']['filename'] == "report.pdf"
    assert call_args[1]['prompt_values']['content'] == "Sample PDF content."


@patch('src.ai_file_classifier.file_analyzer.extract_text_from_txt')
def test_analyze_file_content_extraction_failure(mock_extract_txt):
    """Test that analyze_file_content raises a RuntimeError when text extraction fails."""
    mock_extract_txt.return_value = None
    mock_ai_client = Mock()
    with pytest.raises(RuntimeError) as exc_info:
        analyze_file_content(
            file_path="docs/invalid.txt",
            client=mock_ai_client
        )
    assert "Error analyzing file content" in str(exc_info.value)
    mock_extract_txt.assert_called_once_with("docs/invalid.txt")
