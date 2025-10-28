"""Unit tests for the text_extractor module."""

import logging
import pytest
from fpdf import FPDF

from src.files.extractors import extract_text_from_pdf, extract_text_from_txt

logger = logging.getLogger(__name__)


def test_extract_text_from_txt(tmp_path):
    """
    Test the extraction of text from a plain text file.
    """
    file_path = tmp_path / "sample.txt"
    file_path.write_text("This is a sample text for testing.", encoding="utf-8")
    result = extract_text_from_txt(str(file_path))
    assert result == "This is a sample text for testing."


def test_extract_text_from_pdf(tmp_path):
    """
    Test the extraction of text from a PDF file.
    """
    file_path = tmp_path / "sample.pdf"
    # Create a simple PDF file for testing
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="This is a sample text for testing.", ln=True)
    pdf.output(str(file_path))
    result = extract_text_from_pdf(str(file_path))
    assert result is not None, "Expected non-None result from PDF extraction"
    assert "This is a sample text for testing." in result


def test_extract_text_from_nonexistent_txt(tmp_path, caplog):
    """
    Test that extraction from a non-existent TXT file returns None and logs an error.
    """
    file_path = tmp_path / "nonexistent.txt"
    result = extract_text_from_txt(str(file_path))
    assert result is None
    assert any(
        "Error opening text file:" in record.message for record in caplog.records
    )


def test_extract_text_from_nonexistent_pdf(tmp_path, caplog):
    """
    Test that extraction from a non-existent PDF file returns None and logs an error.
    """
    file_path = tmp_path / "nonexistent.pdf"
    result = extract_text_from_pdf(str(file_path))
    assert result is None
    assert any("Error opening PDF file:" in record.message for record in caplog.records)


def test_extract_text_from_txt_invalid_encoding(tmp_path, caplog):
    """Test that extraction from a TXT file with invalid encoding
    returns None and logs an error."""
    file_path = tmp_path / "invalid.txt"
    # Write bytes that are not valid UTF-8
    file_path.write_bytes(b"\xff\xfe\xfa")
    result = extract_text_from_txt(str(file_path))
    assert result is None
    assert any(
        "Error decoding text file:" in record.message for record in caplog.records
    )


if __name__ == "__main__":
    pytest.main()
