import argparse
import logging
import os

import magic
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set your OpenAI API key here
OpenAI.api_key = ""

def analyze_file_content(file_path):
    """
    Analyzes the content of a file to determine its context and purpose.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            client = OpenAI()
            completion = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that suggests suitable categories and descriptive text for file names based on content."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze the following content and suggest a category and a short descriptive text for the file. The response should be in the format: category,descriptive text. The category should be one concise word that clearly represents the type of document. The descriptive text should be general, concise, and no more than three words, focusing on summarizing the main theme of the content without listing detailed items. For example, if the content contains 'bananas, apples, milk', the category would be 'receipt' and the description would be 'groceries'.\n\n{content}\n\nSuggested category and description:"
                    }
                ],
            )
            suggestion = completion.choices[0].message.content.strip('"')
            category, description = map(str.strip, suggestion.split(',', 1))
            category = category.lower().replace(' ', '-')
            description = description.lower().replace(' ', '-')
            suggested_name = f"{category}-{description}"
        return suggested_name
    except Exception as e:
        logging.error(f"Error reading file: {e}")
        return None


def is_supported_filetype(file_path):
    """
    Checks if the specified file is a supported type.
    """
    try:
        file_type = magic.from_file(file_path, mime=True)
        # Check if the file is a text file based on its MIME type
        return file_type.startswith('text/')
    except Exception as e:
        logging.error(f"Error determining file type: {e}")
        return False


def get_user_arguments():
    """
    Parses and returns the user arguments specifying the file to be classified.
    """
    parser = argparse.ArgumentParser(description="Classify and rename a file based on its content.")
    parser.add_argument('file_path', type=str, help="Path to the target file.")
    return parser.parse_args()


def rename_file(file_path, suggested_name):
    """
    Renames the file to the suggested name if the user confirms.
    """
    directory = os.path.dirname(file_path)
    file_extension = os.path.splitext(file_path)[1]
    new_file_path = os.path.join(directory, suggested_name + file_extension)
    try:
        os.rename(file_path, new_file_path)
        logging.info(f"File has been renamed to: {new_file_path}")
    except Exception as e:
        logging.error(f"Error renaming file: {e}")


def main():
    args = get_user_arguments()
    file_path = args.file_path

    if not os.path.isfile(file_path):
        logging.error(f"The file '{file_path}' does not exist.")
        return

    if not is_supported_filetype(file_path):
        logging.error(f"The file '{file_path}' is not a supported file type.")
        return

    suggested_name = analyze_file_content(file_path)
    if suggested_name:
        logging.info(f"Suggested name for the file: {suggested_name}")
        user_confirmation = input("Do you want to rename the file to this suggested name? (yes/no): ").strip().lower()
        if user_confirmation == 'yes':
            rename_file(file_path, suggested_name)
        else:
            logging.info("File renaming was canceled by the user.")
    else:
        logging.error("Could not determine a suitable name for the file.")


if __name__ == "__main__":
    main()
