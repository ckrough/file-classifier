"""
Module for loading and formatting AI prompts.

This module provides the `load_and_format_prompt` function, which loads a prompt template
from a specified file and formats it with the provided keyword arguments. It includes
robust error handling to ensure graceful failure and informative logging in case of issues.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["load_and_format_prompt"]


def load_and_format_prompt(file_path: str, **kwargs: Any) -> str:
    """
    Load a prompt from a file and format it with the given keyword arguments.

    Args:
        file_path (str): The path to the prompt file.
        **kwargs: Keyword arguments for formatting the prompt.

    Returns:
        str: The formatted prompt or an empty string if an error occurs.
    """
    # Read the prompt file.
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            prompt: str = file.read().strip()
    except (IOError, OSError) as err:
        logger.error("Error reading prompt file %s: %s", file_path, err)
        return ""

    # Clean and prepare the prompt string.
    prompt = ' '.join(prompt.split())

    # If no formatting arguments are provided, return the prompt as-is.
    if not kwargs:
        return prompt

    # Format the prompt with provided keyword arguments.
    try:
        formatted_prompt = prompt.format(**kwargs)
    except KeyError as ke:
        missing_key = ke.args[0]
        logger.error(
            "Missing required keyword argument '%s' in prompt file %s", missing_key, file_path
        )
        raise
    except ValueError as ve:
        # Likely due to unescaped literal braces in a prompt file intended as JSON or similar.
        logger.error(
            "Value error formatting prompt from %s: %s. "
            "Ensure that literal braces are escaped (i.e. use double braces '{{' and '}}').",
            file_path,
            ve,
        )
        raise
    except (TypeError, AttributeError) as e:
        logger.error("Unexpected error formatting prompt from %s: %s", file_path, e)
        logger.debug("Prompt content: %r, Arguments: %r", prompt, kwargs)
        raise

    return formatted_prompt
