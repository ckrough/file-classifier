import logging
import os

from dotenv import load_dotenv

from src.ai_file_classifier.file_analyzer import analyze_file_content
from src.ai_file_classifier.file_inventory import (initialize_cache,
                                                   inventory_files)
from src.ai_file_classifier.logging_config import setup_logging
from src.ai_file_classifier.utils import (get_user_arguments,
                                          is_supported_filetype, rename_file)

# Load environment variables
load_dotenv()
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"

# Get logger instance

# Set your OpenAI API key here
OpenAI.api_key = ""

def main():
    setup_logging()
    logger = logging.getLogger('file-classifier')
    try:
        args = get_user_arguments()
        if args.file_path:
            file_path = args.file_path

            if not os.path.exists(file_path):
                logger.error(f"The file '{file_path}' does not exist.")
                return

            if not os.path.isfile(file_path):
                logger.error(f"The path '{file_path}' is not a file.")
                return

            if not is_supported_filetype(file_path):
                logger.error(
                    f"The file '{file_path}' is not a supported file type.")
                return

            suggested_name = analyze_file_content(file_path, AI_MODEL)
            if suggested_name:
                logger.info(f"Suggested name for the file: {suggested_name}")
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
                        logger.info("File renaming was canceled by the user.")
            else:
                logger.error(
                    "Could not determine a suitable name for the file.")
        elif args.directory:
            # Step 1: Inventory Files
            directory = args.directory
            initialize_cache()
            inventory_files(directory)

            # Step 2: Analyze Files
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if is_supported_filetype(file_path):
                        suggested_name = analyze_file_content(
                            file_path, AI_MODEL)
                        if suggested_name:
                            logger.info(f"Suggested name for the file: {
                                        suggested_name}")
                            if args.auto_rename:
                                rename_file(file_path, suggested_name)
                            else:
                                user_confirmation = input(
                                    f"Do you want to rename the file '{
                                        file}' to '{suggested_name}'? (yes/no): "
                                ).strip().lower()
                                if user_confirmation == 'yes':
                                    rename_file(file_path, suggested_name)
                                else:
                                    logger.info(
                                        "File renaming was canceled by the user.")
                        else:
                            logger.error(
                                "Could not determine a suitable name for the file.")
        else:
            logger.error(
                "Please provide either a --file-path or --directory argument.")

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)


if __name__ == "__main__":
    main()
