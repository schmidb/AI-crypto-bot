#!/usr/bin/env python3

import re

def improve_trade_history_dashboard():
    """Improve the trade history section with better filtering and organization"""
    
    dashboard_file = "/var/www/html/crypto-bot/index.html"
    
    try:
        with open(dashboard_file, 'r') as f:
            content = f.read()
        
        # First, let's add a configuration section for trade history limits
        config_addition = '''                        <tr>
                            <th>Trade History Limit</th>
                            <td id="configTradeLimit">10</td>
                        </tr>'''
        
        # Find the config table and add the new row
        config_pattern = r'(<tr>\s*<th>Max Trade Percentage</th>\s*<td id="configMaxTrade">.*?</td>\s*</tr>)'
        if re.search(config_pattern, content, re.DOTALL):
            content = re.sub(config_pattern, r'\1\n' + config_addition, content, flags=re.DOTALL)
            print("✅ Added trade history limit to config section")
        
        # Replace the current trade history section with an improved version
        old_trade_section = r'''                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5>Trade History</h5>
                        <div>
                            <label for="actionFilter" class="form-label me-2">Filter:</label>
                            <div class="d-inline-block">
                                <select id="actionFilter" class="form-select form-select-sm" style="width: 100px;">
                                    <option value="all">All</option>
                                    <option value="buy">Buy</option>
                                    <option value="sell">Sell</option>
                                    <option value="hold">Hold</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="card-body">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Date/Time</th>
                                    <th>Product</th>
                                    <th>Action</th>
                                    <th>Amount</th>
                                    <th>Price</th>
                                    <th>Value \(USD\)</th>
                                </tr>
                            </thead>
                            <tbody id="tradeHistory">
                                <!-- Trade history will be populated via JavaScript -->
                            </tbody>
                        </table>
                    </div>
                </div>'''
        
        new_trade_section = '''                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5>Trading Activity</h5>
                        <div class="d-flex align-items-center gap-3">
                            <div>
                                <label for="historyLimit" class="form-label me-2">Show:</label>
                                <select id="historyLimit" class="form-select form-select-sm" style="width: 80px;">
                                    <option value="5">5</option>
                                    <option value="10" selected>10</option>
                                    <option value="20">20</option>
                                    <option value="50">50</option>
                                </select>
                            </div>
                            <div>
                                <label for="actionFilter" class="form-label me-2">View:</label>
                                <select id="actionFilter" class="form-select form-select-sm" style="width: 120px;">
                                    <option value="recent">Recent All</option>
                                    <option value="buy">Last Buys</option>
                                    <option value="sell">Last Sells</option>
                                    <option value="hold">Last Holds</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="card-body">
                        <!-- Summary Stats -->
                        <div class="row mb-3">
                            <div class="col-md-3">
                                <div class="text-center p-2 bg-light rounded">
                                    <small class="text-muted">Total Trades</small>
                                    <div class="fw-bold" id="totalTrades">0</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="text-center p-2 bg-success bg-opacity-10 rounded">
                                    <small class="text-muted">Buy Orders</small>
                                    <div class="fw-bold text-success" id="totalBuys">0</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="text-center p-2 bg-danger bg-opacity-10 rounded">
                                    <small class="text-muted">Sell Orders</small>
                                    <div class="fw-bold text-danger" id="totalSells">0</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="text-center p-2 bg-warning bg-opacity-10 rounded">
                                    <small class="text-muted">Hold Decisions</small>
                                    <div class="fw-bold text-warning" id="totalHolds">0</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Trade History Table -->
                        <div class="table-responsive">
                            <table class="table table-striped table-hover">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Date/Time</th>
                                        <th>Product</th>
                                        <th>Action</th>
                                        <th>Amount</th>
                                        <th>Price</th>
                                        <th>Value (USD)</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody id="tradeHistory">
                                    <!-- Trade history will be populated via JavaScript -->
                                </tbody>
                            </table>
                        </div>
                        
                        <!-- No Data Message -->
                        <div id="noTradesMessage" class="text-center py-4 d-none">
                            <div class="text-muted">
                                <i class="fas fa-chart-line fa-3x mb-3"></i>
                                <h5>No Trading Activity</h5>
                                <p>No trades found for the selected filter. Try changing the view or limit settings.</p>
                            </div>
                        </div>
                    </div>
                </div>'''
        
        # Replace the trade history section
        if re.search(old_trade_section, content, re.DOTALL):
            content = re.sub(old_trade_section, new_trade_section, content, flags=re.DOTALL)
            print("✅ Replaced trade history section with improved version")
        else:
            print("⚠️ Could not find exact trade history section pattern")
        
        # Now let's update the JavaScript function
        old_js_function = r'''// Function to update trade history
        function updateTradeHistory\(trades\) \{
            const tradeHistoryElement = document\.getElementById\('tradeHistory'\);
            const actionFilter = document\.getElementById\('actionFilter'\);
            const selectedAction = actionFilter \? actionFilter\.value : 'all';
            
            tradeHistoryElement\.innerHTML = '';
            
            if \(trades && trades\.length > 0\) \{
                // Filter trades based on selected action
                const filteredTrades = selectedAction === 'all' 
                    \? trades 
                    : trades\.filter\(trade => trade\.action && trade\.action\.toLowerCase\(\) === selectedAction\.toLowerCase\(\)\);
                
                if \(filteredTrades\.length === 0\) \{
                    tradeHistoryElement\.innerHTML = `<tr><td colspan="6" class="text-center">No \$\{selectedAction\} trades found</td></tr>`;
                    return;
                \}
                
                filteredTrades\.forEach\(trade => \{
                    const row = document\.createElement\('tr'\);
                    const timestamp = new Date\(trade\.timestamp\)\.toLocaleString\(\);
                    const productId = trade\.product_id \|\| '';
                    const action = trade\.action \|\| '';
                    const cryptoAmount = trade\.crypto_amount \|\| 0;
                    const price = trade\.price \|\| 0;
                    const tradeAmountUsd = trade\.trade_amount_usd \|\| 0;
                    
                    row\.innerHTML = `
                        <td>\$\{timestamp\}</td>
                        <td>\$\{productId\}</td>
                        <td>\$\{action\}</td>
                        <td>\$\{cryptoAmount\.toFixed\(8\)\}</td>
                        <td>\$\$\{price\.toFixed\(2\)\}</td>
                        <td>\$\$\{tradeAmountUsd\.toFixed\(2\)\}</td>
                    `;
                    tradeHistoryElement\.appendChild\(row\);
                \}\);
            \} else \{
                tradeHistoryElement\.innerHTML = '<tr><td colspan="6" class="text-center">No trades yet</td></tr>';
            \}
        \}'''
        
        new_js_function = '''// Function to update trade history with improved filtering
        function updateTradeHistory(trades) {
            const tradeHistoryElement = document.getElementById('tradeHistory');
            const actionFilter = document.getElementById('actionFilter');
            const historyLimit = document.getElementById('historyLimit');
            const noTradesMessage = document.getElementById('noTradesMessage');
            
            const selectedAction = actionFilter ? actionFilter.value : 'recent';
            const limit = historyLimit ? parseInt(historyLimit.value) : 10;
            
            // Clear previous content
            tradeHistoryElement.innerHTML = '';
            noTradesMessage.classList.add('d-none');
            
            if (!trades || trades.length === 0) {
                showNoTradesMessage('No trading activity recorded yet.');
                updateTradingStats([], [], [], []);
                return;
            }
            
            // Sort trades by timestamp (most recent first)
            const sortedTrades = [...trades].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
            
            // Separate trades by action type
            const buyTrades = sortedTrades.filter(trade => trade.action && trade.action.toLowerCase() === 'buy');
            const sellTrades = sortedTrades.filter(trade => trade.action && trade.action.toLowerCase() === 'sell');
            const holdTrades = sortedTrades.filter(trade => trade.action && trade.action.toLowerCase() === 'hold');
            
            // Update summary stats
            updateTradingStats(sortedTrades, buyTrades, sellTrades, holdTrades);
            
            // Filter trades based on selected action and limit
            let filteredTrades = [];
            let messageContext = '';
            
            switch(selectedAction) {
                case 'recent':
                    filteredTrades = sortedTrades.slice(0, limit);
                    messageContext = `last ${limit} activities`;
                    break;
                case 'buy':
                    filteredTrades = buyTrades.slice(0, limit);
                    messageContext = `last ${limit} buy orders`;
                    break;
                case 'sell':
                    filteredTrades = sellTrades.slice(0, limit);
                    messageContext = `last ${limit} sell orders`;
                    break;
                case 'hold':
                    filteredTrades = holdTrades.slice(0, limit);
                    messageContext = `last ${limit} hold decisions`;
                    break;
                default:
                    filteredTrades = sortedTrades.slice(0, limit);
                    messageContext = `last ${limit} activities`;
            }
            
            if (filteredTrades.length === 0) {
                showNoTradesMessage(`No ${messageContext} found.`);
                return;
            }
            
            // Populate the table
            filteredTrades.forEach(trade => {
                const row = document.createElement('tr');
                const timestamp = new Date(trade.timestamp).toLocaleString();
                const productId = trade.product_id || '';
                const action = trade.action || '';
                const cryptoAmount = trade.crypto_amount || 0;
                const price = trade.price || 0;
                const tradeAmountUsd = trade.trade_amount_usd || 0;
                
                // Determine action styling and status
                let actionClass = '';
                let statusBadge = '';
                
                switch(action.toLowerCase()) {
                    case 'buy':
                        actionClass = 'text-success fw-bold';
                        statusBadge = '<span class="badge bg-success">BUY</span>';
                        break;
                    case 'sell':
                        actionClass = 'text-danger fw-bold';
                        statusBadge = '<span class="badge bg-danger">SELL</span>';
                        break;
                    case 'hold':
                        actionClass = 'text-warning fw-bold';
                        statusBadge = '<span class="badge bg-warning">HOLD</span>';
                        break;
                    default:
                        actionClass = 'text-muted';
                        statusBadge = '<span class="badge bg-secondary">UNKNOWN</span>';
                }
                
                // Format amounts based on crypto type
                let formattedAmount = cryptoAmount.toFixed(8);
                if (productId.includes('BTC')) {
                    formattedAmount = cryptoAmount.toFixed(8);
                } else if (productId.includes('ETH')) {
                    formattedAmount = cryptoAmount.toFixed(6);
                } else if (productId.includes('SOL')) {
                    formattedAmount = cryptoAmount.toFixed(4);
                } else {
                    formattedAmount = cryptoAmount.toFixed(6);
                }
                
                row.innerHTML = `
                    <td><small>${timestamp}</small></td>
                    <td><strong>${productId}</strong></td>
                    <td class="${actionClass}">${action.toUpperCase()}</td>
                    <td>${formattedAmount}</td>
                    <td>$${price.toFixed(2)}</td>
                    <td><strong>$${tradeAmountUsd.toFixed(2)}</strong></td>
                    <td>${statusBadge}</td>
                `;
                
                tradeHistoryElement.appendChild(row);
            });
        }
        
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
            document.getElementById('totalTrades').textContent = allTrades.length;
            document.getElementById('totalBuys').textContent = buyTrades.length;
            document.getElementById('totalSells').textContent = sellTrades.length;
            document.getElementById('totalHolds').textContent = holdTrades.length;
        }'''
        
        # Replace the JavaScript function
        if re.search(r'// Function to update trade history', content):
            content = re.sub(old_js_function, new_js_function, content, flags=re.DOTALL)
            print("✅ Updated JavaScript trade history function")
        else:
            print("⚠️ Could not find JavaScript function pattern")
        
        # Update the event listeners to handle the new controls
        old_event_listener = r'''// Add event listener for action filter
            const actionFilter = document\.getElementById\('actionFilter'\);
            if \(actionFilter\) \{
                actionFilter\.addEventListener\('change', function\(\) \{
                    // Reload trade history with the selected filter
                    fetch\('data/trading_data\.json'\)
                        \.then\(response => response\.json\(\)\)
                        \.then\(data => \{
                            updateTradeHistory\(data\.recent_trades\);
                        \}\)
                        \.catch\(error => console\.error\('Error loading trade history:', error\)\);
                \}\);
            \}'''
        
        new_event_listener = '''// Add event listeners for trade history controls
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
            }'''
        
        # Replace the event listener
        if re.search(r'// Add event listener for action filter', content):
            content = re.sub(old_event_listener, new_event_listener, content, flags=re.DOTALL)
            print("✅ Updated event listeners for new controls")
        else:
            print("⚠️ Could not find event listener pattern")
        
        # Write the updated content back
        with open(dashboard_file, 'w') as f:
            f.write(content)
        
        print("\n✅ Trade history dashboard improved successfully!")
        print("🔄 Hard refresh your browser (Ctrl+Shift+R) to see the changes")
        print("\n📊 New features:")
        print("   • Configurable number of trades to show (5, 10, 20, 50)")
        print("   • Separate views for Recent All, Last Buys, Last Sells, Last Holds")
        print("   • Trading statistics summary (total trades, buys, sells, holds)")
        print("   • Better styling with action badges and colors")
        print("   • Improved formatting for different crypto amounts")
        print("   • Better no-data messages")
        
    except Exception as e:
        print(f"❌ Error improving trade history: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Improving Trade History Dashboard ===")
    improve_trade_history_dashboard()
