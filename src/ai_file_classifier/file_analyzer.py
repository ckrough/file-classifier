import logging
import os

from openai import OpenAI

from src.ai_file_classifier.prompt_loader import load_and_format_prompt
from src.ai_file_classifier.text_extractor import (extract_text_from_pdf,
                                                   extract_text_from_txt)


def analyze_file_content(file_path):
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
        completion = client.chat.completions.create(
            model="gpt-4",
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
        )
        suggestion = completion.choices[0].message.content.strip('"')
        category, vendor, description, date = map(
            str.strip, suggestion.split(',', 3)
        )
        category = category.lower().replace(' ', '-')
        vendor = vendor.lower().replace(' ', '-')
        description = description.lower().replace(' ', '-')
        date = date if date else ''
        suggested_name = (
            f"{vendor}-{category}-{description}{'-' + date if date else ''}"
        )
        return suggested_name
    except Exception as e:
        logging.error(f"Error analyzing file content: {e}")
        return None
