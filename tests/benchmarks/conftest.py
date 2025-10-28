"""Shared fixtures for benchmark tests."""

import pytest

from src.analysis.models import Analysis


@pytest.fixture
def sample_analysis_simple() -> Analysis:
    """
    Simple Analysis object for benchmarking standardization.

    Returns:
        Analysis: Pre-populated analysis object with simple values.
    """
    return Analysis(
        category="Invoice",
        vendor="Acme",
        description="Services",
        date="2024-01-15",
    )


@pytest.fixture
def sample_analysis_complex() -> Analysis:
    """
    Complex Analysis object with longer strings for realistic benchmarking.

    Returns:
        Analysis: Pre-populated analysis object with complex values.
    """
    return Analysis(
        category="Financial Statement Quarterly Report",
        vendor="International Business Machines Corporation",
        description="Comprehensive Quarterly Financial Analysis "
        "and Performance Metrics",
        date="2024-01-15",
    )


@pytest.fixture
def sample_analysis_with_spaces() -> Analysis:
    """
    Analysis object with many spaces requiring normalization.

    Returns:
        Analysis: Analysis object with space-heavy strings.
    """
    return Analysis(
        category="Invoice   Document   Type",
        vendor="Acme   Corporation   LLC",
        description="Monthly   Recurring   Services   Agreement",
        date="2024-01-15",
    )


@pytest.fixture
def sample_analysis_batch() -> list[Analysis]:
    """
    Batch of Analysis objects for testing collection operations.

    Returns:
        list[Analysis]: List of 100 analysis objects for batch benchmarking.
    """
    return [
        Analysis(
            category=f"Category {i % 10}",
            vendor=f"Vendor {i % 20}",
            description=f"Description for document {i}",
            date=f"2024-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
        )
        for i in range(100)
    ]


@pytest.fixture
def sample_filename_base() -> str:
    """
    Sample base filename for testing filename operations.

    Returns:
        str: Base filename string.
    """
    return "original-document-name.pdf"


@pytest.fixture
def sample_content_small() -> str:
    """
    Small text content for testing content processing (~1KB).

    Returns:
        str: Sample text content.
    """
    return "This is a sample document for testing. " * 20


@pytest.fixture
def sample_content_large() -> str:
    """
    Large text content for testing content processing (~100KB).

    Returns:
        str: Sample text content.
    """
    return "This is a sample document for testing. " * 2000
