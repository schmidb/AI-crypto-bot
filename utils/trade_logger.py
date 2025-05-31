import os
import csv
import logging
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TradeLogger:
    """
    Logs trading activities to CSV files for record keeping and tax reporting.
    """
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize the trade logger."""
        self.log_dir = log_dir
        self.trades_file = os.path.join(log_dir, "trade_history.csv")
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Initialize log file with headers if it doesn't exist
        self._initialize_trades_file()
        
        logger.info(f"Trade logger initialized. Logs will be saved to {log_dir}")
    
    def _initialize_trades_file(self):
        """Initialize the trades CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.trades_file):
            with open(self.trades_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 
                    'trade_id', 
                    'product_id', 
                    'side', 
                    'price', 
                    'size', 
                    'value_usd',
                    'fee_usd',
                    'cost_basis_usd',
                    'tax_year'
                ])
            logger.info(f"Created new trades log file: {self.trades_file}")
    
    def log_trade(self, trade_data: Dict[str, Any]):
        """Log a trade to the CSV file."""
        try:
            timestamp = trade_data.get('timestamp', datetime.now().isoformat())
            dt = datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else timestamp
            tax_year = dt.year
            
            # Calculate values
            price = float(trade_data.get('price', 0.0))
            size = float(trade_data.get('size', 0.0))
            value_usd = float(trade_data.get('value_usd', price * size))
            fee_usd = float(trade_data.get('fee_usd', 0.0))
            cost_basis_usd = value_usd + fee_usd
            
            with open(self.trades_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    trade_data.get('trade_id', ''),
                    trade_data.get('product_id', ''),
                    trade_data.get('side', ''),  # buy or sell
                    price,
                    size,
                    value_usd,
                    fee_usd,
                    cost_basis_usd,
                    tax_year
                ])
            
            logger.info(f"Logged trade: {trade_data.get('side')} {size} {trade_data.get('product_id')} at ${price}")
            return True
        except Exception as e:
            logger.error(f"Error logging trade: {e}")
            return False
