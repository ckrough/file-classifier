"""Module for analyzing file content and extracting metadata."""

import logging
import os
from typing import Optional, Tuple

from openai import OpenAI
from pydantic import BaseModel

from src.ai_file_classifier.prompt_loader import load_and_format_prompt
from src.ai_file_classifier.text_extractor import (extract_text_from_pdf,
                                                   extract_text_from_txt)

logger = logging.getLogger(__name__)


class Analysis(BaseModel):
    """Represents the analyzed metadata of a file."""
    category: str
    vendor: str
    description: str
    date: Optional[str]


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


def analyze_file_content(file_path: str, model: str, client: OpenAI) -> \
        Tuple[Optional[str], Optional[str], Optional[str], Optional[str],
              Optional[str]]:
    """
    Analyzes the content of a file to determine its context and purpose.
    Returns suggested name, category, vendor, description, and date.
    """
    try:
        # Extract content based on file type
        if file_path.lower().endswith('.pdf'):
            content: str = extract_text_from_pdf(file_path)
        else:
            content: str = extract_text_from_txt(file_path)

        # Load prompts
        system_prompt: str = load_and_format_prompt(
            'prompts/file-analysis-system-prompt.txt'
        )

        user_prompt: str = load_and_format_prompt(
            'prompts/file-analysis-user-prompt.txt',
            filename=os.path.basename(file_path),
            content=content
        )

        # Make API request to analyze content
        completion: OpenAI = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            response_format=Analysis,
            max_tokens=50
        )

        logger.debug("Completion response: %s", completion)

        response: Analysis = completion.choices[0].message

        # Add debug output for the recommended metadata
        logger.debug("AI recommended metadata: %s", response.parsed)

        if hasattr(response, 'refusal') and response.refusal:
            raise ValueError(f"Refusal: {response.refusal}")

        analyzed_data: Analysis = standardize_analysis(response.parsed)
        category: str = analyzed_data.category
        vendor: str = analyzed_data.vendor
        description: str = analyzed_data.description
        date: str = analyzed_data.date
        suggested_name: str = generate_filename(analyzed_data)

        # Add debug output for the standardized metadata
        logger.debug("Standardized metadata: %s", analyzed_data)

        return suggested_name, category, vendor, description, date
    except Exception as e:
        raise RuntimeError("Error analyzing file content: %s") from e


def generate_filename(analysis: Analysis) -> str:
    """Generate a standardized filename based on the analysis data."""
    category: str = analysis.category.lower().replace(' ', '-')
    vendor: str = analysis.vendor.lower().replace(' ', '-')
    description: str = analysis.description.lower().replace(' ', '-')
    date: str = analysis.date if analysis.date else ''

    filename: str = (
        f"{vendor}-{category}-{description}"
        f"{'-' + date if date else ''}"
    )

    return filename
