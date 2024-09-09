# OSHA Inspection Data Scraper

This project is a set of Python scripts designed to scrape inspection data from the OSHA (Occupational Safety and Health Administration) website. The program can extract inspection numbers, details, and other relevant data using web scraping techniques, such as BeautifulSoup and Selenium.

## Features

- Scrapes data such as "Inspection Nr", "Report ID", "Date Opened", and violation summaries.
- Supports both batch and individual scraping modes for efficiency.
- Stores the scraped data in Excel and text formats.
- Includes logging for easy debugging and monitoring of the scraping process.

## Prerequisites

To use this project, ensure you have the following:

1. **Python 3.8+**
2. **Required Python Packages:**
    - requests
    - beautifulsoup4
    - selenium
    - webdriver-manager
    - tqdm
    - pandas

You can install all dependencies using the following command:

```bash
$ pip install -r requirements.txt
```

3. **ChromeDriver:** The project uses Chrome as the default browser. ChromeDriver should be installed via `webdriver_manager` automatically.

## Files in the Project

- `inspection_bs4.py`: Scrapes inspection numbers using BeautifulSoup and stores the data in logs. This script is configured to handle smaller batches of data efficiently.
- `inspection_selenium.py`: Uses Selenium to scrape OSHA inspection data by simulating a browser. It allows processing larger batches of data and extracts inspection details.
- `summary.py`: Extracts "Summary Nrs" from HTML files and saves them into a text file for further processing.
- `utils.py`: Contains utility functions to assist with reading files, fetching inspection numbers, and handling HTML data.
- `inspection_detail.py`: Retrieves detailed information about specific inspections from OSHA by navigating the website via Selenium.
- `Summary_Nrs.txt`: A sample file containing a list of Summary Nrs to process.

## Usage

### 1. Extract Summary Numbers

To extract summary numbers from HTML files, run:

```bash
$ python summary.py --directory /path/to/html/files
```

### 2. Scrape Inspection Numbers

To scrape inspection numbers based on the summary numbers, you can use:

```bash
$ python inspection_bs4.py --file Summary_Nrs.txt
```

### 3. Scrape Detailed Inspection Information

To scrape detailed inspection data for specific inspection numbers, run:

```bash
$ python inspection_detail.py --input-file_path Summary_Nrs.txt
```

### Command Line Options

- `--directory` or `-D`: Specifies the directory containing HTML files (used in `summary.py`).
- `--file` or `-F`: Specifies the file containing the list of Summary Nrs (used in `inspection_bs4.py`).
- `--input-file_path` or `-I`: Path to the file containing the list of Summary Nrs (used in `inspection_detail.py`).

## Logging

Logs are automatically created and stored in the `logs/` directory. The logging format includes timestamps and relevant information about the operations being performed.

## Output

The output data is saved in the following formats:

- **Text Files:** Inspection numbers are saved in .txt files.
- **Excel Files:** Detailed inspection data is saved in .xlsx files.

## License

This project is licensed under the MIT License.

## Acknowledgements

- This project uses data provided by OSHA (Occupational Safety and Health Administration).
- Web scraping is performed using the BeautifulSoup and Selenium libraries.

---

## Author

Created by [@pikaybh](https://github.com/pikaybh)
