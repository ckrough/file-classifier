"""
Path Construction Agent.

Expertise: Directory structure assembly and special case handling.
Knows about file systems, not document semantics.

Responsibilities:
- Build directory path: domain/category/vendor/ (all lowercase)
- Construct standard 3-level taxonomy: domain/category/vendor/
- Tax documents follow standard format: financial/tax/vendor/
- Normalize vendor names for directory use (addresses, abbreviations)
- Apply filename to complete path
"""

import logging
import os
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
    - Standard: domain/category/vendor/doctype-vendor-subject-YYYYMMDD.ext
    - Example: financial/banking/chase/statement-chase-checking-20250131.pdf
    - Tax documents: financial/tax/irs/return-irs-form1040-20250415.pdf

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

        # Defensive lowercase conversion: Ensure all path components are lowercase
        # This guarantees consistency even if the AI doesn't follow prompt exactly
        path_metadata = _lowercase_path_components(path_metadata)

        logger.debug(
            "Path Construction Agent built path: %s",
            path_metadata.full_path,
        )

        return path_metadata

    except Exception as e:
        logger.error(
            "Path Construction Agent failed for %s/%s/%s: %s",
            normalized.domain,
            normalized.category,
            normalized.vendor_name,
            type(e).__name__,
            exc_info=True,
        )
        error_msg = (
            f"Path construction failed for {normalized.domain}/"
            f"{normalized.category}/{normalized.vendor_name}\n"
            f"  → Check that domain/category/vendor are valid\n"
            f"  → Verify date format is YYYYMMDD\n"
            f"  → Ensure doctype and subject are standardized"
        )
        raise RuntimeError(error_msg) from e


def _lowercase_path_components(path_metadata: PathMetadata) -> PathMetadata:
    """
    Defensive conversion: Lowercase all directory and filename components.

    Ensures consistency even if the AI doesn't follow prompts exactly.
    Preserves file extension case-sensitivity (though typically lowercase).

    Args:
        path_metadata (PathMetadata): Original path metadata from AI.

    Returns:
        PathMetadata: Path with all components lowercased.
    """
    # Split the full path into directory and filename
    directory_path = path_metadata.directory_path.lower()
    filename = path_metadata.filename.lower()

    # Reconstruct full path (which includes extension)
    # Extract extension to preserve it if needed
    name_without_ext, ext = os.path.splitext(path_metadata.full_path)
    full_path_lowercase = f"{name_without_ext.lower()}{ext.lower()}"

    return PathMetadata(
        directory_path=directory_path,
        filename=filename,
        full_path=full_path_lowercase,
    )
