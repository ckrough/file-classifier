"""
Path Construction Agent.

Expertise: Directory structure assembly and special case handling.
Knows about file systems, not document semantics.

Responsibilities:
- Build directory path: Domain/Category/Vendor/
- Handle special structures (Tax requires year subdirectories:
  Tax/Federal/2024/)
- Normalize vendor names for directory use (addresses, abbreviations)
- Apply filename to complete path
"""

import logging
from src.ai.client import AIClient
from src.ai.prompts import get_prompt_template
from src.analysis.models import NormalizedMetadata, PathMetadata

__all__ = ["construct_path"]

logger = logging.getLogger(__name__)


def construct_path(
    normalized: NormalizedMetadata, ai_client: AIClient, file_extension: str = ".pdf"
) -> PathMetadata:
    """
    Assemble directory path and filename following taxonomy structure.

    This agent constructs paths following the document archival system:
    - Standard: Domain/Category/Vendor/doctype-vendor-subject-YYYYMMDD.ext
    - Special cases: Tax/Federal/2024/return-irs-form1040-20250415.pdf

    Args:
        normalized (NormalizedMetadata): Normalized metadata from Standards Agent.
        ai_client (AIClient): The AI client to use for path construction.
        file_extension (str): File extension to append (default: .pdf).

    Returns:
        PathMetadata: Complete path including directory_path, filename,
                      and full_path.

    Raises:
        RuntimeError: If path construction fails or AI client errors.
    """
    try:
        # Get the path construction prompt template
        prompt_template = get_prompt_template("path-construction-agent")

        # Prepare prompt values
        prompt_values = {
            "domain": normalized.domain,
            "category": normalized.category,
            "vendor_name": normalized.vendor_name,
            "doctype": normalized.doctype,
            "subject": normalized.subject,
            "date": normalized.date,
            "file_extension": file_extension,
        }

        logger.debug(
            "Path Construction Agent building path for: %s/%s/%s",
            normalized.domain,
            normalized.category,
            normalized.vendor_name,
        )

        # Invoke AI client with structured output
        path_metadata: PathMetadata = ai_client.analyze_content(
            prompt_template=prompt_template,
            prompt_values=prompt_values,
            schema=PathMetadata,
        )

        logger.debug(
            "Path Construction Agent built path: %s",
            path_metadata.full_path,
        )

        return path_metadata

    except Exception as e:
        logger.error("Path Construction Agent failed: %s", e, exc_info=True)
        raise RuntimeError("Path construction failed") from e
