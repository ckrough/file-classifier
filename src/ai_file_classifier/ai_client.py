"""
Module for AI Client Abstractions.

This module provides abstract and concrete implementations of AI clients
for analyzing file content using various AI models.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from pydantic import ValidationError
import openai

from src.ai_file_classifier.models import Analysis
from src.config.logging_config import setup_logging

logger = logging.getLogger(__name__)


class AIClient(ABC):
    """Abstract base class for AI clients."""

    # pylint: disable=too-few-public-methods

    @abstractmethod
    def analyze_content(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_tokens: Optional[int] = None,
    ) -> Analysis:
        if max_tokens is None:
            max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", 50))
        """
        Analyze the content using the AI model.

        Args:
            system_prompt (str): The system prompt for the AI.
            user_prompt (str): The user prompt for the AI.
            model (str): The AI model to use.
            max_tokens (int): The maximum number of tokens for the response.

        Returns:
            Analysis: The analyzed metadata of the file.
        """


class OpenAIClient(AIClient):
    """Concrete implementation of AIClient using OpenAI."""

    # pylint: disable=too-few-public-methods

    def __init__(self, api_key: str = None):
        """Initialize the OpenAI client with the API key from environment variables."""
        setup_logging()
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.critical(
                "OPENAI_API_KEY not provided or set in environment variables."
            )
            raise ValueError("OPENAI_API_KEY must be provided.")
        openai.api_key = api_key

    def analyze_content(
        self, system_prompt: str, user_prompt: str, model: str, max_tokens: int = 50
    ) -> Analysis:
        """
        Analyze the content using OpenAI's ChatCompletion API.

        Args:
            system_prompt (str): The system prompt for the AI.
            user_prompt (str): The user prompt for the AI.
            model (str): The AI model to use (e.g., 'gpt-4').
            max_tokens (int, optional): The maximum number of tokens for the response. Defaults to 50.

        Returns:
            Analysis: The analyzed metadata of the file.

        Raises:
            RuntimeError: If there's an error communicating with the OpenAI API.
        """
        try:

            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
            )

            content = response.choices[0].message["content"]

            # Optional: Validate JSON structure before parsing
            try:
                json_content = json.loads(content)
            except json.JSONDecodeError as json_err:
                logger.error("Invalid JSON format in OpenAI response: %s", json_err)
                raise RuntimeError(
                    "Invalid JSON format in OpenAI response."
                ) from json_err

            analysis = Analysis.parse_obj(json_content)
            return analysis
        except ValidationError as ve:
            logger.error(
                "Validation error while parsing Analysis: %s", ve, exc_info=True
            )
            raise RuntimeError("Validation error while parsing Analysis.") from ve
        except openai.error.OpenAIError as e:
            logger.exception("Error communicating with OpenAI API.")
            raise RuntimeError("Error communicating with OpenAI API.") from e
