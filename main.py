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
                        "content": "You are a helpful assistant that suggests suitable file names based on content."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze the following content and suggest a suitable name for the file:\n\n{content}\n\nSuggested file name:"
                    }
                ],
            )
            suggested_name = completion.choices[0].message.content
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
            # Get the directory and new file name with the same extension
            directory = os.path.dirname(file_path)
            file_extension = os.path.splitext(file_path)[1]
            new_file_path = os.path.join(directory, suggested_name + file_extension)
            try:
                os.rename(file_path, new_file_path)
                logging.info(f"File has been renamed to: {new_file_path}")
            except Exception as e:
                logging.error(f"Error renaming file: {e}")
        else:
            logging.info("File renaming was canceled by the user.")
    else:
        logging.error("Could not determine a suitable name for the file.")


if __name__ == "__main__":
    main()
