# eBay Electronics Scraper

This is a Python-based web scraper that helps you gather information about recently sold electronic devices on eBay. The scraper allows you to search for specific types of devices and filter results based on various attributes like storage, color, and condition.

## Features

- Search for any electronic device type (phones, laptops, tablets, etc.)
- Filter results based on device-specific attributes
- Extracts product names, selling prices, and relevant attributes
- Saves results to a CSV file
- Supports headless browsing

## Installation

1. Make sure you have Python 3.7+ installed
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the scraper:
   ```bash
   python ebay_scraper.py
   ```

2. Follow the prompts:
   - Enter the type of electronic device you're looking for
   - Provide values for the suggested filters (or press Enter to skip)

3. The scraper will:
   - Search eBay for recently sold items matching your criteria
   - Display the results in the console
   - Save the results to a CSV file named `[device_type]_sold_items.csv`

## Supported Device Types

The scraper has specialized filters for:
- Phones (storage, color, condition)
- Laptops (processor, RAM, storage, condition)
- Tablets (storage, color, condition)
- Smartwatches (color, condition)
- Cameras (type, resolution, condition)

For other device types, it will default to basic filtering options.

## Notes

- The scraper uses Chrome in headless mode, so you don't need to have a browser window open
- Results are limited to the 50 most recent sold items to maintain performance
- Make sure you have a stable internet connection while running the scraper
