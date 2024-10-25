"""Unit tests for the text_extractor module."""

import logging
import os
import tempfile

import pytest

from src.ai_file_classifier.text_extractor import (extract_text_from_pdf,
                                                   extract_text_from_txt)

logger = logging.getLogger(__name__)


def test_extract_text_from_txt():
    """
    Test the extraction of text from a plain text file.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w',
                                     encoding='utf-8') as temp_txt_file:
        temp_txt_file.write("This is a sample text for testing.")
        temp_txt_file_path = temp_txt_file.name

    try:
        # Test extraction of text from the text file
        result = extract_text_from_txt(temp_txt_file_path)
        assert result == "This is a sample text for testing."
    except IOError as e:
        pytest.fail(f"Failed to read text file: {e}")
    except AssertionError as e:
        pytest.fail(f"Extracted text does not match expected: {e}")
    finally:
        # Clean up the temporary file
        os.remove(temp_txt_file_path)


def test_extract_text_from_pdf():
    """
    Test the extraction of text from a PDF file.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf", mode='wb') as temp_pdf_file:
        # Create a simple PDF file for testing
        from fpdf import FPDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="This is a sample text for testing.", ln=True)
        pdf.output(temp_pdf_file.name)
        temp_pdf_file_path = temp_pdf_file.name

    try:
        # Test extraction of text from the PDF file
        result = extract_text_from_pdf(temp_pdf_file_path)
        assert "This is a sample text for testing." in result
    except IOError as e:
        pytest.fail(f"Failed to read PDF file: {e}")
    except AssertionError as e:
        pytest.fail(f"Extracted text does not contain expected content: {e}")
    finally:
        # Clean up the temporary file
        os.remove(temp_pdf_file_path)


if __name__ == "__main__":
    pytest.main()
