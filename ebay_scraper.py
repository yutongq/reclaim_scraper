import requests
from bs4 import BeautifulSoup
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import sys
import os
import platform

class EbayElectronicsScraper:
    def __init__(self):
        self.base_url = "https://www.ebay.com"
        self.setup_driver()
        
    def setup_driver(self):
        """Set up Chrome driver with appropriate options"""
        try:
            options = uc.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # Create undetected Chrome driver
            self.driver = uc.Chrome(
                options=options,
                driver_executable_path=None,  # Will be downloaded automatically
                browser_executable_path=None,  # Will use system Chrome
            )
            
            # Set window size for headless mode
            self.driver.set_window_size(1920, 1080)
        except Exception as e:
            print(f"Error setting up Chrome driver: {str(e)}")
            sys.exit(1)

    def get_device_filters(self, device_type):
        """Return appropriate filters based on device type"""
        filters = {
            'phone': ['storage', 'color', 'condition'],
            'laptop': ['processor', 'ram', 'storage', 'condition'],
            'tablet': ['storage', 'color', 'condition'],
            'smartwatch': ['color', 'condition'],
            'camera': ['type', 'resolution', 'condition']
        }
        return filters.get(device_type.lower(), ['condition'])

    def prompt_for_filters(self, device_type):
        """Prompt user for filter values based on device type"""
        filters = self.get_device_filters(device_type)
        filter_values = {}
        
        print(f"\nPlease provide the following details for your {device_type}:")
        for filter_type in filters:
            value = input(f"Enter desired {filter_type} (press Enter to skip): ").strip()
            if value:
                filter_values[filter_type] = value
        
        return filter_values

    def build_search_url(self, device_type, filters):
        """Build eBay search URL with filters"""
        # Construct the base search query
        search_terms = [device_type]
        
        # Add filter values to search terms
        for filter_type, value in filters.items():
            if value:
                search_terms.append(value)
        
        # Join all search terms
        search_query = " ".join(search_terms).replace(" ", "+")
        
        # Build the URL with proper eBay parameters
        url = f"{self.base_url}/sch/i.html"
        url += f"?_nkw={search_query}"
        url += "&LH_Sold=1"  # Show sold items
        url += "&LH_Complete=1"  # Show completed items
        url += "&rt=nc"  # No category constraints
        url += "&LH_BIN=1"  # Buy It Now items
        
        return url

    def extract_price(self, price_text):
        """Extract numerical price from price text"""
        if not price_text:
            return None
        price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
        if price_match:
            return float(price_match.group(1).replace(',', ''))
        return None

    def extract_attributes(self, description):
        """Extract relevant attributes from item description"""
        attributes = {}
        
        # Common patterns to look for
        storage_pattern = r'(\d+)\s*(GB|TB)'
        color_pattern = r'(Black|White|Gold|Silver|Gray|Rose Gold|Blue|Red)'
        condition_pattern = r'(New|Pre-owned|Refurbished|Used)'
        
        # Extract storage
        storage_match = re.search(storage_pattern, description, re.IGNORECASE)
        if storage_match:
            attributes['storage'] = storage_match.group()
            
        # Extract color
        color_match = re.search(color_pattern, description, re.IGNORECASE)
        if color_match:
            attributes['color'] = color_match.group(1)
            
        # Extract condition
        condition_match = re.search(condition_pattern, description, re.IGNORECASE)
        if condition_match:
            attributes['condition'] = condition_match.group(1)
            
        return attributes

    def scrape_sold_items(self, device_type, filters=None):
        """Scrape eBay for sold items matching the criteria"""
        if filters is None:
            filters = {}
            
        search_url = self.build_search_url(device_type, filters)
        print(f"\nSearching URL: {search_url}")  # Debug print
        
        try:
            self.driver.get(search_url)
            
            # Wait for the items to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "s-item__title"))
            )
            
            # Scroll to load more items
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # Increased wait time
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Try different item selectors
            items = soup.find_all('div', class_='s-item__info clearfix')
            if not items:
                items = soup.find_all('div', class_='s-item__info')
            if not items:
                items = soup.find_all('li', class_='s-item')
                
            print(f"\nFound {len(items)} items")  # Debug print
            
            results = []
            for item in items:
                if item is None:
                    continue
                    
                title_elem = item.find('span', class_='s-item__title') or item.find('div', class_='s-item__title')
                price_elem = item.find('span', class_='s-item__price') or item.find('div', class_='s-item__price')
                
                if not title_elem or not price_elem:
                    continue
                    
                title = title_elem.text.strip()
                if title.lower() == 'shop on ebay':  # Skip the first dummy item
                    continue
                    
                price = self.extract_price(price_elem.text.strip())
                
                if title and price:
                    item_data = {
                        'name': title,
                        'price': price,
                        **self.extract_attributes(title)
                    }
                    results.append(item_data)
            
            print(f"\nProcessed {len(results)} valid items")  # Debug print
            return pd.DataFrame(results)
            
        except Exception as e:
            print(f"Error during scraping: {str(e)}")
            return pd.DataFrame()

    def close(self):
        """Close the browser"""
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass

def main():
    scraper = EbayElectronicsScraper()
    
    try:
        # Get device type from user
        device_type = input("Enter the electronic device type (e.g., phone, laptop, tablet): ").strip()
        
        # Get filters from user
        filters = scraper.prompt_for_filters(device_type)
        
        # Scrape data
        print("\nScraping eBay for sold items... This may take a moment.")
        df = scraper.scrape_sold_items(device_type, filters)
        
        # Display results
        if len(df) > 0:
            print("\nResults found:")
            print(df.to_string(index=False))
            
            # Save to CSV
            filename = f"{device_type}_sold_items.csv"
            df.to_csv(filename, index=False)
            print(f"\nResults have been saved to {filename}")
        else:
            print("No results found matching your criteria.")
            
    finally:
        scraper.close()

if __name__ == "__main__":
    main() 