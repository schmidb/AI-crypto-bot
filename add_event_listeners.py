#!/usr/bin/env python3

def add_event_listeners():
    """Add the missing event listeners for the new trade history controls"""
    
    dashboard_file = "/var/www/html/crypto-bot/index.html"
    
    try:
        with open(dashboard_file, 'r') as f:
            content = f.read()
        
        # Find the location to add event listeners (before loadDashboardData call)
        insertion_point = "// Load dashboard data\n            loadDashboardData();"
        
        event_listeners_code = '''
            // Add event listeners for trade history controls
            const actionFilter = document.getElementById('actionFilter');
            const historyLimit = document.getElementById('historyLimit');
            
            function reloadTradeHistory() {
                fetch('data/trading_data.json')
                    .then(response => response.json())
                    .then(data => {
                        updateTradeHistory(data.recent_trades);
                    })
                    .catch(error => console.error('Error loading trade history:', error));
            }
            
            if (actionFilter) {
                actionFilter.addEventListener('change', reloadTradeHistory);
            }
            
            if (historyLimit) {
                historyLimit.addEventListener('change', reloadTradeHistory);
            }
            
            // Load dashboard data'''
        
        if "reloadTradeHistory" not in content:
            content = content.replace(insertion_point, event_listeners_code)
            print("✅ Added event listeners for trade history controls")
        else:
            print("✅ Event listeners already exist")
        
        # Write the updated content back
        with open(dashboard_file, 'w') as f:
            f.write(content)
        
        print("\n✅ Event listeners added successfully!")
        print("🔄 The dashboard now includes:")
        print("   • Event listener for Show dropdown (historyLimit)")
        print("   • Event listener for View dropdown (actionFilter)")
        print("   • Automatic reload of trade history when filters change")
        
    except Exception as e:
        print(f"❌ Error adding event listeners: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Adding Event Listeners ===")
    add_event_listeners()
