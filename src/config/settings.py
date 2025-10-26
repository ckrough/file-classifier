"""Application settings and configuration constants."""

import logging

logger = logging.getLogger(__name__)

# Database configuration
DB_FILE: str = "file_cache.db"

# Supported file types
SUPPORTED_MIMETYPES: list[str] = ["text/plain", "application/pdf"]
