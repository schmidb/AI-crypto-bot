#!/usr/bin/env python3

import re
import time

def add_cache_busting():
    """Add cache-busting parameters to dashboard data requests"""
    
    dashboard_file = "/var/www/html/crypto-bot/index.html"
    
    try:
        with open(dashboard_file, 'r') as f:
            content = f.read()
        
        # Add cache-busting timestamp to fetch requests
        timestamp = str(int(time.time()))
        
        # Replace fetch calls with cache-busting versions
        patterns = [
            (r"fetch\('data/portfolio_data\.json'\)", f"fetch('data/portfolio_data.json?v={timestamp}')"),
            (r"fetch\('data/trading_data\.json'\)", f"fetch('data/trading_data.json?v={timestamp}')"),
            (r"fetch\('data/latest_decisions\.json'\)", f"fetch('data/latest_decisions.json?v={timestamp}')"),
            (r"fetch\('data/config\.json'\)", f"fetch('data/config.json?v={timestamp}')"),
            (r"fetch\('data/last_updated\.txt'\)", f"fetch('data/last_updated.txt?v={timestamp}')")
        ]
        
        modified = False
        for pattern, replacement in patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                modified = True
                print(f"✅ Updated: {pattern}")
        
        if modified:
            # Write the updated content back
            with open(dashboard_file, 'w') as f:
                f.write(content)
            print(f"✅ Dashboard updated with cache-busting parameters")
        else:
            print("ℹ️  No fetch calls found to update")
            
    except Exception as e:
        print(f"❌ Error updating dashboard: {e}")

def add_meta_no_cache():
    """Add meta tags to prevent caching"""
    
    dashboard_file = "/var/www/html/crypto-bot/index.html"
    
    try:
        with open(dashboard_file, 'r') as f:
            content = f.read()
        
        # Check if meta tags already exist
        if 'no-cache' not in content:
            # Add meta tags after <head>
            meta_tags = '''    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
'''
            
            content = content.replace('<head>', f'<head>\n{meta_tags}')
            
            with open(dashboard_file, 'w') as f:
                f.write(content)
            
            print("✅ Added no-cache meta tags to dashboard")
        else:
            print("ℹ️  No-cache meta tags already present")
            
    except Exception as e:
        print(f"❌ Error adding meta tags: {e}")

if __name__ == "__main__":
    print("=== Fixing Dashboard Cache Issues ===")
    add_meta_no_cache()
    add_cache_busting()
    print("\n🔄 Please hard refresh your browser (Ctrl+Shift+R) to see the changes")
