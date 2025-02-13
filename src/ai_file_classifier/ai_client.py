"""
Module for AI Client Abstractions.

This module defines the abstract base class `AIClient` and its concrete
implementation `OpenAIClient`. These classes are responsible for interfacing
with AI models to analyze file content. The `OpenAIClient` utilizes OpenAI's APIs
to perform content analysis based on provided prompts and models.

Classes:
    AIClient: Abstract base class outlining the interface for AI clients.
    OpenAIClient: Concrete implementation of AIClient using OpenAI's services.
"""

import os
import logging
from abc import ABC, abstractmethod
import json
from typing import Optional

from pydantic import ValidationError
from openai import OpenAI, OpenAIError

from src.ai_file_classifier.models import Analysis
__all__ = ["AIClient", "OpenAIClient"]

logger = logging.getLogger(__name__)


class AIClient(ABC):
    """Abstract base class for AI clients."""

    # pylint: disable=too-few-public-methods
    # This class intentionally has few public methods as it serves as an interface.

    @abstractmethod
    def analyze_content(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_tokens: Optional[int] = None,
    ) -> Analysis:
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

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the OpenAI client with the API key from environment variables."""
        if not api_key:
            api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.critical(
                "OPENAI_API_KEY not provided or set in environment variables."
            )
            raise ValueError("OPENAI_API_KEY must be provided.")
        self.client = OpenAI(api_key=api_key)

    def analyze_content(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_tokens: Optional[int] = None
    ) -> Analysis:
        """
        Analyze the content using OpenAI's ChatCompletion API.

        Args:
            system_prompt (str): The system prompt for the AI.
            user_prompt (str): The user prompt for the AI.
            model (str): The AI model to use (e.g., 'gpt-4').
            max_tokens (int, optional): The maximum number of tokens for the response. If not provided,
                defaults to the value of the OPENAI_MAX_TOKENS environment variable (default: 50).

        Returns:
            Analysis: The analyzed metadata of the file.

        Raises:
            RuntimeError: If there's an error communicating with the OpenAI API.
        """
        try:
            if max_tokens is None:
                try:
                    max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", "50"))
                except ValueError as ve:
                    logger.error(
                        "Invalid OPENAI_MAX_TOKENS environment variable value: %s",
                        os.getenv("OPENAI_MAX_TOKENS")
                    )
                    raise ValueError("OPENAI_MAX_TOKENS must be an integer.") from ve

            functions = [
                {
                    "name": "parse_analysis",
                    "description": "Parses file content analysis into a structured format.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {"type": "string", "description": "File category"},
                            "vendor": {"type": "string", "description": "File vendor"},
                            "description": {"type": "string", "description": "File description"},
                            "date": {"type": "string", "description": "File date (optional)"}
                        },
                        "required": ["category", "vendor", "description"]
                    }
                }
            ]

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                functions=functions,
                function_call={"name": "parse_analysis"},
                max_tokens=max_tokens,
            )

            # Retrieve the structured output from the function call field
            function_call_resp = response.choices[0].message.function_call
            if not function_call_resp or not hasattr(function_call_resp, "arguments"):
                logger.error("Structured output not provided by API: %s", response)
                raise RuntimeError("Structured output not provided by API.")

            arguments = json.loads(function_call_resp.arguments)
            analysis = Analysis.parse_obj(arguments)
            return analysis
        except ValidationError as ve:
            logger.error(
                "Validation error while parsing Analysis: %s", ve, exc_info=True
            )
            raise RuntimeError("Validation error while parsing Analysis.") from ve
        except OpenAIError as e:
            logger.exception("Error communicating with OpenAI API.")
            raise RuntimeError("Error communicating with OpenAI API.") from e
