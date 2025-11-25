"""Tests for LangChain-backed document loaders.

These tests exercise the happy paths for TXT and PDF loading using the
real loaders, but with tiny fixture files to keep them fast.
"""

from __future__ import annotations

from pathlib import Path

from fpdf import FPDF

from src.files.extractors import ExtractionConfig
from src.files.langchain_loader import (
    load_pdf_text_with_langchain,
    load_txt_text_with_langchain,
)


def _make_sample_pdf(path: Path, text: str) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=text, ln=True)
    pdf.output(str(path))


def test_load_txt_text_with_langchain(tmp_path):
    txt_path = tmp_path / "sample.txt"
    txt_content = "Hello from LangChain loader"
    txt_path.write_text(txt_content, encoding="utf-8")

    config = ExtractionConfig(strategy="full", max_chars=1000)
    content, meta = load_txt_text_with_langchain(str(txt_path), config)

    assert content is not None
    assert "Hello from LangChain loader" in content
    assert meta is not None
    assert meta.file_type == "txt"
    assert meta.char_count == len(content)


def test_load_pdf_text_with_langchain(tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    pdf_text = "Hello from LangChain PDF loader"
    _make_sample_pdf(pdf_path, pdf_text)

    config = ExtractionConfig(strategy="full", max_chars=5000)
    content, meta = load_pdf_text_with_langchain(str(pdf_path), config)

    assert content is not None
    assert "Hello" in content
    assert meta is not None
    assert meta.file_type == "pdf"
    assert meta.page_count is not None
    assert meta.char_count == len(content)
