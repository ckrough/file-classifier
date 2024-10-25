"""
This module provides functionality for loading and formatting prompts from files.

It includes a function to read a prompt from a file, format it with given
parameters, and handle potential errors during the process.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def load_and_format_prompt(file_path: str, **kwargs: Any) -> str:
    """
    Loads a prompt from a file and formats it with the given keyword arguments.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            prompt: str = file.read()
            return prompt.format(**kwargs)
    except Exception as e:
        logger.error("Error loading or formatting prompt from file: %s", e)
        return ""
