"""Unit tests for the multi-agent file analyzer module."""

from unittest.mock import patch, Mock
import pytest
from src.analysis.analyzer import analyze_file_content
from src.analysis.models import ResolvedMetadata


@pytest.mark.unit
@patch("src.analysis.analyzer.extract_text_from_txt")
@patch("src.analysis.analyzer.process_document_multi_agent")
def test_analyze_file_content_txt(mock_multi_agent, mock_extract_txt):
    """Test analyze_file_content with a .txt file using multi-agent pipeline."""
    # Setup mocks for the .txt file
    mock_extract_txt.return_value = "Sample text content."

    # Mock the multi-agent pipeline response
    mock_multi_agent.return_value = ResolvedMetadata(
        final_path="financial/banking/acme/statement-acme-checking-20231001.txt",
        alternative_paths=None,
        resolution_notes=None,
    )

    mock_ai_client = Mock()

    # Test with a .txt file
    result = analyze_file_content(
        file_path="docs/user_guide.txt", client=mock_ai_client
    )

    assert result["suggested_name"] == "statement-acme-checking-20231001.txt"
    assert result["category"] == "statement"
    assert result["vendor"] == "acme"
    assert result["description"] == "checking"
    assert result["date"] == "20231001"
    assert (
        result["destination_relative_path"]
        == "financial/banking/acme/statement-acme-checking-20231001.txt"
    )

    mock_extract_txt.assert_called_once_with("docs/user_guide.txt")
    mock_multi_agent.assert_called_once_with(
        "Sample text content.", "user_guide.txt", mock_ai_client
    )


@pytest.mark.unit
@patch("src.analysis.analyzer.extract_text_from_pdf")
@patch("src.analysis.analyzer.process_document_multi_agent")
def test_analyze_file_content_pdf(mock_multi_agent, mock_extract_pdf):
    """Test analyze_file_content with a .pdf file using multi-agent pipeline."""
    # Setup mocks for the .pdf file
    mock_extract_pdf.return_value = "Sample PDF content."

    # Mock the multi-agent pipeline response
    mock_multi_agent.return_value = ResolvedMetadata(
        final_path="financial/banking/chase/statement-chase-savings-20230115.pdf",
        alternative_paths=None,
        resolution_notes=None,
    )

    mock_ai_client = Mock()

    # Test with a .pdf file
    result = analyze_file_content(file_path="docs/report.pdf", client=mock_ai_client)

    assert result["suggested_name"] == "statement-chase-savings-20230115.pdf"
    assert result["category"] == "statement"
    assert result["vendor"] == "chase"
    assert result["description"] == "savings"
    assert result["date"] == "20230115"
    assert (
        result["destination_relative_path"]
        == "financial/banking/chase/statement-chase-savings-20230115.pdf"
    )

    mock_extract_pdf.assert_called_once_with("docs/report.pdf")
    mock_multi_agent.assert_called_once_with(
        "Sample PDF content.", "report.pdf", mock_ai_client
    )


@pytest.mark.unit
@patch("src.analysis.analyzer.extract_text_from_txt")
def test_analyze_file_content_extraction_failure(mock_extract_txt):
    """Test that analyze_file_content raises RuntimeError on extraction failure."""
    mock_extract_txt.return_value = None
    mock_ai_client = Mock()
    with pytest.raises(RuntimeError) as exc_info:
        analyze_file_content(file_path="docs/invalid.txt", client=mock_ai_client)
    assert "Failed to extract content" in str(exc_info.value)
    mock_extract_txt.assert_called_once_with("docs/invalid.txt")


@pytest.mark.unit
@patch("src.analysis.analyzer.extract_text_from_pdf")
@patch("src.analysis.analyzer.process_document_multi_agent")
def test_analyze_file_content_complex_filename(mock_multi_agent, mock_extract_pdf):
    """Test parsing of complex multi-part filenames."""
    mock_extract_pdf.return_value = "Invoice content"

    # Mock response with complex filename (multi-word description)
    mock_multi_agent.return_value = ResolvedMetadata(
        final_path="financial/banking/bofa/invoice-bofa-wire-transfer-fee-20240315.pdf",
        alternative_paths=None,
        resolution_notes=None,
    )

    mock_ai_client = Mock()

    result = analyze_file_content(file_path="test.pdf", client=mock_ai_client)

    assert result["suggested_name"] == "invoice-bofa-wire-transfer-fee-20240315.pdf"
    assert result["category"] == "invoice"
    assert result["vendor"] == "bofa"
    assert result["description"] == "wire-transfer-fee"
    assert result["date"] == "20240315"
    assert (
        result["destination_relative_path"]
        == "financial/banking/bofa/invoice-bofa-wire-transfer-fee-20240315.pdf"
    )


@pytest.mark.unit
@patch("src.analysis.analyzer.extract_text_from_pdf")
@patch("src.analysis.analyzer.process_document_multi_agent")
def test_analyze_file_content_no_date(mock_multi_agent, mock_extract_pdf):
    """Test parsing of filename without date."""
    mock_extract_pdf.return_value = "Document content"

    # Mock response without date in filename
    mock_multi_agent.return_value = ResolvedMetadata(
        final_path="legal/contracts/vendor-name/agreement-vendor-name-service.pdf",
        alternative_paths=None,
        resolution_notes=None,
    )

    mock_ai_client = Mock()

    result = analyze_file_content(file_path="test.pdf", client=mock_ai_client)

    assert result["suggested_name"] == "agreement-vendor-name-service.pdf"
    assert result["category"] == "agreement"
    assert result["vendor"] == "vendor"
    assert result["description"] == "name-service"
    assert result["date"] == ""
    assert (
        result["destination_relative_path"]
        == "legal/contracts/vendor-name/agreement-vendor-name-service.pdf"
    )
