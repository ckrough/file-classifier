import logging
import os
from pprint import pprint

from openai import OpenAI
from pydantic import BaseModel

from src.ai_file_classifier.prompt_loader import load_and_format_prompt
from src.ai_file_classifier.text_extractor import (extract_text_from_pdf,
                                                   extract_text_from_txt)


class Analysis(BaseModel):
    category: str
    vendor: str
    description: str
    date: str


def analyze_file_content(file_path, model):
    """
    Analyzes the content of a file to determine its context and purpose.
    """
    try:
        # Extract content based on file type
        if file_path.lower().endswith('.pdf'):
            content = extract_text_from_pdf(file_path)
        else:
            content = extract_text_from_txt(file_path)

        # Load prompts
        system_prompt = load_and_format_prompt(
            'prompts/file-analysis-system-prompt.txt'
        )

        user_prompt = load_and_format_prompt(
            'prompts/file-analysis-user-prompt.txt',
            filename=os.path.basename(file_path),
            content=content
        )

        # Make API request to analyze content
        client = OpenAI()
        completion = client.beta.chat.completions.parse(
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

        logging.debug(f"Completion response: {completion}")

        response = completion.choices[0].message

        if (response.refusal):
            raise (response.refusal)
        else:
            suggestion = response.parsed
            category = suggestion.category.lower().replace(' ', '-')
            vendor = suggestion.vendor.lower().replace(' ', '-')
            description = suggestion.description.lower().replace(' ', '-')
            date = suggestion.date if suggestion.date else ''
            suggested_name = (
                f"{vendor}-{category}-{description}{'-' + date if date else ''}"
            )
            return suggested_name, category
    except Exception as e:
        logging.error(f"Error analyzing file content: {e}", exc_info=True)
        return None, None
