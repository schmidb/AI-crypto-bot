import os
import pandas as pd
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class TaxReportGenerator:
    """
    Generates tax reports from trade history CSV files.
    """
    
    def __init__(self, trades_file: str = "logs/trade_history.csv"):
        """Initialize the tax report generator."""
        self.trades_file = trades_file
        logger.info(f"Tax report generator initialized with trades file: {trades_file}")
    
    def generate_report(self, output_file: str, tax_year: Optional[int] = None):
        """
        Generate a tax report Excel file from trade history.
        
        Args:
            output_file: Path to the output Excel file
            tax_year: Optional tax year to filter records
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if trades file exists
            if not os.path.exists(self.trades_file):
                logger.error(f"Trades file not found: {self.trades_file}")
                return False
            
            # Read trades file
            df = pd.read_csv(self.trades_file)
            
            # Filter by tax year if specified
            if tax_year is not None:
                df = df[df['tax_year'] == tax_year]
            
            if df.empty:
                logger.warning("No trades found for the specified criteria")
                return False
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            
            # Create a writer for Excel
            with pd.ExcelWriter(output_file) as writer:
                # Write the main trade records
                df.to_excel(writer, sheet_name='Trade History', index=False)
                
                # Create buys sheet
                buys = df[df['side'] == 'buy']
                if not buys.empty:
                    buys.to_excel(writer, sheet_name='Buys', index=False)
                
                # Create sells sheet
                sells = df[df['side'] == 'sell']
                if not sells.empty:
                    sells.to_excel(writer, sheet_name='Sells', index=False)
                
                # Create summary sheet
                summary = pd.DataFrame({
                    'Total Buys (USD)': [buys['value_usd'].sum() if not buys.empty else 0],
                    'Total Sells (USD)': [sells['value_usd'].sum() if not sells.empty else 0],
                    'Total Fees (USD)': [df['fee_usd'].sum()],
                    'Number of Trades': [len(df)],
                    'Tax Year': [tax_year if tax_year else 'All Years'],
                    'Report Generated': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
                })
                summary.to_excel(writer, sheet_name='Summary', index=False)
                
                # Create asset summary sheet
                asset_summary = df.groupby(['product_id', 'side']).agg({
                    'size': 'sum',
                    'value_usd': 'sum',
                    'fee_usd': 'sum'
                }).reset_index()
                
                if not asset_summary.empty:
                    asset_summary.to_excel(writer, sheet_name='Asset Summary', index=False)
            
            logger.info(f"Tax report exported to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error generating tax report: {e}")
            return False
