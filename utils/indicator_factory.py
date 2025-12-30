#!/usr/bin/env python3
"""
Indicator Factory Import Bridge

This module provides backward compatibility by importing from the correct location.
"""

# Import from the actual location
from .performance.indicator_factory import IndicatorFactory

# Export main class
__all__ = ['IndicatorFactory']
