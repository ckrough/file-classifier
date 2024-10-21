import argparse
import logging
import os

logger = logging.getLogger(__name__)


def get_user_arguments():
    """
    Parses command line arguments provided by the user.
    """
    parser = argparse.ArgumentParser(description="File Analyzer Application")
    parser.add_argument(
        "file_path", type=str, help="Path to the file to be analyzed"
    )
    parser.add_argument(
        "--auto-rename", action="store_true", help="Always rename the file"
    )
    return parser.parse_args()


def is_supported_filetype(file_path):
    """
    Validates if the specified file is a supported type.
    """
    supported_mimetypes = ["text/plain", "application/pdf"]
    try:
        import magic
        mime = magic.Magic(mime=True)
        mimetype = mime.from_file(file_path)
        logger.debug(f"Detected MIME type for file '{file_path}': {mimetype}")
        return mimetype in supported_mimetypes
    except Exception as e:
        logger.error(f"Error detecting MIME type for file '{
                     file_path}': {e}", exc_info=True)
        return False


def rename_file(file_path, new_name):
    """
    Renames the specified file to the new name, preserving the file extension.
    """
    try:
        base, ext = os.path.splitext(file_path)
        directory = os.path.dirname(file_path)
        new_path = os.path.join(directory, f"{new_name}{ext}")
        os.rename(file_path, new_path)
        logger.info(f"File '{file_path}' renamed to '{new_path}'")
    except Exception as e:
        logger.error(f"Error renaming file '{file_path}' to '{
                     new_name}': {e}", exc_info=True)
