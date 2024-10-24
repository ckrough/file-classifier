import logging
import os
from typing import Tuple, Optional
from openai import OpenAI

from pydantic import BaseModel

from src.ai_file_classifier.prompt_loader import load_and_format_prompt
from src.ai_file_classifier.text_extractor import (extract_text_from_pdf,
                                                   extract_text_from_txt)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Analysis(BaseModel):
    category: str
    vendor: str
    description: str
    date: Optional[str]


def analyze_file_content(file_path: str, model: str, client: OpenAI) -> \
        Tuple[Optional[str], Optional[str], Optional[str], Optional[str],
              Optional[str]]:
    """
    Analyzes the content of a file to determine its context and purpose.
    Returns suggested name, category, vendor, description, and date.
    """
    try:
        # Extract content based on file type
        if file_path.lower().endswith('.pdf'):
            content: str = extract_text_from_pdf(file_path)
        else:
            content: str = extract_text_from_txt(file_path)

        # Load prompts
        system_prompt: str = load_and_format_prompt(
            'prompts/file-analysis-system-prompt.txt'
        )

        user_prompt: str = load_and_format_prompt(
            'prompts/file-analysis-user-prompt.txt',
            filename=os.path.basename(file_path),
            content=content
        )

        # Make API request to analyze content
        completion: OpenAI = client.beta.chat.completions.parse(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            response_format=Analysis,
            max_tokens=50
        )

        logger.debug(f"Completion response: {completion}")

        response: Analysis = completion.choices[0].message

        if hasattr(response, 'refusal') and response.refusal:
            raise ValueError(f"Refusal: {response.refusal}")
        else:
            suggestion: Analysis = response.parsed
            category: str = suggestion.category.lower().replace(' ', '-')
            vendor: str = suggestion.vendor.lower().replace(' ', '-')
            description: str = suggestion.description.lower().replace(' ', '-')
            date: str = suggestion.date if suggestion.date else ''
            suggested_name: str = (
                f"{vendor}-{category}-{description}"
                f"{'-' + date if date else ''}"
            )
            return suggested_name, category, vendor, description, date
    except Exception as e:
        raise RuntimeError(f"Error analyzing file content: {e}") from e
