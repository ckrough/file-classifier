"""
File content analysis and metadata extraction.

This module coordinates the analysis workflow using the multi-agent pipeline
for document processing. It maintains backward compatibility with the legacy
interface while leveraging the new 4-agent system.
"""

import logging
import os
from typing import Optional

from src.ai.client import AIClient
from src.ai.prompts import get_file_analysis_prompt
from src.analysis.models import Analysis
from src.analysis.filename import generate_filename
from src.files.extractors import extract_text_from_pdf, extract_text_from_txt
from src.agents.pipeline import process_document_multi_agent

__all__ = ["analyze_file_content", "standardize_analysis"]

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
        category=analysis.category.lower().replace(" ", "-"),
        vendor=analysis.vendor.lower().replace(" ", "-"),
        description=analysis.description.lower().replace(" ", "-"),
        date=analysis.date if analysis.date else "",
    )


def analyze_file_content(
    file_path: str, client: AIClient, use_multi_agent: Optional[bool] = None
) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Analyze the content of a file to determine its context and purpose.
    Returns suggested name, category, vendor, description, and date.

    This function uses the multi-agent pipeline by default, which provides
    more accurate and consistent results through specialized agents. The legacy
    single-agent analysis can be used by setting use_multi_agent=False or by
    setting the USE_LEGACY_ANALYSIS environment variable to "true".

    Args:
        file_path (str): The path to the file to analyze.
        client (AIClient): The AI client to use for analysis.
        use_multi_agent (bool, optional): Use multi-agent pipeline.
                                          If None (default), checks environment
                                          variable USE_LEGACY_ANALYSIS.
                                          If "true", uses legacy mode.

    Returns:
        tuple: containing suggested_name, category, vendor, description, and date.
    """
    # Determine whether to use multi-agent mode
    if use_multi_agent is None:
        # Check environment variable
        use_legacy = os.getenv("USE_LEGACY_ANALYSIS", "false").lower() == "true"
        use_multi_agent = not use_legacy

    try:
        # Extract content based on file type
        if file_path.lower().endswith(".pdf"):
            content: Optional[str] = extract_text_from_pdf(file_path)
        else:
            content: Optional[str] = extract_text_from_txt(file_path)

        if content is None:
            raise ValueError(f"Failed to extract content from file: {file_path}")

        filename = os.path.basename(file_path)

        # Use multi-agent pipeline (new approach)
        if use_multi_agent:
            logger.info("Using multi-agent pipeline for analysis")
            resolved = process_document_multi_agent(content, filename, client)

            # Extract filename from the final path
            # Path format: Domain/Category/Vendor/doctype-vendor-subject-YYYYMMDD.ext
            suggested_name = os.path.basename(resolved.final_path)

            # For backward compatibility, we need to extract category, vendor, description, date
            # from the resolved path. Parse the filename components.
            # Filename format: doctype-vendor-subject-YYYYMMDD.ext
            parts = os.path.splitext(suggested_name)[0].split("-")

            if len(parts) >= 4:
                doctype = parts[0]
                vendor = parts[1]
                # Subject may be multiple parts
                date = parts[-1] if parts[-1].isdigit() and len(parts[-1]) == 8 else ""
                description = "-".join(parts[2:-1] if date else parts[2:])
                category = doctype  # Use doctype as category for backward compatibility

                logger.debug(
                    "Multi-agent result: suggested_name=%s, category=%s, "
                    "vendor=%s, description=%s, date=%s",
                    suggested_name,
                    category,
                    vendor,
                    description,
                    date,
                )
                return suggested_name, category, vendor, description, date

            # Fallback if parsing fails
            logger.warning("Failed to parse multi-agent filename: %s", suggested_name)
            return suggested_name, "", "", "", ""

        # Legacy single-agent approach (for backward compatibility)
        logger.info("Using legacy single-agent analysis")
        prompt_template = get_file_analysis_prompt()
        prompt_values = {"filename": filename, "content": content}
        logger.debug(
            "Prepared prompt values: filename=%s, content_length=%d",
            prompt_values["filename"],
            len(prompt_values["content"]),
        )

        # Make API request to analyze content
        response: Analysis = client.analyze_content(
            prompt_template=prompt_template,
            prompt_values=prompt_values,
        )

        logger.debug("AI recommended metadata: %s", response)

        analyzed_data: Analysis = standardize_analysis(response)
        category: str = analyzed_data.category
        vendor: str = analyzed_data.vendor
        description: str = analyzed_data.description
        date: str = analyzed_data.date
        suggested_name: str = generate_filename(analyzed_data)

        logger.debug("Standardized metadata: %s", analyzed_data)

        return suggested_name, category, vendor, description, date

    except (ValueError, FileNotFoundError) as e:
        logger.error("Failed to analyze file content: %s", e)
        raise RuntimeError("Error analyzing file content") from e
