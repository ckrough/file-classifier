"""Module for analyzing file content and extracting metadata."""

import logging
import os
from typing import Optional, Tuple

from src.ai_file_classifier.ai_client import AIClient
from src.ai_file_classifier.models import Analysis
from src.ai_file_classifier.prompt_loader import load_and_format_prompt
from src.ai_file_classifier.text_extractor import (
    extract_text_from_pdf,
    extract_text_from_txt,
)

logger = logging.getLogger(__name__)


def standardize_analysis(analysis: Analysis) -> Analysis:
    """
    Standardize the analysis data by converting fields to lowercase and
    replacing spaces with hyphens.

    Args:
        analysis (Analysis): The original analysis object.

    Returns:
        Analysis: A new Analysis object with standardized fields.
    """
    return Analysis(
        category=analysis.category.lower().replace(' ', '-'),
        vendor=analysis.vendor.lower().replace(' ', '-'),
        description=analysis.description.lower().replace(' ', '-'),
        date=analysis.date if analysis.date else ''
    )


def analyze_file_content(
    file_path: str,
    client: AIClient
) -> Tuple[
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str]
]:
    """
    Analyzes the content of a file to determine its context and purpose.
    Returns suggested name, category, vendor, description, and date.

    Args:
        file_path (str): The path to the file to analyze.
        client (AIClient): The AI client to use for analysis.

    Returns:
        Tuple containing suggested_name, category, vendor, description, and date.
    """
    try:
        # Extract content based on file type
        if file_path.lower().endswith('.pdf'):
            content: Optional[str] = extract_text_from_pdf(file_path)
        else:
            content: Optional[str] = extract_text_from_txt(file_path)

        if content is None:
            raise ValueError(f"Failed to extract content from file: {file_path}")

        # Load prompts
        system_prompt: str = load_and_format_prompt(
            'prompts/file-analysis-system-prompt.txt'
        )
        logger.debug("System prompt loaded: %s", system_prompt)

        user_prompt: str = load_and_format_prompt(
            'prompts/file-analysis-user-prompt.txt',
            filename=os.path.basename(file_path),
            content=content
        )
        logger.debug("User prompt loaded: %s", user_prompt)

        # Make API request to analyze content
        response: Analysis = client.analyze_content(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        logger.debug("AI recommended metadata: %s", response)

        analyzed_data: Analysis = standardize_analysis(response)
        category: str = analyzed_data.category
        vendor: str = analyzed_data.vendor
        description: str = analyzed_data.description
        date: str = analyzed_data.date
        suggested_name: str = generate_filename(analyzed_data)

        # Add debug output for the standardized metadata
        logger.debug("Standardized metadata: %s", analyzed_data)

        return suggested_name, category, vendor, description, date
    except (ValueError, FileNotFoundError) as e:
        logger.error("Failed to analyze file content: %s", e)
        raise RuntimeError("Error analyzing file content") from e


def generate_filename(analysis: Analysis) -> str:
    """Generate a standardized filename based on the analysis data."""
    category: str = analysis.category
    vendor: str = analysis.vendor
    description: str = analysis.description
    date: str = analysis.date if analysis.date else ''

    filename: str = f"{vendor}-{category}-{description}"
    if date:
        filename += f"-{date}"

    return filename
