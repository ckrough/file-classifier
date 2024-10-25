# File Classifier Application

## Overview
This application organizes and categorizes text and PDF files by analyzing their content. It suggests logical file names and optionally renames files in bulk based on the analysis results. The tool is designed to help users maintain a well-structured, easily navigable document storage system.

## Features
- **File Inventory**: Traverse specified directories to inventory all `.txt` and `.pdf` files.
- **AI-Powered Analysis**: Analyze file content using AI to suggest a suitable name, category, vendor, and description for each document.
- **Cache Management**: Uses an SQLite cache to store file metadata, avoiding redundant analysis.
- **User Approval**: Present suggested changes to users for approval before renaming files in bulk.
- **Batch Renaming**: Automatically rename files in accordance with the suggested naming convention.

## Setup Instructions

1. **Clone the Repository**:
   ```sh
   git clone <repository_url>
   cd <repository_directory>
   ```

2. **Create a Virtual Environment**:
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Dependencies**:
   ```sh
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   Create a `.env` file in the root directory with the following variables:
   ```env
   AI_MODEL=gpt-4o-mini
   DEBUG_MODE=false
   OPENAI_API_KEY=<your_openai_api_key>
   ```

## Usage

### Command Line Arguments
The application supports command-line arguments for specifying the file or directory to be analyzed.

- **Analyze a Single File**:
  ```sh
  python main.py <path_to_file>
  ```

- **Analyze an Entire Directory**:
  ```sh
  python main.py <path_to_directory>
  ```

- **Automatically Rename Files**:
  Add the `--auto-rename` flag to automatically rename the files without user confirmation:
  ```sh
  python main.py <path_to_directory> --auto-rename
  ```

## How It Works
1. **File Inventory**: The application inventories all `.txt` and `.pdf` files in the specified directory, storing their metadata in a cache.
2. **AI Analysis**: File content is analyzed using an AI model, which suggests appropriate names and categories.
3. **User Interaction**: The user is presented with suggested changes and can choose to accept or reject them.
4. **Renaming Files**: Approved suggestions are applied, and files are renamed accordingly.

## License

MIT License

Copyright (c) [2024] [Chris Krough]

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## Contact
For questions or issues, please reach out via the repository's Issues section.

