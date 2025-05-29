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
from csv_utils import save_to_csv

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

    def get_condition_options(self):
        """Return available condition options"""
        return {
            '1': 'New',
            '2': 'Open Box',
            '3': 'Certified Refurbished',
            '4': 'Seller Refurbished',
            '5': 'Pre-owned',
            '6': 'For Parts or Not Working'
        }

    def get_available_filters(self, device_type):
        """Scrape available filter options from eBay search page"""
        try:
            # Search URL without filters
            url = f"{self.base_url}/sch/i.html?_nkw={device_type.replace(' ', '+')}&rt=nc"
            self.driver.get(url)
            
            # Wait for filters to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "x-refine__left__nav"))
            )
            
            time.sleep(2)  # Give extra time for filters to load
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            filter_options = {
                'color': [],
                'storage': [],
                'condition': self.get_condition_options()
            }
            
            # Find all filter sections
            filter_sections = soup.find_all('div', class_='x-refine__group')
            
            for section in filter_sections:
                header = section.find('h3', class_='x-refine__group__header')
                if not header:
                    continue
                    
                header_text = header.text.strip().lower()
                
                # Extract color options
                if 'color' in header_text:
                    options = section.find_all('span', class_='x-refine__multi-select-label')
                    filter_options['color'] = [opt.text.strip() for opt in options if opt.text.strip()]
                
                # Extract storage options
                elif any(word in header_text for word in ['storage', 'capacity', 'gb', 'tb']):
                    options = section.find_all('span', class_='x-refine__multi-select-label')
                    filter_options['storage'] = [opt.text.strip() for opt in options if opt.text.strip()]
            
            return filter_options
            
        except Exception as e:
            print(f"Error scraping filters: {str(e)}")
            return None

    def prompt_for_filters(self, device_type):
        """Prompt user for filter values based on device type with dynamic options"""
        filter_values = {
            'color': [],
            'storage': [],
            'condition': []
        }
        
        # Get available filter options
        print("\nFetching available filter options...")
        available_filters = self.get_available_filters(device_type)
        
        if not available_filters:
            print("Could not fetch filter options. Using basic filters.")
            return super().prompt_for_filters(device_type)
        
        print(f"\nPlease select from the available options for your {device_type}:")
        print("(For multiple selections, enter numbers separated by commas, e.g., '1,3,4')")
        
        # Handle color selection
        if available_filters['color']:
            print("\nAvailable colors:")
            for idx, color in enumerate(available_filters['color'], 1):
                print(f"{idx}: {color}")
            while True:
                value = input("Enter color number(s) (or press Enter to skip): ").strip()
                if not value:
                    break
                try:
                    # Handle multiple selections
                    indices = [int(idx.strip()) for idx in value.split(',')]
                    valid_indices = [idx for idx in indices if 1 <= idx <= len(available_filters['color'])]
                    if valid_indices:
                        filter_values['color'] = [available_filters['color'][idx-1] for idx in valid_indices]
                        break
                    print("No valid numbers entered, please try again.")
                except ValueError:
                    print("Please enter valid numbers separated by commas.")
        
        # Handle storage selection
        if available_filters['storage']:
            print("\nAvailable storage options:")
            for idx, storage in enumerate(available_filters['storage'], 1):
                print(f"{idx}: {storage}")
            while True:
                value = input("Enter storage number(s) (or press Enter to skip): ").strip()
                if not value:
                    break
                try:
                    indices = [int(idx.strip()) for idx in value.split(',')]
                    valid_indices = [idx for idx in indices if 1 <= idx <= len(available_filters['storage'])]
                    if valid_indices:
                        filter_values['storage'] = [available_filters['storage'][idx-1] for idx in valid_indices]
                        break
                    print("No valid numbers entered, please try again.")
                except ValueError:
                    print("Please enter valid numbers separated by commas.")
        
        # Handle condition selection
        print("\nAvailable conditions:")
        conditions = available_filters['condition']
        for key, value in conditions.items():
            print(f"{key}: {value}")
        while True:
            value = input("Enter condition number(s) (or press Enter to skip): ").strip()
            if not value:
                break
            try:
                # Handle multiple selections
                condition_numbers = [num.strip() for num in value.split(',')]
                valid_conditions = [conditions[num] for num in condition_numbers if num in conditions]
                if valid_conditions:
                    filter_values['condition'] = valid_conditions
                    break
                print("No valid numbers entered, please try again.")
            except ValueError:
                print("Please enter valid numbers separated by commas.")
        
        return filter_values

    def build_search_url(self, device_type, filters):
        """Build eBay search URL with filters"""
        # Construct the base search query
        search_terms = [device_type]
        
        # Add non-condition filter values to search terms
        for filter_type, values in filters.items():
            if filter_type != 'condition' and values:
                if isinstance(values, list):
                    search_terms.extend(values)
                else:
                    search_terms.append(values)
        
        # Join all search terms
        search_query = " ".join(search_terms).replace(" ", "+")
        
        # Build the URL with proper eBay parameters
        url = f"{self.base_url}/sch/i.html"
        url += f"?_nkw={search_query}"
        url += "&LH_Sold=1"  # Show sold items
        url += "&LH_Complete=1"  # Show completed items
        url += "&rt=nc"  # No category constraints
        
        # Add condition parameters if present
        if 'condition' in filters and filters['condition']:
            condition_params = []
            for condition in filters['condition']:
                if condition == 'New':
                    condition_params.append("1000")
                elif condition == 'Open Box':
                    condition_params.append("1500")
                elif condition == 'Certified Refurbished':
                    condition_params.append("2000")
                elif condition == 'Seller Refurbished':
                    condition_params.append("2500")
                elif condition == 'Pre-owned':
                    condition_params.append("3000")
                elif condition == 'For Parts or Not Working':
                    condition_params.append("7000")
            
            if condition_params:
                url += f"&LH_ItemCondition={'|'.join(condition_params)}"
        
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
        condition_pattern = r'(New|Open Box|Certified Refurbished|Seller Refurbished|Pre-owned|For Parts or Not Working)'
        
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
        print(f"\nSearching URL: {search_url}")
        
        try:
            self.driver.get(search_url)
            
            # Wait for the items to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "s-item__title"))
            )
            
            # Scroll to load more items
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Try different item selectors
            items = soup.find_all('div', class_='s-item__info clearfix')
            if not items:
                items = soup.find_all('div', class_='s-item__info')
            if not items:
                items = soup.find_all('li', class_='s-item')
                
            print(f"\nFound {len(items)} items")
            
            results = []
            for item in items:
                if item is None:
                    continue
                    
                title_elem = item.find('span', class_='s-item__title') or item.find('div', class_='s-item__title')
                price_elem = item.find('span', class_='s-item__price') or item.find('div', class_='s-item__price')
                
                if not title_elem or not price_elem:
                    continue
                    
                title = title_elem.text.strip()
                if title.lower() == 'shop on ebay':
                    continue
                    
                price = self.extract_price(price_elem.text.strip())
                
                if title and price:
                    item_data = {
                        'name': title,
                        'price': price,
                        **self.extract_attributes(title)
                    }
                    results.append(item_data)
            
            df = pd.DataFrame(results)
            
            if len(df) > 0:
                # Calculate statistics for the last 30 items
                recent_df = df.head(30)
                stats = {
                    'count': len(recent_df),
                    'average_price': round(recent_df['price'].mean(), 2),
                    'min_price': round(recent_df['price'].min(), 2),
                    'max_price': round(recent_df['price'].max(), 2)
                }
                
                print("\nPrice Statistics (Last 30 Sales):")
                print(f"Number of items analyzed: {stats['count']}")
                print(f"Average Price: ${stats['average_price']}")
                print(f"Price Range: ${stats['min_price']} - ${stats['max_price']}")
                
                # Save full results to CSV
                save_to_csv(df, device_type, filters)
                
            return df
            
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
        
        if len(df) == 0:
            print("No results found matching your criteria.")
            
    finally:
        scraper.close()

if __name__ == "__main__":
    main() 