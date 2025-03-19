# debug_utils.py
import pandas as pd
import sys
import traceback
import os
import logging
from datetime import datetime

# Set up logging
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"app_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    filename=log_file,
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def setup_exception_handler():
    """Set up a global exception handler to log unhandled exceptions"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Let keyboard interrupts through
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
    sys.excepthook = handle_exception

def debug_dataframe(df, description="DataFrame"):
    """Log detailed information about a DataFrame"""
    logging.debug(f"--- {description} Debug Info ---")
    logging.debug(f"Shape: {df.shape}")
    logging.debug(f"Columns: {df.columns.tolist()}")
    logging.debug(f"Data types: {df.dtypes}")
    
    # Check for problematic values
    logging.debug("Checking for NaN values:")
    nan_counts = df.isna().sum()
    logging.debug(nan_counts[nan_counts > 0])
    
    # Check for specific columns
    if 'SGPA' in df.columns:
        logging.debug(f"SGPA column values (first 10): {df['SGPA'].head(10).tolist()}")
        logging.debug(f"SGPA unique values: {df['SGPA'].unique()}")
    
    # Check for object columns that should be numeric
    for col in df.select_dtypes(include=['object']).columns:
        if col.endswith('_GRD_PNT') or col.endswith('_CRD_PNT') or col == 'SGPA':
            logging.debug(f"Column {col} unique values: {df[col].unique()}")

def debug_function(func):
    """Decorator to debug a function's execution"""
    def wrapper(*args, **kwargs):
        logging.debug(f"Calling function: {func.__name__}")
        logging.debug(f"Arguments: {args}")
        logging.debug(f"Keyword arguments: {kwargs}")
        try:
            result = func(*args, **kwargs)
            logging.debug(f"Function {func.__name__} completed successfully")
            return result
        except Exception as e:
            logging.error(f"Error in function {func.__name__}: {str(e)}")
            logging.error(traceback.format_exc())
            raise
    return wrapper

# Function to analyze SGPA column
def analyze_sgpa_column(df):
    """Analyze the SGPA column for potential issues"""
    if 'SGPA' not in df.columns:
        return "SGPA column not found"
    
    sgpa_values = df['SGPA'].tolist()
    analysis = {
        "total_values": len(sgpa_values),
        "unique_values": df['SGPA'].nunique(),
        "sample_values": df['SGPA'].head(10).tolist(),
        "data_type": str(df['SGPA'].dtype),
        "non_numeric_values": [],
        "problematic_values": []
    }
    
    for value in df['SGPA'].unique():
        try:
            float(value)
        except (ValueError, TypeError):
            if value not in (None, pd.NA, "-----", "N/A"):
                analysis["non_numeric_values"].append(value)
    
    return analysis