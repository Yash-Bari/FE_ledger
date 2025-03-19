# Student Data Extractor

A Streamlit web application that extracts student data from PDF result sheets and converts it to structured Excel format.

## Features

- Extract student information (PRN, Seat No, Name, Mother Name)
- Parse academic performance data (SGPA, Credits Earned, Total Credit Points)
- Extract subject-wise grades and marks (CCE, ESE, TW components)
- Generate organized Excel output with proper column formatting
- Visualize SGPA distribution and show basic statistics
- Simple and intuitive user interface

## Installation

1. Clone this repository or download the source code
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:

```bash
streamlit run appv3.py
```

2. Open the web interface (usually at http://localhost:8501)
3. Upload your PDF result file
4. Click "Process PDF" button
5. View the results and download the Excel file

## Requirements

- Python 3.7+
- See requirements.txt for all Python dependencies

## File Structure

- `appv3.py`: Main Streamlit application with UI components
- `pdf_extractor.py`: Backend for PDF parsing and data extraction
- `debug_utils.py`: Utilities for debugging and logging

## Troubleshooting

If you encounter any issues:
- Check the logs folder for detailed error logs
- Make sure the PDF file is properly formatted
- Verify that all dependencies are installed correctly 