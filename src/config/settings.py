"""Application settings and configuration constants."""

import logging
import os
import re

logger = logging.getLogger(__name__)

# Supported file types
SUPPORTED_MIMETYPES: list[str] = ["text/plain", "application/pdf"]

# GPO Naming Standards Constants
# These constants enforce Government Publishing Office (GPO) file naming standards
# Reference: https://www.gpo.gov/how-to-work-with-us/vendors/supplier-performance

# Maximum total path length (filesystem limit)
MAX_PATH_LENGTH = 200

# Maximum directory hierarchy depth
MAX_HIERARCHY_DEPTH = 5

# Target filename length (recommended for readability and compatibility)
TARGET_FILENAME_LENGTH = 25

# Allowed characters pattern for GPO compliance (a-z, 0-9, underscores, hyphens)
ALLOWED_CHARS_PATTERN = re.compile(r"^[a-z0-9_-]+$", re.IGNORECASE)

# Filler words to remove per GPO standards
FILLER_WORDS = ["a", "and", "of", "the", "to"]

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

# Naming style configuration
# Allowed naming styles
ALLOWED_NAMING_STYLES = {"compact_gpo", "descriptive_nara"}
DEFAULT_NAMING_STYLE = "descriptive_nara"

NAMING_STYLE = os.getenv("NAMING_STYLE", DEFAULT_NAMING_STYLE).strip().lower()
if NAMING_STYLE not in ALLOWED_NAMING_STYLES:
    logger.warning(
        "Unknown NAMING_STYLE '%s'; falling back to '%s'",
        NAMING_STYLE,
        DEFAULT_NAMING_STYLE,
    )
    NAMING_STYLE = DEFAULT_NAMING_STYLE

# Optional plugin entry point/module for custom styles
NAMING_STYLE_PLUGIN = os.getenv("NAMING_STYLE_PLUGIN", "").strip()
