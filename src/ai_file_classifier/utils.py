import argparse
import logging
import os

import magic


def is_supported_filetype(file_path):
    """
    Checks if the specified file is a supported type.
    """
    try:
        file_type = magic.from_file(file_path, mime=True)
        # Check if the file is a text file or a PDF based on its MIME type
        return file_type.startswith('text/') or file_type == 'application/pdf'
    except Exception as e:
        logging.error(f"Error determining file type: {e}")
        return False


def get_user_arguments():
    """
    Parses and returns the user arguments specifying the file to be classified.
    """
    parser = argparse.ArgumentParser(
        description="Classify and rename a file based on its content."
    )
    parser.add_argument(
        '--file-path', type=str, required=True,
        help="Path to the target file."
    )
    parser.add_argument(
        '--auto-rename', action='store_true',
        help="Automatically rename the file without user confirmation."
    )
    return parser.parse_args()


def rename_file(file_path, suggested_name):
    """
    Renames the file to the suggested name.
    """
    directory = os.path.dirname(file_path)
    file_extension = os.path.splitext(file_path)[1]
    new_file_path = os.path.join(directory, suggested_name + file_extension)
    try:
        os.rename(file_path, new_file_path)
        logging.info(f"File has been renamed to: {new_file_path}")
    except Exception as e:
        logging.error(f"Error renaming file: {e}")
