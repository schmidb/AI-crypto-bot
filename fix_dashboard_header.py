#!/usr/bin/env python3

def fix_dashboard_header():
    """Fix the dashboard header section with proper controls"""
    
    dashboard_file = "/var/www/html/crypto-bot/index.html"
    
    try:
        with open(dashboard_file, 'r') as f:
            content = f.read()
        
        # Replace the old header section
        old_header = '''                        <div class="d-flex justify-content-between align-items-center">
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
                        </div>'''
        
        new_header = '''                        <div class="d-flex justify-content-between align-items-center">
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
                        </div>'''
        
        if old_header in content:
            content = content.replace(old_header, new_header)
            print("✅ Updated dashboard header with new controls")
        else:
            print("⚠️ Could not find exact header pattern")
            # Try a more flexible approach
            import re
            pattern = r'<h5>Recent Trading Activity</h5>.*?</select>\s*</div>\s*</div>'
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, '''<h5>Trading Activity</h5>
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
                        </div>''', content, flags=re.DOTALL)
                print("✅ Updated header using flexible pattern matching")
            else:
                print("❌ Could not find any matching pattern")
        
        # Write the updated content back
        with open(dashboard_file, 'w') as f:
            f.write(content)
        
        print("\n✅ Dashboard header fixed!")
        print("🔄 The dashboard header now includes:")
        print("   • Show dropdown (5, 10, 20, 50 trades)")
        print("   • View dropdown (Recent All, Last Buys, Last Sells, Last Holds)")
        print("   • Updated title to 'Trading Activity'")
        
    except Exception as e:
        print(f"❌ Error fixing dashboard header: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Fixing Dashboard Header Section ===")
    fix_dashboard_header()
