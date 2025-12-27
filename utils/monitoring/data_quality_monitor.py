"""
Data Quality Monitor

Production utility to validate data quality and detect issues before they affect trading.
Can be used as a decorator or standalone validator.
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from functools import wraps


class DataQualityError(Exception):
    """Custom exception for data quality issues."""
    pass


class DataQualityMonitor:
    """Monitor and validate data quality across the trading system."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.validation_errors = []
        self.warnings = []
    
    def validate_market_data(self, market_data: Dict) -> Tuple[bool, List[str]]:
        """
        Validate market data quality.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not isinstance(market_data, dict):
            errors.append(f"Market data must be dict, got {type(market_data)}")
            return False, errors
        
        # Validate price
        if 'price' in market_data:
            price_errors = self._validate_price(market_data['price'], 'market_data.price')
            errors.extend(price_errors)
        else:
            errors.append("Missing required field: price")
        
        # Validate volume
        if 'volume' in market_data:
            volume_errors = self._validate_volume_data(market_data['volume'])
            errors.extend(volume_errors)
        
        # Validate price changes
        if 'price_changes' in market_data:
            price_change_errors = self._validate_price_changes(market_data['price_changes'])
            errors.extend(price_change_errors)
        
        # Validate timestamp if present
        if 'timestamp' in market_data:
            timestamp_errors = self._validate_timestamp(market_data['timestamp'])
            errors.extend(timestamp_errors)
        
        return len(errors) == 0, errors
    
    def validate_technical_indicators(self, indicators: Dict) -> Tuple[bool, List[str]]:
        """
        Validate technical indicators quality.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not isinstance(indicators, dict):
            errors.append(f"Technical indicators must be dict, got {type(indicators)}")
            return False, errors
        
        # Validate RSI
        if 'rsi' in indicators:
            rsi_errors = self._validate_rsi(indicators['rsi'])
            errors.extend(rsi_errors)
        
        # Validate MACD
        if 'macd' in indicators:
            macd_errors = self._validate_macd(indicators['macd'])
            errors.extend(macd_errors)
        
        # Validate Bollinger Bands
        bb_errors = self._validate_bollinger_bands(indicators)
        errors.extend(bb_errors)
        
        # Validate current price
        if 'current_price' in indicators:
            price_errors = self._validate_price(indicators['current_price'], 'current_price')
            errors.extend(price_errors)
        
        return len(errors) == 0, errors
    
    def validate_portfolio_data(self, portfolio: Dict) -> Tuple[bool, List[str]]:
        """
        Validate portfolio data quality.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not isinstance(portfolio, dict):
            errors.append(f"Portfolio must be dict, got {type(portfolio)}")
            return False, errors
        
        total_value = 0
        
        for currency, data in portfolio.items():
            if not isinstance(data, dict):
                errors.append(f"Portfolio entry for {currency} must be dict, got {type(data)}")
                continue
            
            # Validate amount
            if 'amount' not in data:
                errors.append(f"Missing amount for {currency}")
                continue
            
            amount_errors = self._validate_amount(data['amount'], f"{currency}.amount")
            errors.extend(amount_errors)
            
            # Validate price
            if 'price' not in data:
                errors.append(f"Missing price for {currency}")
                continue
            
            price_errors = self._validate_price(data['price'], f"{currency}.price")
            errors.extend(price_errors)
            
            # Calculate value for allocation check
            if len(amount_errors) == 0 and len(price_errors) == 0:
                total_value += data['amount'] * data['price']
        
        # Validate minimum EUR balance for trading
        if 'EUR' in portfolio and isinstance(portfolio['EUR'], dict):
            eur_amount = portfolio['EUR'].get('amount', 0)
            if eur_amount < 50:
                errors.append(f"EUR balance too low for trading: €{eur_amount} (minimum: €50)")
        
        # Validate total portfolio value
        if total_value <= 0:
            errors.append(f"Total portfolio value must be positive: €{total_value}")
        
        return len(errors) == 0, errors
    
    def _validate_price(self, price: Any, field_name: str) -> List[str]:
        """Validate a price value."""
        errors = []
        
        if not isinstance(price, (int, float)):
            errors.append(f"{field_name} must be numeric, got {type(price)}")
            return errors
        
        if np.isnan(price):
            errors.append(f"{field_name} cannot be NaN")
        elif np.isinf(price):
            errors.append(f"{field_name} cannot be infinite")
        elif price <= 0:
            errors.append(f"{field_name} must be positive: {price}")
        elif price > 1000000:
            errors.append(f"{field_name} seems unreasonably high: {price}")
        
        return errors
    
    def _validate_amount(self, amount: Any, field_name: str) -> List[str]:
        """Validate an amount value."""
        errors = []
        
        if not isinstance(amount, (int, float)):
            errors.append(f"{field_name} must be numeric, got {type(amount)}")
            return errors
        
        if np.isnan(amount):
            errors.append(f"{field_name} cannot be NaN")
        elif np.isinf(amount):
            errors.append(f"{field_name} cannot be infinite")
        elif amount < 0:
            errors.append(f"{field_name} cannot be negative: {amount}")
        elif 0 < amount < 0.0001:
            # Warn about dust amounts
            self.warnings.append(f"{field_name} is very small (dust): {amount}")
        
        return errors
    
    def _validate_rsi(self, rsi: Any) -> List[str]:
        """Validate RSI value."""
        errors = []
        
        if not isinstance(rsi, (int, float)):
            errors.append(f"RSI must be numeric, got {type(rsi)}")
            return errors
        
        if np.isnan(rsi):
            errors.append("RSI cannot be NaN")
        elif np.isinf(rsi):
            errors.append("RSI cannot be infinite")
        elif not (0 <= rsi <= 100):
            errors.append(f"RSI must be between 0-100: {rsi}")
        
        return errors
    
    def _validate_macd(self, macd: Any) -> List[str]:
        """Validate MACD data structure."""
        errors = []
        
        if not isinstance(macd, dict):
            errors.append(f"MACD must be dict, got {type(macd)}")
            return errors
        
        # Check for required keys and validate values
        for key in ['macd', 'signal', 'histogram']:
            if key in macd:
                value = macd[key]
                if not isinstance(value, (int, float)):
                    errors.append(f"MACD.{key} must be numeric, got {type(value)}")
                elif np.isnan(value):
                    errors.append(f"MACD.{key} cannot be NaN")
                elif np.isinf(value):
                    errors.append(f"MACD.{key} cannot be infinite")
                elif abs(value) > 100:  # Reasonable bounds check
                    errors.append(f"MACD.{key} seems unreasonable: {value}")
        
        return errors
    
    def _validate_bollinger_bands(self, indicators: Dict) -> List[str]:
        """Validate Bollinger Bands data."""
        errors = []
        
        bb_keys = ['bb_upper', 'bb_lower', 'bb_middle']
        bb_values = {}
        
        # Validate individual values
        for key in bb_keys:
            if key in indicators:
                value = indicators[key]
                value_errors = self._validate_price(value, key)
                errors.extend(value_errors)
                if len(value_errors) == 0:
                    bb_values[key] = value
        
        # Validate relationships if all values are present and valid
        if len(bb_values) == 3:
            upper = bb_values['bb_upper']
            middle = bb_values['bb_middle']
            lower = bb_values['bb_lower']
            
            if not (upper > middle > lower):
                errors.append(f"Invalid Bollinger Band relationship: upper({upper}) > middle({middle}) > lower({lower})")
            
            # Check band width reasonableness
            band_width = upper - lower
            width_percentage = (band_width / middle) * 100
            if width_percentage < 0.5:
                errors.append(f"Bollinger Bands too narrow: {width_percentage:.2f}%")
            elif width_percentage > 30:
                errors.append(f"Bollinger Bands too wide: {width_percentage:.2f}%")
        
        return errors
    
    def _validate_volume_data(self, volume: Any) -> List[str]:
        """Validate volume data structure."""
        errors = []
        
        if not isinstance(volume, dict):
            errors.append(f"Volume data must be dict, got {type(volume)}")
            return errors
        
        for key in ['current', 'average']:
            if key in volume:
                value = volume[key]
                if not isinstance(value, (int, float)):
                    errors.append(f"Volume.{key} must be numeric, got {type(value)}")
                elif np.isnan(value):
                    errors.append(f"Volume.{key} cannot be NaN")
                elif np.isinf(value):
                    errors.append(f"Volume.{key} cannot be infinite")
                elif value < 0:
                    errors.append(f"Volume.{key} cannot be negative: {value}")
        
        return errors
    
    def _validate_price_changes(self, price_changes: Any) -> List[str]:
        """Validate price changes data."""
        errors = []
        
        if not isinstance(price_changes, dict):
            errors.append(f"Price changes must be dict, got {type(price_changes)}")
            return errors
        
        required_timeframes = ['1h', '4h', '24h', '5d']
        
        for timeframe in required_timeframes:
            if timeframe in price_changes:
                change = price_changes[timeframe]
                if not isinstance(change, (int, float)):
                    errors.append(f"Price change {timeframe} must be numeric, got {type(change)}")
                elif np.isnan(change):
                    errors.append(f"Price change {timeframe} cannot be NaN")
                elif np.isinf(change):
                    errors.append(f"Price change {timeframe} cannot be infinite")
                elif abs(change) > 100:  # More than 100% change seems extreme
                    errors.append(f"Price change {timeframe} seems extreme: {change}%")
        
        return errors
    
    def _validate_timestamp(self, timestamp: Any) -> List[str]:
        """Validate timestamp and check freshness."""
        errors = []
        
        if not isinstance(timestamp, str):
            errors.append(f"Timestamp must be string, got {type(timestamp)}")
            return errors
        
        try:
            # Parse timestamp
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # Check freshness (data shouldn't be older than 2 hours)
            now = datetime.utcnow()
            age = now - dt.replace(tzinfo=None)
            
            if age.total_seconds() > 7200:  # 2 hours
                errors.append(f"Data is stale: {age.total_seconds():.0f} seconds old")
            elif age.total_seconds() > 1800:  # 30 minutes
                self.warnings.append(f"Data is getting old: {age.total_seconds():.0f} seconds")
                
        except ValueError as e:
            errors.append(f"Invalid timestamp format: {e}")
        
        return errors
    
    def validate_all(self, market_data: Dict, technical_indicators: Dict, portfolio: Dict) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Validate all data components.
        
        Returns:
            Tuple of (all_valid, dict_of_errors_by_component)
        """
        all_errors = {}
        
        # Validate market data
        market_valid, market_errors = self.validate_market_data(market_data)
        if market_errors:
            all_errors['market_data'] = market_errors
        
        # Validate technical indicators
        tech_valid, tech_errors = self.validate_technical_indicators(technical_indicators)
        if tech_errors:
            all_errors['technical_indicators'] = tech_errors
        
        # Validate portfolio
        portfolio_valid, portfolio_errors = self.validate_portfolio_data(portfolio)
        if portfolio_errors:
            all_errors['portfolio'] = portfolio_errors
        
        all_valid = market_valid and tech_valid and portfolio_valid
        
        # Log results
        if not all_valid:
            self.logger.error(f"Data quality validation failed: {all_errors}")
        elif self.warnings:
            self.logger.warning(f"Data quality warnings: {self.warnings}")
        else:
            self.logger.debug("All data quality checks passed")
        
        return all_valid, all_errors
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation results."""
        return {
            'errors': self.validation_errors,
            'warnings': self.warnings,
            'error_count': len(self.validation_errors),
            'warning_count': len(self.warnings)
        }


def validate_data_quality(logger: Optional[logging.Logger] = None):
    """
    Decorator to validate data quality before function execution.
    
    Usage:
        @validate_data_quality()
        def analyze_market(market_data, technical_indicators, portfolio):
            # Function will only execute if data quality is good
            pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = DataQualityMonitor(logger)
            
            # Try to extract data from function arguments
            market_data = None
            technical_indicators = None
            portfolio = None
            
            # Look for data in args and kwargs
            if len(args) >= 3:
                market_data, technical_indicators, portfolio = args[0], args[1], args[2]
            else:
                market_data = kwargs.get('market_data')
                technical_indicators = kwargs.get('technical_indicators')
                portfolio = kwargs.get('portfolio')
            
            # Validate if we have the data
            if all(x is not None for x in [market_data, technical_indicators, portfolio]):
                is_valid, errors = monitor.validate_all(market_data, technical_indicators, portfolio)
                
                if not is_valid:
                    error_msg = f"Data quality validation failed: {errors}"
                    if logger:
                        logger.error(error_msg)
                    raise DataQualityError(error_msg)
            
            # Execute original function if validation passes
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Example usage functions
def check_data_quality_before_trading(market_data: Dict, technical_indicators: Dict, portfolio: Dict) -> bool:
    """
    Standalone function to check data quality before making trading decisions.
    
    Returns:
        True if data quality is acceptable for trading
    """
    monitor = DataQualityMonitor()
    is_valid, errors = monitor.validate_all(market_data, technical_indicators, portfolio)
    
    if not is_valid:
        print(f"Data quality issues detected: {errors}")
        return False
    
    if monitor.warnings:
        print(f"Data quality warnings: {monitor.warnings}")
    
    return True


def log_data_quality_metrics(market_data: Dict, technical_indicators: Dict, portfolio: Dict, logger: logging.Logger):
    """
    Log detailed data quality metrics for monitoring.
    """
    monitor = DataQualityMonitor(logger)
    is_valid, errors = monitor.validate_all(market_data, technical_indicators, portfolio)
    
    summary = monitor.get_validation_summary()
    
    logger.info(f"Data Quality Summary: "
               f"Valid={is_valid}, "
               f"Errors={summary['error_count']}, "
               f"Warnings={summary['warning_count']}")
    
    if errors:
        for component, component_errors in errors.items():
            logger.error(f"Data quality errors in {component}: {component_errors}")
    
    return is_valid
