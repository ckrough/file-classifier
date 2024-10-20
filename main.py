import logging
import os

from src.ai_file_classifier.file_analyzer import analyze_file_content
from src.ai_file_classifier.utils import (get_user_arguments,
                                          is_supported_filetype, rename_file)

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Set your OpenAI API key here
OpenAI.api_key = ""

def main():
    try:
        args = get_user_arguments()
        file_path = args.file_path

        if not os.path.exists(file_path):
            logging.error(f"The file '{file_path}' does not exist.")
            return

        if not os.path.isfile(file_path):
            logging.error(f"The path '{file_path}' is not a file.")
            return

        if not is_supported_filetype(file_path):
            logging.error(
                f"The file '{file_path}' is not a supported file type.")
            return

        suggested_name = analyze_file_content(file_path)
        if suggested_name:
            logging.info(f"Suggested name for the file: {suggested_name}")
            if args.auto_rename:
                rename_file(file_path, suggested_name)
            else:
                user_confirmation = input(
                    "Do you want to rename the file? (yes/no): "
                ).strip().lower()
                while user_confirmation not in ['yes', 'no']:
                    user_confirmation = input(
                        "Please enter 'yes' or 'no': ").strip().lower()
                if user_confirmation == 'yes':
                    rename_file(file_path, suggested_name)
                else:
                    logging.info("File renaming was canceled by the user.")
        else:
            logging.error("Could not determine a suitable name for the file.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)


if __name__ == "__main__":
    main()
