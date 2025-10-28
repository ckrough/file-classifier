"""
Standards Enforcement Agent (Naming).

Expertise: Applying normalization rules and formatting conventions.
The logic is deterministic and documented. A dedicated agent can be tested
against the standard, versioned independently, and guarantees consistent
application of conventions.

This is where "receipt from 'Bank of America' dated '01/31/2025' for
'wire transfer'" becomes "receipt-bank_of_america-wire_transfer-20250131"

Responsibilities:
- Vendor name standardization (Bank of America → bank_of_america,
  Dr. John Smith → smith_john_md)
- Date formatting (any format → YYYYMMDD)
- Subject generation (condensing purpose into 1-3 standardized words)
- Document type standardization (ensuring consistent vocabulary)
"""

import logging
from src.ai.client import AIClient
from src.ai.prompts import get_prompt_template
from src.analysis.models import RawMetadata, NormalizedMetadata

__all__ = ["standardize_metadata"]

logger = logging.getLogger(__name__)


def standardize_metadata(raw: RawMetadata, ai_client: AIClient) -> NormalizedMetadata:
    """
    Apply document archival system naming conventions to raw metadata.

    This agent enforces deterministic normalization rules:
    - Vendor names: lowercase, underscores, standard abbreviations
    - Dates: ISO 8601 YYYYMMDD format
    - Subjects: 1-3 words, lowercase, underscores
    - Document types: standardized vocabulary

    Args:
        raw (RawMetadata): Raw metadata from Classification Agent.
        ai_client (AIClient): The AI client to use for standardization.

    Returns:
        NormalizedMetadata: Normalized metadata following naming conventions.

    Raises:
        RuntimeError: If standardization fails or AI client errors.
    """
    try:
        # Get the standards enforcement prompt template
        prompt_template = get_prompt_template("standards-enforcement-agent")

        # Prepare prompt values with raw metadata
        prompt_values = {
            "domain": raw.domain,
            "category": raw.category,
            "doctype": raw.doctype,
            "vendor_raw": raw.vendor_raw,
            "date_raw": raw.date_raw,
            "subject_raw": raw.subject_raw,
        }

        logger.debug(
            "Standards Enforcement Agent normalizing metadata: %s",
            raw.vendor_raw,
        )

        # Invoke AI client with structured output
        normalized: NormalizedMetadata = ai_client.analyze_content(
            prompt_template=prompt_template,
            prompt_values=prompt_values,
            schema=NormalizedMetadata,
        )

        logger.debug(
            "Standards Enforcement Agent normalized: %s → %s",
            raw.vendor_raw,
            normalized.vendor_name,
        )

        return normalized

    except Exception as e:
        logger.error(
            "Standards Enforcement Agent failed for vendor '%s': %s",
            raw.vendor_raw,
            type(e).__name__,
            exc_info=True,
        )
        error_msg = (
            f"Metadata standardization failed for vendor: {raw.vendor_raw}\n"
            f"  → Check that vendor name is recognizable\n"
            f"  → Verify date format is parseable\n"
            f"  → Ensure AI model can normalize naming conventions"
        )
        raise RuntimeError(error_msg) from e
