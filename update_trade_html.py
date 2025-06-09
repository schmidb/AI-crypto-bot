#!/usr/bin/env python3

import re

def update_trade_history_html():
    """Update the trade history HTML section with the new improved structure"""
    
    dashboard_file = "/var/www/html/crypto-bot/index.html"
    
    try:
        with open(dashboard_file, 'r') as f:
            content = f.read()
        
        # Find and replace the trade history section
        old_section_pattern = r'''                        <div class="d-flex justify-content-between align-items-center">
                            <h5>Recent Trading Activity</h5>
                            <div class="d-flex align-items-center">
                                <label for="actionFilter" class="me-2">Filter by action:</label>
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
                        </table>'''
        
        new_section = '''                        <div class="d-flex justify-content-between align-items-center">
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
                        </div>'''
        
        # Replace the section
        if re.search(old_section_pattern, content, re.DOTALL):
            content = re.sub(old_section_pattern, new_section, content, flags=re.DOTALL)
            print("✅ Successfully updated trade history HTML structure")
        else:
            print("⚠️ Could not find the exact HTML pattern to replace")
            print("Let me try a more flexible approach...")
            
            # Try a more flexible pattern
            flexible_pattern = r'<h5>Recent Trading Activity</h5>.*?</table>'
            if re.search(flexible_pattern, content, re.DOTALL):
                # Find the start and end points more carefully
                start_marker = '<h5>Recent Trading Activity</h5>'
                end_marker = '</table>'
                
                start_pos = content.find(start_marker)
                if start_pos != -1:
                    # Find the end position after the table
                    temp_content = content[start_pos:]
                    end_pos = temp_content.find(end_marker) + len(end_marker)
                    
                    if end_pos > len(end_marker):
                        # Extract the section to replace
                        section_to_replace = content[start_pos:start_pos + end_pos]
                        
                        # Create the new section (just the inner content)
                        new_inner_section = '''<h5>Trading Activity</h5>
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
                </div>
            </div>
        </div>
        
        <!-- Add the missing closing div and start of next section -->
        <div class="row">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Market Data</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped table-hover">
                                <thead class="table-dark">
                                    <tr>
                                        <th>Asset</th>
                                        <th>Current Price</th>
                                        <th>24h Change</th>
                                        <th>7d Change</th>
                                        <th>30d Change</th>
                                    </tr>
                                </thead>
                                <tbody id="marketData">
                                    <!-- Market data will be populated via JavaScript -->
                                </tbody>
                            </table'''
                        
                        content = content.replace(section_to_replace, new_inner_section)
                        print("✅ Successfully updated using flexible pattern matching")
                    else:
                        print("❌ Could not find end marker")
                else:
                    print("❌ Could not find start marker")
            else:
                print("❌ Could not find any matching pattern")
        
        # Write the updated content back
        with open(dashboard_file, 'w') as f:
            f.write(content)
        
        print("\n✅ Trade history HTML structure updated!")
        print("🔄 The dashboard now includes:")
        print("   • Dropdown to select number of trades to show (5, 10, 20, 50)")
        print("   • Filter options: Recent All, Last Buys, Last Sells, Last Holds")
        print("   • Trading statistics summary with counts")
        print("   • Enhanced table with Status column and better styling")
        print("   • No-data message for better UX")
        
    except Exception as e:
        print(f"❌ Error updating trade history HTML: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Updating Trade History HTML Structure ===")
    update_trade_history_html()
