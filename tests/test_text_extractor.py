import pytest
from src.ai_file_classifier.text_extractor import extract_text_from_pdf, extract_text_from_txt
import tempfile
import os


def test_extract_text_from_txt():
    """
    Test the extraction of text from a .txt file.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8') as temp_txt_file:
        temp_txt_file.write("This is a test text file.")
        temp_txt_file_path = temp_txt_file.name

    try:
        # Test the function
        extracted_text = extract_text_from_txt(temp_txt_file_path)
        assert extracted_text == "This is a test text file."
    finally:
        # Clean up the temporary file
        os.remove(temp_txt_file_path)


def test_extract_text_from_pdf():
    """
    Test the extraction of text from a .pdf file.
    """
    # Creating a PDF file for testing
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="This is a test PDF file.", ln=True)
    temp_pdf_file_path = tempfile.mktemp(suffix=".pdf")
    pdf.output(temp_pdf_file_path)

    try:
        # Test the function
        extracted_text = extract_text_from_pdf(temp_pdf_file_path)
        assert "This is a test PDF file." in extracted_text
    finally:
        # Clean up the temporary file
        os.remove(temp_pdf_file_path)


if __name__ == "__main__":
    pytest.main()
