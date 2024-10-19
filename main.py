import os
import argparse
import openai
import magic

# Set your OpenAI API key here
openai.api_key = "YOUR_OPENAI_API_KEY"


def analyze_file_content(file_path):
    """
    Analyzes the content of a file to determine its context and purpose.
    """
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            # Use OpenAI's GPT model to analyze the file content
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that suggests suitable file names based on content."},
                    {"role": "user", "content": f"Analyze the following content and suggest a suitable name for the file:\n\n{
                        content}\n\nSuggested file name:"}
                ],
                max_tokens=50
            )
            suggested_name = response.choices[0].message['content'].strip()
            return suggested_name
    except Exception as e:
        print(f"Error reading file: {e}")
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
        print(f"Error determining file type: {e}")
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
        print(f"The file '{file_path}' does not exist.")
        return

    if not is_supported_filetype(file_path):
        print(f"The file '{file_path}' is not a supported file type.")
        return

    suggested_name = analyze_file_content(file_path)
    if suggested_name:
        print(f"Suggested name for the file: {suggested_name}")
        user_confirmation = input("Do you want to rename the file to this suggested name? (yes/no): ")
        if user_confirmation.lower() == 'yes':
            # Get the directory and new file name with the same extension
            directory = os.path.dirname(file_path)
            file_extension = os.path.splitext(file_path)[1]
            new_file_path = os.path.join(directory, suggested_name + file_extension)
            try:
                os.rename(file_path, new_file_path)
                print(f"File has been renamed to: {new_file_path}")
            except Exception as e:
                print(f"Error renaming file: {e}")
        else:
            print("File renaming was canceled by the user.")
    else:
        print("Could not determine a suitable name for the file.")


if __name__ == "__main__":
    main()
