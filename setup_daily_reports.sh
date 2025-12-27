#!/bin/bash
# Setup Daily Email Reports

echo "🤖 Setting up Daily Email Reports for Crypto Bot"
echo "================================================"

# Add email configuration to .env file
echo ""
echo "Adding email configuration to .env..."

# Check if email config already exists
if ! grep -q "GMAIL_USER" /home/markus/AI-crypto-bot/.env; then
    echo "" >> /home/markus/AI-crypto-bot/.env
    echo "# Email Configuration for Daily Reports" >> /home/markus/AI-crypto-bot/.env
    echo "GMAIL_USER=your-email@gmail.com" >> /home/markus/AI-crypto-bot/.env
    echo "GMAIL_APP_PASSWORD=your-app-password" >> /home/markus/AI-crypto-bot/.env
    echo "✅ Email configuration added to .env"
else
    echo "✅ Email configuration already exists in .env"
fi

# Install required packages
echo ""
echo "Installing required packages..."
cd /home/markus/AI-crypto-bot
source venv/bin/activate
pip install google-generativeai

# Create cron job for daily reports at 8:00 AM
echo ""
echo "Setting up daily cron job..."
(crontab -l 2>/dev/null; echo "0 8 * * * cd /home/markus/AI-crypto-bot && source venv/bin/activate && python3 daily_report.py >> logs/daily_report.log 2>&1") | crontab -

echo ""
echo "✅ Setup complete!"
echo ""
echo "📧 NEXT STEPS:"
echo "1. Edit /home/markus/AI-crypto-bot/.env and add your:"
echo "   - GMAIL_USER=your-email@gmail.com"
echo "   - GMAIL_APP_PASSWORD=your-gmail-app-password"
echo ""
echo "2. To get Gmail App Password:"
echo "   - Go to Google Account settings"
echo "   - Enable 2-factor authentication"
echo "   - Generate App Password for 'Mail'"
echo ""
echo "3. Test the report:"
echo "   cd /home/markus/AI-crypto-bot && python3 daily_report.py"
echo ""
echo "📅 Daily reports will be sent at 8:00 AM every day to markus@juntoai.org"
