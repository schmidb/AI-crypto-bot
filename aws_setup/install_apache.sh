#!/bin/bash

# Script to install and configure Apache web server for crypto bot monitoring
# Exit on error
set -e

echo "Installing and configuring Apache web server for crypto bot monitoring..."

# Install Apache
echo "Installing Apache..."
sudo yum install -y httpd

# Start and enable Apache
echo "Starting and enabling Apache..."
sudo systemctl start httpd
sudo systemctl enable httpd

# Create directory for the dashboard
echo "Creating dashboard directory..."
sudo mkdir -p /var/www/html/crypto-bot
sudo chown ec2-user:ec2-user /var/www/html/crypto-bot

# Create initial HTML files
echo "Creating initial HTML files..."
cat > /var/www/html/crypto-bot/index.html << 'EOL'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Crypto Trading Bot Dashboard</title>
    <meta http-equiv="refresh" content="300"> <!-- Auto-refresh every 5 minutes -->
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <h1>Crypto Trading Bot Dashboard</h1>
        <p class="last-update">Last updated: <span id="update-time">Initializing...</span></p>
    </header>
    
    <main>
        <section class="status-section">
            <h2>Bot Status</h2>
            <div class="status-indicator">
                <span class="status-badge initializing">Initializing</span>
            </div>
            <p>The bot is being initialized. Please wait for the first trading cycle to complete.</p>
        </section>
        
        <section class="trading-pairs">
            <h2>Trading Pairs</h2>
            <div class="pairs-container">
                <p>Waiting for data...</p>
            </div>
        </section>
        
        <section class="recent-trades">
            <h2>Recent Trades</h2>
            <div class="trades-container">
                <p>No trades executed yet.</p>
            </div>
        </section>
        
        <section class="performance">
            <h2>Performance</h2>
            <div class="performance-container">
                <p>Waiting for performance data...</p>
            </div>
        </section>
    </main>
    
    <footer>
        <p>AI Crypto Trading Bot &copy; 2025</p>
    </footer>
</body>
</html>
EOL

cat > /var/www/html/crypto-bot/styles.css << 'EOL'
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f4f7fa;
    padding: 20px;
}

header {
    background-color: #2c3e50;
    color: white;
    padding: 20px;
    border-radius: 8px 8px 0 0;
    margin-bottom: 20px;
}

header h1 {
    margin-bottom: 10px;
}

.last-update {
    font-size: 0.9em;
    opacity: 0.8;
}

section {
    background-color: white;
    border-radius: 8px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

h2 {
    margin-bottom: 15px;
    color: #2c3e50;
    border-bottom: 1px solid #eee;
    padding-bottom: 10px;
}

.status-indicator {
    margin-bottom: 15px;
}

.status-badge {
    display: inline-block;
    padding: 5px 15px;
    border-radius: 20px;
    font-weight: bold;
    color: white;
}

.running {
    background-color: #27ae60;
}

.stopped {
    background-color: #e74c3c;
}

.initializing {
    background-color: #f39c12;
}

.error {
    background-color: #c0392b;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 15px;
}

table, th, td {
    border: 1px solid #eee;
}

th, td {
    padding: 12px 15px;
    text-align: left;
}

th {
    background-color: #f8f9fa;
    font-weight: 600;
}

tr:nth-child(even) {
    background-color: #f8f9fa;
}

.buy {
    color: #27ae60;
}

.sell {
    color: #e74c3c;
}

.hold {
    color: #3498db;
}

footer {
    text-align: center;
    margin-top: 30px;
    color: #7f8c8d;
    font-size: 0.9em;
}

.performance-metrics {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 15px;
    margin-top: 15px;
}

.metric-card {
    background-color: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    text-align: center;
}

.metric-value {
    font-size: 1.8em;
    font-weight: bold;
    margin: 10px 0;
}

.profit {
    color: #27ae60;
}

.loss {
    color: #e74c3c;
}
EOL

# Create .htaccess file for password protection
echo "Creating .htaccess file..."
cat > /var/www/html/crypto-bot/.htaccess << 'EOL'
AuthType Basic
AuthName "Crypto Bot Dashboard"
AuthUserFile /etc/httpd/conf/.htpasswd
Require valid-user
EOL

# Create password file
echo "Creating password file..."
read -p "Enter username for dashboard access: " DASHBOARD_USER
sudo htpasswd -c /etc/httpd/conf/.htpasswd $DASHBOARD_USER

# Set proper permissions
echo "Setting permissions..."
sudo chown -R ec2-user:ec2-user /var/www/html/crypto-bot
sudo chmod -R 755 /var/www/html/crypto-bot
sudo chmod 644 /var/www/html/crypto-bot/.htaccess
sudo chmod 644 /etc/httpd/conf/.htpasswd

# Configure Apache to allow .htaccess
echo "Configuring Apache to allow .htaccess..."
sudo sed -i '/<Directory "\/var\/www\/html">/,/<\/Directory>/ s/AllowOverride None/AllowOverride All/' /etc/httpd/conf/httpd.conf

# Restart Apache to apply changes
echo "Restarting Apache..."
sudo systemctl restart httpd

# Update security group to allow HTTP access
echo "Note: Make sure to update your EC2 security group to allow HTTP access (port 80)"
echo "You can do this from the AWS Console or with the following AWS CLI command:"
echo "aws ec2 authorize-security-group-ingress --group-id YOUR_SECURITY_GROUP_ID --protocol tcp --port 80 --cidr YOUR_IP_ADDRESS/32"

echo ""
echo "Apache installation and configuration completed!"
echo ""
echo "Your dashboard is available at: http://YOUR_EC2_PUBLIC_IP/crypto-bot/"
echo "Username: $DASHBOARD_USER"
echo ""
echo "Next step: Configure the bot to update the dashboard after each trading cycle"
echo ""
