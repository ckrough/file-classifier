"""Unit tests for the multi-agent file analyzer module."""

from unittest.mock import patch, Mock, ANY
import pytest

from src.analysis.analyzer import analyze_file_content
from src.analysis.models import RawMetadata, NormalizedMetadata
from src.files.langchain_loader import LoaderMetadata
from src.path.builder import PathMetadata


@pytest.mark.unit
@patch("src.analysis.analyzer.load_txt_text_with_langchain")
@patch("src.analysis.analyzer.process_document_multi_agent")
def test_analyze_file_content_txt(mock_multi_agent, mock_load_txt):
    """Test analyze_file_content with a .txt file using multi-agent pipeline."""
    # Setup mocks for the .txt file
    mock_loader_meta = LoaderMetadata(
        file_type="txt",
        loader="TextLoader",
        page_count=None,
        pages_sampled=[],
        char_count=len("Sample text content."),
    )
    mock_load_txt.return_value = ("Sample text content.", mock_loader_meta)

    # Mock the multi-agent pipeline response (now returns tuple)
    mock_raw = RawMetadata(
        domain="financial",
        category="banking",
        doctype="statement",
        vendor_raw="Acme Bank",
        date_raw="2023-10-01",
        subject_raw="Checking account",
        account_types=["checking"],
    )
    mock_normalized = NormalizedMetadata(
        domain="financial",
        category="banking",
        doctype="statement",
        vendor_name="acme",
        date="20231001",
        subject="checking",
    )
    mock_path = PathMetadata(
        directory_path="financial/banking/statement/",
        filename="statement-acme-checking-20231001.txt",
        full_path="financial/banking/statement/statement-acme-checking-20231001.txt",
    )
    mock_multi_agent.return_value = (mock_raw, mock_normalized, mock_path)

    mock_ai_client = Mock()

    # Test with a .txt file
    result = analyze_file_content(
        file_path="docs/user_guide.txt", client=mock_ai_client
    )

    assert result["suggested_name"] == "statement-acme-checking-20231001.txt"
    assert result["domain"] == "financial"
    assert result["category"] == "banking"
    assert result["doctype"] == "statement"
    assert result["vendor"] == "acme"
    assert result["description"] == "checking"
    assert result["date"] == "20231001"
    assert (
        result["destination_relative_path"]
        == "financial/banking/statement/statement-acme-checking-20231001.txt"
    )

    # Loader metadata should be attached
    loader_meta = result["loader_metadata"]
    assert loader_meta.file_type == "txt"
    assert loader_meta.loader == "TextLoader"

    mock_load_txt.assert_called_once_with("docs/user_guide.txt", ANY)
    mock_multi_agent.assert_called_once_with(
        "Sample text content.", "user_guide.txt", mock_ai_client
    )


@pytest.mark.unit
@patch("src.analysis.analyzer.load_pdf_text_with_langchain")
@patch("src.analysis.analyzer.process_document_multi_agent")
def test_analyze_file_content_pdf(mock_multi_agent, mock_load_pdf):
    """Test analyze_file_content with a .pdf file using multi-agent pipeline."""
    # Setup mocks for the .pdf file
    mock_loader_meta = LoaderMetadata(
        file_type="pdf",
        loader="PyPDFLoader",
        page_count=3,
        pages_sampled=[0, 1, 2],
        char_count=len("Sample PDF content."),
    )
    mock_load_pdf.return_value = ("Sample PDF content.", mock_loader_meta)

    # Mock the multi-agent pipeline response (now returns tuple)
    mock_raw = RawMetadata(
        domain="financial",
        category="banking",
        doctype="statement",
        vendor_raw="Chase Bank",
        date_raw="2023-01-15",
        subject_raw="Savings account",
        account_types=["savings"],
    )
    mock_normalized = NormalizedMetadata(
        domain="financial",
        category="banking",
        doctype="statement",
        vendor_name="chase",
        date="20230115",
        subject="savings",
    )
    mock_path = PathMetadata(
        directory_path="financial/banking/statement/",
        filename="statement-chase-savings-20230115.pdf",
        full_path=(
            "financial/banking/statement/"
            "statement-chase-savings-20230115.pdf"
        ),
    )
    mock_multi_agent.return_value = (mock_raw, mock_normalized, mock_path)

    mock_ai_client = Mock()

    # Test with a .pdf file
    result = analyze_file_content(file_path="docs/report.pdf", client=mock_ai_client)

    assert result["suggested_name"] == "statement-chase-savings-20230115.pdf"
    assert result["domain"] == "financial"
    assert result["category"] == "banking"
    assert result["doctype"] == "statement"
    assert result["vendor"] == "chase"
    assert result["description"] == "savings"
    assert result["date"] == "20230115"
    assert (
        result["destination_relative_path"]
        == "financial/banking/statement/statement-chase-savings-20230115.pdf"
    )

    loader_meta = result["loader_metadata"]
    assert loader_meta.file_type == "pdf"
    assert loader_meta.loader == "PyPDFLoader"

    mock_load_pdf.assert_called_once_with("docs/report.pdf", ANY)
    mock_multi_agent.assert_called_once_with(
        "Sample PDF content.", "report.pdf", mock_ai_client
    )


