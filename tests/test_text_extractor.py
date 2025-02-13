"""Unit tests for the text_extractor module."""

import logging
import pytest
from fpdf import FPDF

from src.ai_file_classifier.text_extractor import (extract_text_from_pdf,
                                                   extract_text_from_txt)

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


if __name__ == "__main__":
    pytest.main()
