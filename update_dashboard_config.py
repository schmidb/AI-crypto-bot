#!/usr/bin/env python3

import re

def update_dashboard_config_usage():
    """Update dashboard to use configuration for default trade history limit"""
    
    dashboard_file = "/var/www/html/crypto-bot/index.html"
    
    try:
        with open(dashboard_file, 'r') as f:
            content = f.read()
        
        # Update the config display to show the trade history limit
        config_update = '''            document.getElementById('configTradingPairs').textContent = config.trading_pairs || 'N/A';
            document.getElementById('configInterval').textContent = `${config.decision_interval_minutes || 'N/A'} minutes`;
            document.getElementById('configRiskLevel').textContent = config.risk_level || 'N/A';
            document.getElementById('configLLMModel').textContent = config.llm_model || 'N/A';
            document.getElementById('configRebalance').textContent = config.portfolio_rebalance ? 'Enabled' : 'Disabled';
            document.getElementById('configMaxTrade').textContent = `${config.max_trade_percentage || 'N/A'}%`;
            
            // Update trade history limit if element exists
            const tradeLimit = document.getElementById('configTradeLimit');
            if (tradeLimit) {
                tradeLimit.textContent = config.dashboard_trade_history_limit || '10';
            }'''
        
        # Find and replace the config update section
        old_config_pattern = r'''document\.getElementById\('configTradingPairs'\)\.textContent = config\.trading_pairs \|\| 'N/A';
            document\.getElementById\('configInterval'\)\.textContent = `\$\{config\.decision_interval_minutes \|\| 'N/A'\} minutes`;
            document\.getElementById\('configRiskLevel'\)\.textContent = config\.risk_level \|\| 'N/A';
            document\.getElementById\('configLLMModel'\)\.textContent = config\.llm_model \|\| 'N/A';
            document\.getElementById\('configRebalance'\)\.textContent = config\.portfolio_rebalance \? 'Enabled' : 'Disabled';
            document\.getElementById\('configMaxTrade'\)\.textContent = `\$\{config\.max_trade_percentage \|\| 'N/A'\}%`;'''
        
        if re.search(old_config_pattern, content):
            content = re.sub(old_config_pattern, config_update, content)
            print("✅ Updated config display to include trade history limit")
        else:
            print("⚠️ Could not find config display pattern")
        
        # Update the default selection in the history limit dropdown to use config
        default_limit_update = '''            const limit = historyLimit ? parseInt(historyLimit.value) : (globalConfig?.dashboard_trade_history_limit || 10);'''
        
        old_limit_pattern = r'const limit = historyLimit \? parseInt\(historyLimit\.value\) : 10;'
        
        if re.search(old_limit_pattern, content):
            content = re.sub(old_limit_pattern, default_limit_update, content)
            print("✅ Updated default limit to use configuration")
        else:
            print("⚠️ Could not find limit pattern")
        
        # Update the dropdown to select the configured default
        dropdown_update = '''            // Set default history limit from config
            if (globalConfig?.dashboard_trade_history_limit && historyLimit) {
                historyLimit.value = globalConfig.dashboard_trade_history_limit.toString();
            }'''
        
        # Find where to insert this - after the globalConfig is set
        config_set_pattern = r'(// Store config globally for use in other functions\s*globalConfig = config;)'
        
        if re.search(config_set_pattern, content):
            content = re.sub(config_set_pattern, r'\1\n            \n            ' + dropdown_update, content)
            print("✅ Added default dropdown selection from config")
        else:
            print("⚠️ Could not find config set pattern")
        
        # Write the updated content back
        with open(dashboard_file, 'w') as f:
            f.write(content)
        
        print("✅ Dashboard configuration usage updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating dashboard config usage: {e}")

if __name__ == "__main__":
    update_dashboard_config_usage()
