"""Application settings and configuration constants."""

import logging
import os

logger = logging.getLogger(__name__)

# Supported file types
SUPPORTED_MIMETYPES: list[str] = ["text/plain", "application/pdf"]

# Content Extraction Configuration for Performance Tuning
# These settings control how much content is extracted and sent to AI for classification
# Reducing content extraction can significantly reduce API costs and latency

# Strategy for content extraction
# Options: "full", "first_n_pages", "char_limit", "adaptive"
# - "full": Extract all content (highest accuracy, slowest, most expensive)
# - "first_n_pages": Extract first N pages only
# - "char_limit": Extract until character limit reached
# - "adaptive": Smart strategy based on document size (recommended)
CLASSIFICATION_STRATEGY = os.getenv("CLASSIFICATION_STRATEGY", "adaptive")

# Maximum number of pages to extract for page-based strategies
CLASSIFICATION_MAX_PAGES = int(os.getenv("CLASSIFICATION_MAX_PAGES", "3"))

# Maximum characters to extract (safety net to prevent excessive token usage)
CLASSIFICATION_MAX_CHARS = int(os.getenv("CLASSIFICATION_MAX_CHARS", "10000"))

# Whether to include the last page when using page-based extraction
# Useful for documents with summaries on the last page
CLASSIFICATION_INCLUDE_LAST_PAGE = (
    os.getenv("CLASSIFICATION_INCLUDE_LAST_PAGE", "true").lower() == "true"
)
