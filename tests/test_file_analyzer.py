import pytest
from unittest.mock import Mock, patch
from src.ai_file_classifier.file_analyzer import (
    standardize_analysis,
    generate_filename,
    analyze_file_content
)
from src.ai_file_classifier.models import Analysis


def test_standardize_analysis():
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
    analysis = Analysis(
        category="financial-report",
        vendor="acme-corp",
        description="annual-financial-overview",
        date="2023-10-01"
    )
    
    filename = generate_filename(analysis)
    
    assert filename == "acme-corp-financial-report-annual-financial-overview-2023-10-01"


@patch('src.ai_file_classifier.file_analyzer.extract_text_from_txt')
@patch('src.ai_file_classifier.file_analyzer.load_and_format_prompt')
def test_analyze_file_content_txt(
    mock_load_prompt,
    mock_extract_txt
):
    # Setup mocks for the .txt file
    mock_extract_txt.return_value = "Sample text content."
    mock_load_prompt.side_effect = [
        "System prompt content.",
        "User prompt content with filename and content."
    ]
    
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
        model="gpt-3.5-turbo",
        client=mock_ai_client
    )
    
    assert suggested_name == "openai-documentation-user-guide-2023-10-01"
    assert category == "documentation"
    assert vendor == "openai"
    assert description == "user-guide"
    assert date == "2023-10-01"
    
    mock_extract_txt.assert_called_once_with("docs/user_guide.txt")
    mock_load_prompt.assert_any_call('prompts/file-analysis-system-prompt.txt')
    mock_load_prompt.assert_any_call(
        'prompts/file-analysis-user-prompt.txt',
        filename="user_guide.txt",
        content="Sample text content."
    )
    mock_ai_client.analyze_content.assert_called_once()


@patch('src.ai_file_classifier.file_analyzer.extract_text_from_pdf')
@patch('src.ai_file_classifier.file_analyzer.load_and_format_prompt')
def test_analyze_file_content_pdf(
    mock_load_prompt,
    mock_extract_pdf
):
    # Setup mocks for the .pdf file
    mock_extract_pdf.return_value = "Sample PDF content."
    mock_load_prompt.side_effect = [
        "System prompt content.",
        "User prompt content with filename and content."
    ]
    
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
        model="gpt-3.5-turbo",
        client=mock_ai_client
    )
    
    assert suggested_name == "openai-documentation-annual-report-2023-10-01"
    assert category == "documentation"
    assert vendor == "openai"
    assert description == "annual-report"
    assert date == "2023-10-01"
    
    mock_extract_pdf.assert_called_once_with("docs/report.pdf")
    mock_load_prompt.assert_any_call('prompts/file-analysis-system-prompt.txt')
    mock_load_prompt.assert_any_call(
        'prompts/file-analysis-user-prompt.txt',
        filename="report.pdf",
        content="Sample PDF content."
    )
    mock_ai_client.analyze_content.assert_called_once()


@patch('src.ai_file_classifier.file_analyzer.extract_text_from_txt')
def test_analyze_file_content_extraction_failure(mock_extract_txt):
    mock_extract_txt.return_value = None
    mock_ai_client = Mock()
    
    with pytest.raises(RuntimeError) as exc_info:
        analyze_file_content(
            file_path="docs/invalid.txt",
            model="gpt-3.5-turbo",
            client=mock_ai_client
        )
    
    assert "Error analyzing file content" in str(exc_info.value)
    mock_extract_txt.assert_called_once_with("docs/invalid.txt")
