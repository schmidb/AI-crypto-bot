"""
Push notification service using Pushover for trade alerts
"""

import logging
import requests
from typing import Dict, Any, Optional
from datetime import datetime
from config import config

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending push notifications via Pushover"""
    
    def __init__(self):
        """Initialize notification service"""
        self.pushover_token = getattr(config, 'PUSHOVER_TOKEN', None)
        self.pushover_user = getattr(config, 'PUSHOVER_USER', None)
        self.notifications_enabled = getattr(config, 'NOTIFICATIONS_ENABLED', False)
        
        if self.notifications_enabled and (not self.pushover_token or not self.pushover_user):
            logger.warning("Notifications enabled but Pushover credentials missing")
            self.notifications_enabled = False
        
        if self.notifications_enabled:
            logger.info("Push notifications enabled via Pushover")
        else:
            logger.info("Push notifications disabled")
    
    def send_trade_notification(self, trade_data: Dict[str, Any]) -> bool:
        """
        Send push notification for executed trade
        
        Args:
            trade_data: Dictionary containing trade information
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        if not self.notifications_enabled:
            return False
        
        try:
            # Extract trade information
            action = trade_data.get('action', 'UNKNOWN')
            product_id = trade_data.get('product_id', 'UNKNOWN')
            amount = trade_data.get('amount', 0)
            price = trade_data.get('price', 0)
            total_value = trade_data.get('total_value', 0)
            confidence = trade_data.get('confidence', 0)
            
            # Enhanced fee information
            total_fees = trade_data.get('total_fees', 0)
            actual_eur_spent = trade_data.get('actual_eur_spent', total_value)
            average_filled_price = trade_data.get('average_filled_price', price)
            
            # Create notification message
            title = f"🤖 AI Crypto Bot - {action} Order Executed"
            
            if action == 'BUY':
                emoji = "🟢"
                message = f"{emoji} BUY executed!\n\n"
                message += f"💰 Pair: {product_id}\n"
                message += f"🪙 Quantity: {amount:.6f}\n"
                message += f"📊 Price: €{average_filled_price:.2f}\n"
                message += f"💵 Gross Value: €{total_value:.2f}\n"
                if total_fees > 0:
                    message += f"💸 Fees: €{total_fees:.4f}\n"
                    message += f"💰 Net Spent: €{actual_eur_spent:.2f}\n"
                    fee_percentage = (total_fees / total_value) * 100 if total_value > 0 else 0
                    message += f"📈 Fee Rate: {fee_percentage:.3f}%\n"
                message += f"🎯 AI Confidence: {confidence}%"
            elif action == 'SELL':
                emoji = "🔴"
                message = f"{emoji} SELL executed!\n\n"
                message += f"💰 Pair: {product_id}\n"
                message += f"🪙 Amount: {amount:.6f}\n"
                message += f"📊 Price: €{average_filled_price:.2f}\n"
                message += f"💵 Gross Value: €{total_value:.2f}\n"
                if total_fees > 0:
                    message += f"💸 Fees: €{total_fees:.4f}\n"
                    message += f"💰 Net Received: €{actual_eur_spent:.2f}\n"
                    fee_percentage = (total_fees / total_value) * 100 if total_value > 0 else 0
                    message += f"📈 Fee Rate: {fee_percentage:.3f}%\n"
                message += f"🎯 AI Confidence: {confidence}%"
            else:
                message = f"Trade executed: {action} {product_id}"
            
            # Add timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            message += f"\n\n⏰ Time: {timestamp}"
            
            # Send notification
            return self._send_pushover_notification(title, message, priority=1)
            
        except Exception as e:
            logger.error(f"Error sending trade notification: {e}")
            return False
    
    def send_error_notification(self, error_message: str, context: str = "") -> bool:
        """
        Send push notification for critical errors
        
        Args:
            error_message: Error message to send
            context: Additional context about the error
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        if not self.notifications_enabled:
            return False
        
        try:
            title = "⚠️ AI Crypto Bot - Error Alert"
            message = f"🚨 Critical Error Detected!\n\n"
            message += f"Error: {error_message}\n"
            if context:
                message += f"Context: {context}\n"
            message += f"\n⏰ Time: {datetime.now().strftime('%H:%M:%S')}"
            
            return self._send_pushover_notification(title, message, priority=2)
            
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
            return False
    
    def send_status_notification(self, status_message: str, priority: int = 0) -> bool:
        """
        Send general status notification
        
        Args:
            status_message: Status message to send
            priority: Notification priority (0=normal, 1=high, 2=emergency)
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        if not self.notifications_enabled:
            return False
        
        try:
            title = "ℹ️ AI Crypto Bot - Status Update"
            message = f"{status_message}\n\n⏰ Time: {datetime.now().strftime('%H:%M:%S')}"
            
            return self._send_pushover_notification(title, message, priority=priority)
            
        except Exception as e:
            logger.error(f"Error sending status notification: {e}")
            return False
    
    def send_portfolio_summary(self, portfolio_data: Dict[str, Any]) -> bool:
        """
        Send daily portfolio summary notification
        
        Args:
            portfolio_data: Portfolio summary data
            
        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        if not self.notifications_enabled:
            return False
        
        try:
            title = "📊 AI Crypto Bot - Daily Portfolio Summary"
            
            total_value = portfolio_data.get('total_value', 0)
            daily_change = portfolio_data.get('daily_change', 0)
            daily_change_pct = portfolio_data.get('daily_change_pct', 0)
            
            message = f"📈 Portfolio Update\n\n"
            message += f"💰 Total Value: €{total_value:.2f}\n"
            
            if daily_change >= 0:
                message += f"📈 Daily Change: +€{daily_change:.2f} (+{daily_change_pct:.2f}%)\n"
            else:
                message += f"📉 Daily Change: €{daily_change:.2f} ({daily_change_pct:.2f}%)\n"
            
            # Add top holdings
            holdings = portfolio_data.get('holdings', {})
            if holdings:
                message += f"\n🏆 Top Holdings:\n"
                for asset, data in list(holdings.items())[:3]:
                    if asset != 'EUR':
                        value = data.get('value', 0)
                        percentage = data.get('percentage', 0)
                        message += f"• {asset}: €{value:.2f} ({percentage:.1f}%)\n"
            
            message += f"\n⏰ Time: {datetime.now().strftime('%H:%M:%S')}"
            
            return self._send_pushover_notification(title, message, priority=0)
            
        except Exception as e:
            logger.error(f"Error sending portfolio summary: {e}")
            return False
    
    def _send_pushover_notification(self, title: str, message: str, priority: int = 0) -> bool:
        """
        Send notification via Pushover API
        
        Args:
            title: Notification title
            message: Notification message
            priority: Priority level (0=normal, 1=high, 2=emergency)
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            url = "https://api.pushover.net/1/messages.json"
            
            data = {
                "token": self.pushover_token,
                "user": self.pushover_user,
                "title": title,
                "message": message,
                "priority": priority,
                "sound": "cashregister" if "BUY" in title or "SELL" in title else "pushover"
            }
            
            # Add retry and expire for emergency notifications
            if priority == 2:
                data["retry"] = 60  # Retry every 60 seconds
                data["expire"] = 3600  # Stop retrying after 1 hour
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("status") == 1:
                    logger.info(f"Push notification sent successfully: {title}")
                    return True
                else:
                    logger.error(f"Pushover API error: {result}")
                    return False
            else:
                logger.error(f"HTTP error sending notification: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Exception sending Pushover notification: {e}")
            return False
    
    def test_notification(self) -> bool:
        """
        Send a test notification to verify setup
        
        Returns:
            bool: True if test notification sent successfully
        """
        if not self.notifications_enabled:
            logger.info("Notifications are disabled - cannot send test")
            return False
        
        title = "🧪 AI Crypto Bot - Test Notification"
        message = "This is a test notification to verify your Pushover setup is working correctly!"
        
        success = self._send_pushover_notification(title, message, priority=0)
        
        if success:
            logger.info("Test notification sent successfully!")
        else:
            logger.error("Failed to send test notification")
        
        return success
