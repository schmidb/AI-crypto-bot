#!/usr/bin/env python3

def fix_dashboard_stats():
    """Add the missing statistics section to the dashboard"""
    
    dashboard_file = "/var/www/html/crypto-bot/index.html"
    
    try:
        with open(dashboard_file, 'r') as f:
            content = f.read()
        
        # Find the card-body section and add the statistics before the table
        stats_section = '''                        <!-- Summary Stats -->
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
                        
'''
        
        # Find the position right after <div class="card-body"> and before the table
        card_body_pattern = r'(<div class="card-body">\s*)(<!-- Trade History Table -->|<div class="table-responsive">|<table)'
        
        if '<!-- Summary Stats -->' not in content:
            import re
            match = re.search(card_body_pattern, content)
            if match:
                # Insert the stats section
                content = content[:match.end(1)] + stats_section + content[match.end(1):]
                print("✅ Added statistics section to dashboard")
            else:
                print("⚠️ Could not find insertion point for statistics")
        else:
            print("✅ Statistics section already exists")
        
        # Also ensure the table has the proper responsive wrapper and styling
        table_pattern = r'<table class="table table-striped">'
        if '<table class="table table-striped table-hover">' not in content:
            content = content.replace(
                '<table class="table table-striped">',
                '<div class="table-responsive">\n                            <table class="table table-striped table-hover">'
            )
            print("✅ Updated table styling")
        
        # Ensure table has the Status column header
        if '<th>Status</th>' not in content:
            content = content.replace(
                '<th>Value (USD)</th>',
                '<th>Value (USD)</th>\n                                        <th>Status</th>'
            )
            print("✅ Added Status column header")
        
        # Ensure table header has proper styling
        if 'table-dark' not in content:
            content = content.replace(
                '<thead>',
                '<thead class="table-dark">'
            )
            print("✅ Updated table header styling")
        
        # Write the updated content back
        with open(dashboard_file, 'w') as f:
            f.write(content)
        
        print("\n✅ Dashboard statistics section fixed!")
        print("🔄 The dashboard now includes:")
        print("   • Trading statistics summary (Total, Buys, Sells, Holds)")
        print("   • Enhanced table styling")
        print("   • Status column in trade history")
        
    except Exception as e:
        print(f"❌ Error fixing dashboard stats: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Fixing Dashboard Statistics Section ===")
    fix_dashboard_stats()