@pytest.mark.unit
@patch("src.analysis.analyzer.load_txt_text_with_langchain")
def test_analyze_file_content_extraction_failure(mock_load_txt):
    """Test that analyze_file_content raises RuntimeError on extraction failure."""
    mock_load_txt.return_value = (None, None)
    mock_ai_client = Mock()
    with pytest.raises(RuntimeError) as exc_info:
        analyze_file_content(file_path="docs/invalid.txt", client=mock_ai_client)
    assert "Failed to extract content" in str(exc_info.value)
    mock_load_txt.assert_called_once_with("docs/invalid.txt", ANY)


@pytest.mark.unit
@patch("src.analysis.analyzer.load_pdf_text_with_langchain")
@patch("src.analysis.analyzer.process_document_multi_agent")
def test_analyze_file_content_complex_filename(mock_multi_agent, mock_load_pdf):
    """Test parsing of complex multi-part filenames."""
    mock_loader_meta = LoaderMetadata(
        file_type="pdf",
        loader="PyPDFLoader",
        page_count=1,
        pages_sampled=[0],
        char_count=len("Invoice content"),
    )
    mock_load_pdf.return_value = ("Invoice content", mock_loader_meta)

    # Mock response with complex filename (multi-word description)
    mock_raw = RawMetadata(
        domain="financial",
        category="banking",
        doctype="invoice",
        vendor_raw="Bank of America",
        date_raw="2024-03-15",
        subject_raw="Wire transfer fee",
        account_types=None,
    )
    mock_normalized = NormalizedMetadata(
        domain="financial",
        category="banking",
        doctype="invoice",
        vendor_name="bofa",
        date="20240315",
        subject="wire_transfer_fee",
    )
    mock_path = PathMetadata(
        directory_path="financial/banking/invoice/",
        filename="invoice-bofa-wire_transfer_fee-20240315.pdf",
        full_path=(
            "financial/banking/invoice/"
            "invoice-bofa-wire_transfer_fee-20240315.pdf"
        ),
    )
    mock_multi_agent.return_value = (mock_raw, mock_normalized, mock_path)

    mock_ai_client = Mock()

    result = analyze_file_content(file_path="test.pdf", client=mock_ai_client)

    assert result["suggested_name"] == "invoice-bofa-wire_transfer_fee-20240315.pdf"
    assert result["domain"] == "financial"
    assert result["category"] == "banking"
    assert result["doctype"] == "invoice"
    assert result["vendor"] == "bofa"
    assert result["description"] == "wire_transfer_fee"
    assert result["date"] == "20240315"
    assert (
        result["destination_relative_path"]
        == "financial/banking/invoice/invoice-bofa-wire_transfer_fee-20240315.pdf"
    )

    loader_meta = result["loader_metadata"]
    assert loader_meta.file_type == "pdf"
    assert loader_meta.loader == "PyPDFLoader"


@pytest.mark.unit
@patch("src.analysis.analyzer.load_pdf_text_with_langchain")
@patch("src.analysis.analyzer.process_document_multi_agent")
def test_analyze_file_content_no_date(mock_multi_agent, mock_load_pdf):
    """Test parsing of filename without date."""
    mock_loader_meta = LoaderMetadata(
        file_type="pdf",
        loader="PyPDFLoader",
        page_count=1,
        pages_sampled=[0],
        char_count=len("Document content"),
    )
    mock_load_pdf.return_value = ("Document content", mock_loader_meta)

    # Mock response without date in filename
    mock_raw = RawMetadata(
        domain="legal",
        category="contracts",
        doctype="agreement",
        vendor_raw="Vendor Name LLC",
        date_raw="",
        subject_raw="Service agreement",
        account_types=None,
    )
    mock_normalized = NormalizedMetadata(
        domain="legal",
        category="contracts",
        doctype="agreement",
        vendor_name="vendor_name",
        date="",
        subject="service",
    )
    mock_path = PathMetadata(
        directory_path="legal/contracts/agreement/",
        filename="agreement-vendor_name-service.pdf",
        full_path=(
            "legal/contracts/agreement/"
            "agreement-vendor_name-service.pdf"
        ),
    )
    mock_multi_agent.return_value = (mock_raw, mock_normalized, mock_path)

    mock_ai_client = Mock()

    result = analyze_file_content(file_path="test.pdf", client=mock_ai_client)

    assert result["suggested_name"] == "agreement-vendor_name-service.pdf"
    assert result["domain"] == "legal"
    assert result["category"] == "contracts"
    assert result["doctype"] == "agreement"
    assert result["vendor"] == "vendor_name"
    assert result["description"] == "service"
    assert result["date"] == ""
    assert (
        result["destination_relative_path"]
        == "legal/contracts/agreement/agreement-vendor_name-service.pdf"
    )

    loader_meta = result["loader_metadata"]
    assert loader_meta.file_type == "pdf"
    assert loader_meta.loader == "PyPDFLoader"
