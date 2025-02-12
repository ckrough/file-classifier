from abc import ABC, abstractmethod
import os
import openai
from typing import TYPE_CHECKING
from src.ai_file_classifier.models import Analysis

if TYPE_CHECKING:
    from src.ai_file_classifier.models import Analysis


"""Module for AI Client Abstractions."""


class AIClient(ABC):
    """Abstract base class for AI clients."""

    @abstractmethod
    def analyze_content(
        self, system_prompt: str, user_prompt: str, model: str, max_tokens: int = 50
    ) -> "Analysis":
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

    def __init__(self):
        """Initialize the OpenAI client with the API key from environment variables."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        openai.api_key = api_key

    def analyze_content(
        self, system_prompt: str, user_prompt: str, model: str, max_tokens: int = 50
    ) -> "Analysis":
        """
        Analyze the content using OpenAI's ChatCompletion API.

        Args:
            system_prompt (str): The system prompt for the AI.
            user_prompt (str): The user prompt for the AI.
            model (str): The AI model to use.
            max_tokens (int): The maximum number of tokens for the response.

        Returns:
            Analysis: The analyzed metadata of the file.
        """
        try:
            response = openai.beta.chat.completions.parse(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format=Analysis,
                max_tokens=max_tokens,
            )

            analysis: Analysis = response.choices[0].message.parsed
            return analysis
        except Exception as e:
            raise RuntimeError(f"Error communicating with OpenAI API: {e}") from e
