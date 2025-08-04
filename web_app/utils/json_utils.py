"""
JSON utilities for handling pandas DataFrames and Series
"""
import pandas as pd
import numpy as np
import json
from decimal import Decimal

def clean_for_json(obj):
    """
    Clean pandas objects for JSON serialization
    Handles NaN, Infinity, and other problematic values
    """
    if isinstance(obj, pd.DataFrame):
        # Replace NaN and inf values with None
        return obj.replace([np.inf, -np.inf], None).where(pd.notnull(obj), None)
    
    elif isinstance(obj, pd.Series):
        # Replace NaN and inf values with None
        return obj.replace([np.inf, -np.inf], None).where(pd.notnull(obj), None)
    
    elif isinstance(obj, dict):
        # Recursively clean dictionary values
        return {k: clean_for_json(v) for k, v in obj.items()}
    
    elif isinstance(obj, list):
        # Recursively clean list items
        return [clean_for_json(item) for item in obj]
    
    elif isinstance(obj, (np.integer, np.int64)):
        # Convert numpy integers to Python int
        return int(obj)
    
    elif isinstance(obj, (np.floating, np.float64)):
        # Convert numpy floats to Python float, handle NaN/inf
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    
    elif isinstance(obj, np.ndarray):
        # Convert numpy arrays to lists
        return clean_for_json(obj.tolist())
    
    elif isinstance(obj, Decimal):
        # Convert Decimal to float
        return float(obj)
    
    elif pd.isna(obj):
        # Handle pandas NA values
        return None
    
    else:
        # Return as-is for other types
        return obj


def dataframe_to_json_safe(df):
    """
    Convert DataFrame to JSON-safe dictionary
    """
    # First clean the dataframe
    df_clean = clean_for_json(df)
    
    # Convert to dict
    result = df_clean.to_dict('records')
    
    # Additional cleaning pass
    return clean_for_json(result)


def series_to_json_safe(series):
    """
    Convert Series to JSON-safe dictionary
    """
    # First clean the series
    series_clean = clean_for_json(series)
    
    # Convert to dict
    result = series_clean.to_dict()
    
    # Additional cleaning pass
    return clean_for_json(result)