#!/usr/bin/env python3
"""
Test script for push notifications
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.notification_service import NotificationService
from config import config
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_notifications():
    """Test push notification functionality"""
    
    print("🧪 Testing Push Notifications")
    print("=" * 50)
    
    # Check configuration
    print(f"Notifications Enabled: {config.NOTIFICATIONS_ENABLED}")
    print(f"Pushover Token: {'✓ Set' if config.PUSHOVER_TOKEN else '✗ Missing'}")
    print(f"Pushover User: {'✓ Set' if config.PUSHOVER_USER else '✗ Missing'}")
    print()
    
    if not config.NOTIFICATIONS_ENABLED:
        print("❌ Notifications are disabled in configuration")
        print("To enable notifications:")
        print("1. Set NOTIFICATIONS_ENABLED=true in your .env file")
        print("2. Add your Pushover credentials")
        return False
    
    if not config.PUSHOVER_TOKEN or not config.PUSHOVER_USER:
        print("❌ Pushover credentials missing")
        print("Please add the following to your .env file:")
        print("PUSHOVER_TOKEN=your_pushover_app_token")
        print("PUSHOVER_USER=your_pushover_user_key")
        return False
    
    # Initialize notification service
    notification_service = NotificationService()
    
    # Test 1: Basic test notification
    print("📱 Sending test notification...")
    success = notification_service.test_notification()
    if success:
        print("✅ Test notification sent successfully!")
    else:
        print("❌ Failed to send test notification")
        return False
    
    # Test 2: Trade notification (BUY)
    print("\n📱 Sending sample BUY notification...")
    buy_trade_data = {
        'action': 'BUY',
        'product_id': 'BTC-EUR',
        'amount': 0.001234,
        'price': 45000.50,
        'total_value': 55.56,
        'confidence': 85,
        'order_id': 'test-buy-order-123',
        'timestamp': '2024-01-01T12:00:00'
    }
    
    success = notification_service.send_trade_notification(buy_trade_data)
    if success:
        print("✅ BUY notification sent successfully!")
    else:
        print("❌ Failed to send BUY notification")
    
    # Test 3: Trade notification (SELL)
    print("\n📱 Sending sample SELL notification...")
    sell_trade_data = {
        'action': 'SELL',
        'product_id': 'ETH-EUR',
        'amount': 0.05678,
        'price': 2500.75,
        'total_value': 142.04,
        'confidence': 78,
        'order_id': 'test-sell-order-456',
        'timestamp': '2024-01-01T12:05:00'
    }
    
    success = notification_service.send_trade_notification(sell_trade_data)
    if success:
        print("✅ SELL notification sent successfully!")
    else:
        print("❌ Failed to send SELL notification")
    
    # Test 4: Error notification
    print("\n📱 Sending sample error notification...")
    success = notification_service.send_error_notification(
        "API connection failed", 
        "Testing error notification system"
    )
    if success:
        print("✅ Error notification sent successfully!")
    else:
        print("❌ Failed to send error notification")
    
    # Test 5: Portfolio summary
    print("\n📱 Sending sample portfolio summary...")
    portfolio_data = {
        'total_value': 1250.75,
        'daily_change': 45.30,
        'daily_change_pct': 3.75,
        'holdings': {
            'BTC': {'value': 500.25, 'percentage': 40.0},
            'ETH': {'value': 375.50, 'percentage': 30.0},
            'SOL': {'value': 250.00, 'percentage': 20.0},
            'EUR': {'value': 125.00, 'percentage': 10.0}
        }
    }
    
    success = notification_service.send_portfolio_summary(portfolio_data)
    if success:
        print("✅ Portfolio summary sent successfully!")
    else:
        print("❌ Failed to send portfolio summary")
    
    print("\n🎉 Notification testing completed!")
    print("Check your mobile device for the test notifications.")
    
    return True

def setup_instructions():
    """Display setup instructions for Pushover"""
    
    print("📱 Pushover Setup Instructions")
    print("=" * 50)
    print()
    print("1. Download the Pushover app on your mobile device:")
    print("   - iOS: https://apps.apple.com/app/pushover-notifications/id506088175")
    print("   - Android: https://play.google.com/store/apps/details?id=net.superblock.pushover")
    print()
    print("2. Create a Pushover account at https://pushover.net")
    print()
    print("3. Get your User Key:")
    print("   - Login to https://pushover.net")
    print("   - Your User Key is displayed on the main page")
    print()
    print("4. Create an Application:")
    print("   - Go to https://pushover.net/apps/build")
    print("   - Create a new application (e.g., 'AI Crypto Bot')")
    print("   - Note down the API Token/Key")
    print()
    print("5. Add to your .env file:")
    print("   NOTIFICATIONS_ENABLED=true")
    print("   PUSHOVER_TOKEN=your_app_api_token")
    print("   PUSHOVER_USER=your_user_key")
    print()
    print("6. Install the python-pushover package:")
    print("   pip install python-pushover")
    print()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "setup":
        setup_instructions()
    else:
        test_notifications()
