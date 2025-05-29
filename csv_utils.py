import pandas as pd
from datetime import datetime

def save_to_csv(df, device_type, filters=None):
    """
    Save the DataFrame to a CSV file with timestamp
    """
    # Create timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create filename with device type and timestamp
    base_filename = f"{device_type}_sold_items_{timestamp}.csv"
    
    # Save to CSV
    df.to_csv(base_filename, index=False)
    print(f"\nDetailed results have been saved to {base_filename}")
    
def load_recent_results(device_type):
    """
    Load the most recent CSV file for a given device type
    """
    try:
        import glob
        import os
        
        # Find all matching CSV files
        files = glob.glob(f"{device_type}_sold_items_*.csv")
        
        if not files:
            return None
            
        # Get the most recent file
        latest_file = max(files, key=os.path.getctime)
        
        # Load and return the DataFrame
        return pd.read_csv(latest_file)
    except Exception as e:
        print(f"Error loading recent results: {str(e)}")
        return None 