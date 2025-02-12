"""Module for data models used across the AI File Classifier application."""

from typing import Optional
from pydantic import BaseModel


class Analysis(BaseModel):
    """Represents the analyzed metadata of a file."""
    category: str
    vendor: str
    description: str
    date: Optional[str]
