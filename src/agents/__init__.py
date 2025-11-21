"""
Multi-agent document processing system.

This module implements a 2-agent pipeline for document analysis:
1. Classification Agent - Semantic analysis and metadata extraction
2. Standards Enforcement Agent - Normalization and formatting
3. Deterministic Path Builder - Directory structure assembly (no AI)

The path construction is now deterministic (no AI agent needed).
Conflict resolution has been eliminated - standards agent makes decisive choices.
"""

from src.agents.classification import classify_document
from src.agents.standards import standardize_metadata
from src.agents.pipeline import process_document_multi_agent

__all__ = [
    "classify_document",
    "standardize_metadata",
    "process_document_multi_agent",
]
