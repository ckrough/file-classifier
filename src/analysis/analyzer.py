"""
File content analysis and metadata extraction.

This module coordinates the analysis workflow using the multi-agent pipeline
for document processing with a 4-agent system for intelligent file classification.
"""

import logging
import os
from typing import Optional

from src.ai.client import AIClient
from src.files.extractors import extract_text_from_pdf, extract_text_from_txt
from src.agents.pipeline import process_document_multi_agent

__all__ = ["analyze_file_content"]

logger = logging.getLogger(__name__)


def analyze_file_content(file_path: str, client: AIClient) -> tuple[
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
    Optional[str],
]:
    """
    Analyze the content of a file using the multi-agent pipeline.
    Returns suggested name, category, vendor, description, date, and destination path.

    Uses a 4-agent pipeline for intelligent document processing:
    1. Classification Agent: Semantic analysis and metadata extraction
    2. Standards Agent: Apply naming conventions and normalization
    3. Path Construction Agent: Build directory structure and filename
    4. Conflict Resolution Agent: Handle edge cases and ambiguities

    Args:
        file_path (str): The path to the file to analyze.
        client (AIClient): The AI client to use for analysis.

    Returns:
        tuple: (suggested_name, category, vendor, description, date,
               destination_relative_path)
               - suggested_name: basename only (for backward compatibility)
               - destination_relative_path: full path relative to archive root
                 (e.g., "Financial/Banking/chase/statement-chase-checking-20240115.pdf")
    """
    try:
        # Extract content based on file type
        if file_path.lower().endswith(".pdf"):
            content: Optional[str] = extract_text_from_pdf(file_path)
        else:
            content: Optional[str] = extract_text_from_txt(file_path)

        if content is None:
            raise ValueError(f"Failed to extract content from file: {file_path}")

        filename = os.path.basename(file_path)

        logger.info("Using multi-agent pipeline for analysis")
        resolved = process_document_multi_agent(content, filename, client)

        # Extract filename from the final path
        # Path format: Domain/Category/Vendor/doctype-vendor-subject-YYYYMMDD.ext
        suggested_name = os.path.basename(resolved.final_path)
        destination_relative_path = resolved.final_path

        # Log alternative paths if present
        if resolved.alternative_paths:
            logger.info(
                "Alternative paths available: %s", ", ".join(resolved.alternative_paths)
            )
        if resolved.resolution_notes:
            logger.info("Resolution notes: %s", resolved.resolution_notes)

        # For backward compatibility, extract category, vendor, description, date
        # Filename format: doctype-vendor-subject-YYYYMMDD.ext
        parts = os.path.splitext(suggested_name)[0].split("-")

        if len(parts) >= 4:
            doctype = parts[0]
            vendor = parts[1]
            # Subject may be multiple parts
            date_str = parts[-1]
            date = date_str if date_str.isdigit() and len(date_str) == 8 else ""
            description = "-".join(parts[2:-1] if date else parts[2:])
            category = doctype  # Use doctype as category

            logger.debug(
                "Multi-agent result: suggested_name=%s, category=%s, "
                "vendor=%s, description=%s, date=%s, destination=%s",
                suggested_name,
                category,
                vendor,
                description,
                date,
                destination_relative_path,
            )
            return (
                suggested_name,
                category,
                vendor,
                description,
                date,
                destination_relative_path,
            )

        # Fallback if parsing fails
        logger.warning("Failed to parse filename: %s", suggested_name)
        return suggested_name, "", "", "", "", destination_relative_path

    except (ValueError, FileNotFoundError) as e:
        logger.error("Failed to analyze file content: %s", e)
        raise RuntimeError("Error analyzing file content") from e
