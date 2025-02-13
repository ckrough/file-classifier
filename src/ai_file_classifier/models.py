"""
Module for data models used across the AI File Classifier application.

This module defines the `Analysis` model, which represents the analyzed metadata of a file.
The `Analysis` model is utilized throughout the application to standardize data handling and ensure consistency.
"""

from typing import Optional

from pydantic import BaseModel


__all__ = ["Analysis"]

class Analysis(BaseModel):
    """Represents the analyzed metadata of a file."""
    category: str
    vendor: str
    description: str
    date: Optional[str]
