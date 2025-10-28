"""
Document Classification Agent.

Expertise: Semantic understanding of document content and taxonomy mapping.
Requires deep semantic understanding of financial/medical/legal contexts.
This is pattern recognition and content comprehension.

Responsibilities:
- Determine Domain (Financial/Property/Insurance/Tax/Legal/Medical)
- Determine Category (Banking, Real_Estate, Health, etc.)
- Identify Document Type (statement, receipt, invoice, policy, etc.)
- Extract raw metadata (vendor, dates, amounts, account types, subjects)
"""

import logging
from src.ai.client import AIClient
from src.ai.prompts import get_prompt_template
from src.analysis.models import RawMetadata

__all__ = ["classify_document"]

logger = logging.getLogger(__name__)


def classify_document(content: str, filename: str, ai_client: AIClient) -> RawMetadata:
    """
    Analyze document content to extract raw semantic metadata.

    This agent performs semantic analysis to understand document purpose,
    identify key entities, and extract unprocessed metadata before
    standardization.

    Args:
        content (str): The extracted text content of the document.
        filename (str): The original filename (for context).
        ai_client (AIClient): The AI client to use for analysis.

    Returns:
        RawMetadata: Raw metadata including domain, category, doctype,
                     vendor_raw, date_raw, subject_raw, and optional
                     account_types.

    Raises:
        RuntimeError: If classification fails or AI client errors.
    """
    try:
        # Get the classification prompt template
        prompt_template = get_prompt_template("classification-agent")

        # Prepare prompt values
        prompt_values = {"filename": filename, "content": content}

        logger.debug(
            "Classification Agent analyzing document: %s (content_length=%d)",
            filename,
            len(content),
        )

        # Invoke AI client with structured output
        raw_metadata: RawMetadata = ai_client.analyze_content(
            prompt_template=prompt_template,
            prompt_values=prompt_values,
            schema=RawMetadata,
        )

        logger.debug("Classification Agent extracted metadata: %s", raw_metadata)

        return raw_metadata

    except Exception as e:
        logger.error("Classification Agent failed: %s", e, exc_info=True)
        raise RuntimeError("Document classification failed") from e
