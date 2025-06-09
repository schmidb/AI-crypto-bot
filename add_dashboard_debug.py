#!/usr/bin/env python3

import re

def add_debug_to_dashboard():
    """Add debugging console logs to the dashboard"""
    
    dashboard_file = "/var/www/html/crypto-bot/index.html"
    
    try:
        with open(dashboard_file, 'r') as f:
            content = f.read()
        
        # Add debug logging to the updatePortfolioDisplay function
        debug_code = '''            console.log('updatePortfolioDisplay called with:', portfolio);
            
            // Debug SOL specifically
            if (portfolio.SOL) {
                console.log('SOL data found:', portfolio.SOL);
                console.log('SOL amount:', portfolio.SOL.amount, 'type:', typeof portfolio.SOL.amount);
                console.log('SOL value_usd:', portfolio.SOL.value_usd, 'type:', typeof portfolio.SOL.value_usd);
                console.log('SOL allocation:', portfolio.SOL.allocation, 'type:', typeof portfolio.SOL.allocation);
            } else {
                console.log('SOL data NOT found in portfolio');
            }
            
'''
        
        # Insert debug code at the beginning of updatePortfolioDisplay function
        pattern = r'(function updatePortfolioDisplay\(portfolio\) \{\s*// Update portfolio table)'
        replacement = f'function updatePortfolioDisplay(portfolio) {{\n{debug_code}            // Update portfolio table'
        
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            print("✅ Added debug logging to updatePortfolioDisplay function")
        else:
            print("⚠️ Could not find updatePortfolioDisplay function pattern")
        
        # Add debug logging to the asset filtering
        asset_debug = '''            console.log('Filtered assets:', assets);
            console.log('Processing assets...');
            
'''
        
        pattern2 = r'(for \(const asset of assets\) \{)'
        replacement2 = f'{asset_debug}            for (const asset of assets) {{'
        
        if re.search(pattern2, content):
            content = re.sub(pattern2, replacement2, content)
            print("✅ Added debug logging to asset processing loop")
        else:
            print("⚠️ Could not find asset processing loop pattern")
        
        # Add debug logging inside the asset loop
        loop_debug = '''                    console.log(`Processing ${asset}:`, {
                        amount: amount,
                        valueUsd: valueUsd,
                        allocation: allocation,
                        formattedAmount: formattedAmount
                    });
                    
                    if (asset === 'SOL') {
                        console.log('SOL processing details:', {
                            'amount (raw)': portfolio[asset].amount,
                            'valueUsd (raw)': portfolio[asset].value_usd,
                            'allocation (raw)': portfolio[asset].allocation,
                            'amount (processed)': amount,
                            'valueUsd (processed)': valueUsd,
                            'allocation (processed)': allocation,
                            'formattedAmount': formattedAmount,
                            'formattedValue': `$${valueUsd.toFixed(2)}`,
                            'formattedAllocation': `${allocation.toFixed(2)}%`
                        });
                    }
                    
'''
        
        # Find the right place to insert the loop debug code
        pattern3 = r'(formattedAmount = amount\.toFixed\(6\); // Default for other cryptos\s*}\s*)(tableHtml \+= `)'
        replacement3 = f'formattedAmount = amount.toFixed(6); // Default for other cryptos\n                    }}\n                    \n{loop_debug}                    tableHtml += `'
        
        if re.search(pattern3, content, re.DOTALL):
            content = re.sub(pattern3, replacement3, content, flags=re.DOTALL)
            print("✅ Added debug logging inside asset processing loop")
        else:
            print("⚠️ Could not find asset processing loop interior pattern")
        
        # Add debug logging after table generation
        table_debug = '''            console.log('Generated table HTML:', tableHtml);
            console.log('Setting portfolioTable.innerHTML...');
            
'''
        
        pattern4 = r'(portfolioTable\.innerHTML = tableHtml;)'
        replacement4 = f'{table_debug}            portfolioTable.innerHTML = tableHtml;\n            console.log("Portfolio table updated successfully");'
        
        if re.search(pattern4, content):
            content = re.sub(pattern4, replacement4, content)
            print("✅ Added debug logging for table HTML generation")
        else:
            print("⚠️ Could not find table HTML assignment pattern")
        
        # Write the updated content back
        with open(dashboard_file, 'w') as f:
            f.write(content)
        
        print("\n✅ Dashboard updated with debug logging")
        print("🔍 Check browser console (F12) for detailed debug information")
        print("🔄 Hard refresh the dashboard (Ctrl+Shift+R) to see debug logs")
        
    except Exception as e:
        print(f"❌ Error updating dashboard: {e}")

if __name__ == "__main__":
    print("=== Adding Debug Logging to Dashboard ===")
    add_debug_to_dashboard()
