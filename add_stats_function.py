#!/usr/bin/env python3

def add_stats_function():
    """Add the missing updateTradingStats function"""
    
    dashboard_file = "/var/www/html/crypto-bot/index.html"
    
    try:
        with open(dashboard_file, 'r') as f:
            content = f.read()
        
        # Find the location to add the function (after updateTradeHistory function)
        insertion_point = "        }"  # End of updateTradeHistory function
        
        stats_function = '''
        
        // Helper function to show no trades message
        function showNoTradesMessage(message) {
            const noTradesMessage = document.getElementById('noTradesMessage');
            const messageElement = noTradesMessage.querySelector('p');
            if (messageElement) {
                messageElement.textContent = message;
            }
            noTradesMessage.classList.remove('d-none');
        }
        
        // Helper function to update trading statistics
        function updateTradingStats(allTrades, buyTrades, sellTrades, holdTrades) {
            const totalTradesElement = document.getElementById('totalTrades');
            const totalBuysElement = document.getElementById('totalBuys');
            const totalSellsElement = document.getElementById('totalSells');
            const totalHoldsElement = document.getElementById('totalHolds');
            
            if (totalTradesElement) totalTradesElement.textContent = allTrades.length;
            if (totalBuysElement) totalBuysElement.textContent = buyTrades.length;
            if (totalSellsElement) totalSellsElement.textContent = sellTrades.length;
            if (totalHoldsElement) totalHoldsElement.textContent = holdTrades.length;
        }'''
        
        if "updateTradingStats" not in content:
            # Find the end of updateTradeHistory function
            import re
            pattern = r'(function updateTradeHistory\(trades\) \{.*?\n        \})'
            match = re.search(pattern, content, re.DOTALL)
            if match:
                content = content.replace(match.group(1), match.group(1) + stats_function)
                print("✅ Added updateTradingStats function")
            else:
                print("⚠️ Could not find updateTradeHistory function to insert after")
        else:
            print("✅ updateTradingStats function already exists")
        
        # Also need to update the updateTradeHistory function to call updateTradingStats
        if "updateTradingStats(sortedTrades, buyTrades, sellTrades, holdTrades);" not in content:
            # Find where to add the call to updateTradingStats
            stats_call_pattern = r'(// Separate trades by action type.*?const holdTrades = sortedTrades\.filter\(trade => trade\.action && trade\.action\.toLowerCase\(\) === \'hold\'\);)'
            stats_call_replacement = r'\1\n            \n            // Update summary stats\n            updateTradingStats(sortedTrades, buyTrades, sellTrades, holdTrades);'
            
            if re.search(stats_call_pattern, content, re.DOTALL):
                content = re.sub(stats_call_pattern, stats_call_replacement, content, flags=re.DOTALL)
                print("✅ Added call to updateTradingStats in updateTradeHistory")
            else:
                print("⚠️ Could not find location to add updateTradingStats call")
        
        # Write the updated content back
        with open(dashboard_file, 'w') as f:
            f.write(content)
        
        print("\n✅ Statistics functions added successfully!")
        print("🔄 The dashboard now includes:")
        print("   • updateTradingStats function to update counters")
        print("   • showNoTradesMessage function for better UX")
        print("   • Proper integration with trade history display")
        
    except Exception as e:
        print(f"❌ Error adding statistics functions: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Adding Statistics Functions ===")
    add_stats_function()
