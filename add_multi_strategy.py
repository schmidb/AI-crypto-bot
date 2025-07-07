#!/usr/bin/env python3
"""
Script to add multi-strategy sections to the dashboard
"""

import re

def add_multi_strategy_section():
    # Read the current dashboard file
    with open('dashboard/static/index.html', 'r') as f:
        content = f.read()
    
    # Multi-strategy HTML section
    multi_strategy_html = '''                                        <!-- Multi-Strategy Analysis -->
                                        <div class="multi-strategy-section mb-3" style="border: 1px solid #e0e0e0; border-radius: 8px; padding: 12px; background: #f8f9fa;">
                                            <div class="strategy-header mb-2">
                                                <small class="text-muted"><i class="fas fa-chess-board me-1"></i>Multi-Strategy Analysis:</small>
                                                <span class="market-regime-badge badge bg-info ms-2">--</span>
                                            </div>
                                            
                                            <!-- Combined Signal -->
                                            <div class="combined-signal mb-2">
                                                <div class="d-flex justify-content-between align-items-center">
                                                    <small><strong>Combined Signal:</strong></small>
                                                    <span class="combined-action-badge badge bg-secondary">--</span>
                                                </div>
                                                <div class="confidence-bar-container mt-1">
                                                    <div class="confidence-bar">
                                                        <div class="confidence-fill" style="width: 0%;"></div>
                                                    </div>
                                                    <small class="confidence-text">0%</small>
                                                </div>
                                            </div>
                                            
                                            <!-- Individual Strategies -->
                                            <div class="individual-strategies" style="display: none;">
                                                <small class="text-muted d-block mb-1">Individual Strategy Signals:</small>
                                                <div class="strategy-signals">
                                                    <div class="strategy-signal" data-strategy="trend_following">
                                                        <span class="strategy-name">Trend Following:</span>
                                                        <span class="strategy-action badge bg-secondary">--</span>
                                                        <span class="strategy-confidence">--</span>
                                                    </div>
                                                    <div class="strategy-signal" data-strategy="mean_reversion">
                                                        <span class="strategy-name">Mean Reversion:</span>
                                                        <span class="strategy-action badge bg-secondary">--</span>
                                                        <span class="strategy-confidence">--</span>
                                                    </div>
                                                    <div class="strategy-signal" data-strategy="momentum">
                                                        <span class="strategy-name">Momentum:</span>
                                                        <span class="strategy-action badge bg-secondary">--</span>
                                                        <span class="strategy-confidence">--</span>
                                                    </div>
                                                </div>
                                            </div>
                                            
                                            <!-- Expand/Collapse Button -->
                                            <button class="btn btn-sm btn-outline-secondary mt-2 expand-strategies" type="button">
                                                <i class="fas fa-chevron-down me-1"></i>Show Strategy Details
                                            </button>
                                        </div>
                                        
'''
    
    # Pattern to find the location to insert multi-strategy section
    # Look for the existing comment that was already added
    pattern = r'(<!-- Enhanced Decision Analysis -->\s*<!-- Multi-Strategy Analysis -->)'
    
    # Replace with the complete multi-strategy section
    replacement = multi_strategy_html + r'                                        <!-- Enhanced Decision Analysis -->'
    
    # Apply the replacement
    new_content = re.sub(pattern, replacement, content)
    
    # Check if replacements were made
    if new_content != content:
        # Write the updated content back
        with open('dashboard/static/index.html', 'w') as f:
            f.write(new_content)
        print("✅ Multi-strategy sections added to dashboard")
        
        # Count how many sections were added
        count = content.count('<!-- Enhanced Decision Analysis -->') - new_content.count('<!-- Enhanced Decision Analysis -->')
        print(f"📊 Added multi-strategy analysis to {abs(count)} asset cards")
    else:
        print("❌ No changes made - pattern not found or already exists")

if __name__ == "__main__":
    add_multi_strategy_section()
