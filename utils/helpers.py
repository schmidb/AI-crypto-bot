import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

def save_to_json(data: Any, filename: str):
    """
    Save data to a JSON file
    
    Args:
        data: Data to save
        filename: Path to save the file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)

def load_from_json(filename: str) -> Any:
    """
    Load data from a JSON file
    
    Args:
        filename: Path to the JSON file
        
    Returns:
        Loaded data
    """
    if not os.path.exists(filename):
        return None
        
    with open(filename, 'r') as f:
        return json.load(f)

def calculate_profit_loss(buy_price: float, sell_price: float, quantity: float) -> Dict:
    """
    Calculate profit/loss from a trade
    
    Args:
        buy_price: Purchase price
        sell_price: Selling price
        quantity: Quantity traded
        
    Returns:
        Dictionary with profit/loss information
    """
    absolute_pl = (sell_price - buy_price) * quantity
    percentage_pl = ((sell_price - buy_price) / buy_price) * 100
    
    return {
        "absolute_pl": absolute_pl,
        "percentage_pl": percentage_pl,
        "buy_price": buy_price,
        "sell_price": sell_price,
        "quantity": quantity
    }

def format_currency(amount: float, currency: str = "USD", precision: int = 2) -> str:
    """
    Format a currency amount
    
    Args:
        amount: Amount to format
        currency: Currency code
        precision: Decimal precision
        
    Returns:
        Formatted currency string
    """
    if currency == "USD":
        return f"${amount:.{precision}f}"
    else:
        return f"{amount:.{precision}f} {currency}"

def get_timeframe_start_end(timeframe: str) -> tuple:
    """
    Get start and end times for a given timeframe
    
    Args:
        timeframe: Timeframe string (e.g., '1d', '7d', '1m', '3m', '1y')
        
    Returns:
        Tuple of (start_time, end_time) as datetime objects
    """
    end_time = datetime.utcnow()
    
    if timeframe.endswith('d'):
        days = int(timeframe[:-1])
        start_time = end_time - timedelta(days=days)
    elif timeframe.endswith('h'):
        hours = int(timeframe[:-1])
        start_time = end_time - timedelta(hours=hours)
    elif timeframe.endswith('m') and len(timeframe) > 1:
        months = int(timeframe[:-1])
        start_time = end_time - timedelta(days=30*months)
    elif timeframe.endswith('y'):
        years = int(timeframe[:-1])
        start_time = end_time - timedelta(days=365*years)
    else:
        # Default to 1 day
        start_time = end_time - timedelta(days=1)
        
    return start_time, end_time

def resample_ohlcv(df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """
    Resample OHLCV data to a different timeframe
    
    Args:
        df: DataFrame with OHLCV data
        timeframe: Target timeframe (e.g., '1H', '4H', '1D')
        
    Returns:
        Resampled DataFrame
    """
    # Ensure timestamp is the index and is datetime
    if 'timestamp' in df.columns:
        df = df.set_index('timestamp')
    
    # Resample
    resampled = df.resample(timeframe).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    
    # Reset index
    resampled = resampled.reset_index()
    
    return resampled

def get_granularity_string(timeframe: str) -> str:
    """
    Convert a timeframe string to Coinbase granularity string
    
    Args:
        timeframe: Timeframe string (e.g., '1h', '4h', '1d')
        
    Returns:
        Coinbase granularity string
    """
    timeframe = timeframe.lower()
    
    if timeframe == '1m':
        return 'ONE_MINUTE'
    elif timeframe == '5m':
        return 'FIVE_MINUTE'
    elif timeframe == '15m':
        return 'FIFTEEN_MINUTE'
    elif timeframe == '30m':
        return 'THIRTY_MINUTE'
    elif timeframe == '1h':
        return 'ONE_HOUR'
    elif timeframe == '2h':
        return 'TWO_HOUR'
    elif timeframe == '6h':
        return 'SIX_HOUR'
    elif timeframe == '1d':
        return 'ONE_DAY'
    else:
        # Default to 1 hour
        return 'ONE_HOUR'
