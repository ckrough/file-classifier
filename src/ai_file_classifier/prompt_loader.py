import logging


def load_and_format_prompt(file_path, **kwargs):
    """
    Loads a prompt from a file and formats it with the given keyword arguments.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            prompt = file.read()
            return prompt.format(**kwargs)
    except Exception as e:
        logging.error(f"Error loading or formatting prompt from file: {e}")
        return ""
