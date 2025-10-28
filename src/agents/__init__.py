"""
Multi-agent document processing system.

This module implements a 4-agent pipeline for document analysis:
1. Classification Agent - Semantic analysis and metadata extraction
2. Standards Enforcement Agent - Normalization and formatting
3. Path Construction Agent - Directory structure assembly
4. Conflict Resolution Agent - Edge case handling

Each agent has a specific responsibility and expertise domain,
following the document archival system design standards.
"""

from src.agents.classification import classify_document
from src.agents.standards import standardize_metadata
from src.agents.path_construction import construct_path
from src.agents.conflict_resolution import resolve_conflicts
from src.agents.pipeline import process_document_multi_agent

__all__ = [
    "classify_document",
    "standardize_metadata",
    "construct_path",
    "resolve_conflicts",
    "process_document_multi_agent",
]
