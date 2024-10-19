import argparse
import logging
import os

import magic
import PyPDF2
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set your OpenAI API key here
OpenAI.api_key = ""

def extract_text_from_pdf(file_path):
    """
    Extracts text from a PDF file.
    """
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            content = ""
            for page in reader.pages:
                content += page.extract_text() + "\n"
        return content
    except Exception as e:
        logging.error(f"Error extracting text from PDF: {e}")
        return ""


def extract_text_from_txt(file_path):
    """
    Extracts text from a text file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        logging.error(f"Error extracting text from text file: {e}")
        return ""


def analyze_file_content(file_path):
    """
    Analyzes the content of a file to determine its context and purpose.
    """
    try:
        if file_path.lower().endswith('.pdf'):
            content = extract_text_from_pdf(file_path)
        else:
            content = extract_text_from_txt(file_path)

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
                    "content": f"Analyze the following content and filename to suggest a category, a vendor name, a short descriptive text for the file, and a prominent date in the content in YYYYMMDD format if available. The response should be in the format: category,vendor,description,date. The category should be one concise word that clearly represents the type of document. The vendor should be a single word representing the name of the company or entity relevant to the content. The description should be general, concise, and no more than three words, focusing on summarizing the main theme of the content without listing detailed items. The date should be in ISO 8601 format (YYYYMMDD) if there is a prominent date in the content, otherwise leave it blank. For example, if the content contains 'ACME Markets' and 'bananas, apples, milk', the category would be 'receipt', the vendor could be 'ACME', and the description would be 'groceries'. If a date is present such as 'April 5, 2023', the date should be returned as '20230405'. Use the filename as additional context if it provides useful information about the document.\n\nFilename: {os.path.basename(file_path)}\n\nContent:\n\n{content}\n\nSuggested category, vendor, description, and date:"
                }
            ],
        )
        suggestion = completion.choices[0].message.content.strip('"')
        category, vendor, description, date = map(str.strip, suggestion.split(',', 3))
        category = category.lower().replace(' ', '-')
        vendor = vendor.lower().replace(' ', '-')
        description = description.lower().replace(' ', '-')
        date = date if date else ''
        suggested_name = f"{vendor}-{category}-{description}{'-' + date if date else ''}"
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
        # Check if the file is a text file or a PDF based on its MIME type
        return file_type.startswith('text/') or file_type == 'application/pdf'
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
