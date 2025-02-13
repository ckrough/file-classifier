"""
Module for data models used across the AI File Classifier application.

This module defines the `Analysis` model, which represents the analyzed metadata of a file.
The `Analysis` model is utilized throughout the application to standardize data handling and ensure consistency.
"""

from typing import Optional

from pydantic import BaseModel, Field


__all__ = ["Analysis"]

class Analysis(BaseModel):
    """Represents the analyzed metadata of a file."""
    category: str = Field(..., description="The file's category (e.g., invoice, receipt).")
    vendor: str = Field(..., description="The vendor or source of the file.")
    description: str = Field(..., description="A brief description of the file content.")
    date: Optional[str] = Field(None, description="The date associated with the file (e.g., 'YYYY-MM-DD').")
