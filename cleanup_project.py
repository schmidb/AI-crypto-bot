#!/usr/bin/env python3
"""
Comprehensive project cleanup script
Removes temporary files, test files, and organizes documentation
"""

import os
import shutil
import glob
from pathlib import Path

def cleanup_project():
    """Clean up the project directory"""
    
    print("🧹 Starting comprehensive project cleanup...")
    
    # Files to remove (temporary, test, and debug files)
    files_to_remove = [
        # Test files
        "test_*.py",
        "debug_*.py",
        "check_*.py",
        "advanced_diagnostics.py",
        "fix_*.py",
        "migrate_*.py",
        "complete_currency_migration.py",
        "currency_migration_helper.py",
        "test_config_dashboard.py",
        "test_currency_config.py",
        
        # Temporary documentation files (we'll keep main ones)
        "DASHBOARD_EUR_FIX_SUMMARY.md",
        "DASHBOARD_STYLING_FIX.md", 
        "DASHBOARD_POPUP_IMPROVEMENT_SUMMARY.md",
        "HIGH_CONTRAST_FIX.md",
        "TRADING_BALANCE_STATUS_REMOVAL.md",
        "ENHANCED_AI_ANALYSIS_SUMMARY.md",
        "AI_FIRST_STRATEGY_IMPLEMENTATION.md",
        "CONFIGURATION_DASHBOARD.md",
        "CONFIGURATION_DASHBOARD_SUMMARY.md",
        "DEPLOYMENT_SUMMARY.md",
        "STRATEGY_IMPROVEMENTS_SUMMARY.md",
        "SELL_ORDER_TROUBLESHOOTING.md",
        "ACCOUNT_MIGRATION_SOLUTION.md",
        "CURRENCY_MIGRATION_SUMMARY.md",
        "CURRENCY_MIGRATION_COMPLETE.md",
        "TOOLTIP_IMPROVEMENTS.md",
        "CLEANUP_AND_COMMIT_SUMMARY.md",
        
        # Support files
        "coinbase_support_ticket.txt",
        
        # Recovery scripts (no longer needed)
        "recover_bot_errors.py",
        "restart_bot_with_fixes.py",
    ]
    
    # Directories to clean
    dirs_to_clean = [
        "__pycache__",
        "tests",  # Remove if empty or contains only old tests
        "gcp_setup",  # Setup files no longer needed
        "aws_setup",  # Setup files no longer needed
    ]
    
    removed_files = []
    removed_dirs = []
    
    # Remove files
    for pattern in files_to_remove:
        for file_path in glob.glob(pattern):
            if os.path.exists(file_path):
                os.remove(file_path)
                removed_files.append(file_path)
                print(f"  ❌ Removed: {file_path}")
    
    # Remove directories
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            removed_dirs.append(dir_name)
            print(f"  🗂️ Removed directory: {dir_name}")
    
    # Clean up data directory (remove old analysis files, keep recent ones)
    print("\n🗂️ Cleaning data directory...")
    data_dir = Path("data")
    if data_dir.exists():
        # Keep only recent analysis files (last 7 days)
        import time
        current_time = time.time()
        week_ago = current_time - (7 * 24 * 60 * 60)
        
        analysis_files = list(data_dir.glob("*_EUR_*.json")) + list(data_dir.glob("*_USD_*.json"))
        old_files = []
        
        for file_path in analysis_files:
            if file_path.stat().st_mtime < week_ago:
                file_path.unlink()
                old_files.append(str(file_path))
        
        if old_files:
            print(f"  🗑️ Removed {len(old_files)} old analysis files")
    
    # Clean up logs (keep only recent logs)
    print("\n📋 Cleaning logs directory...")
    logs_dir = Path("logs")
    if logs_dir.exists():
        log_files = list(logs_dir.glob("*.log*"))
        for log_file in log_files:
            if log_file.stat().st_size > 100 * 1024 * 1024:  # > 100MB
                log_file.unlink()
                print(f"  📋 Removed large log: {log_file}")
    
    # Create docs directory and move important documentation
    print("\n📚 Organizing documentation...")
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    # Keep only essential documentation in root
    essential_docs = [
        "README.md",
        ".gitignore",
        "requirements.txt",
        ".env.example",
    ]
    
    print(f"\n✅ Cleanup completed!")
    print(f"  📁 Removed {len(removed_files)} files")
    print(f"  🗂️ Removed {len(removed_dirs)} directories")
    print(f"  📚 Organized documentation")
    
    return removed_files, removed_dirs

def update_gitignore():
    """Update .gitignore to prevent future clutter"""
    
    gitignore_additions = """
# Temporary and test files
test_*.py
debug_*.py
check_*.py
fix_*.py
*_temp.py
*_backup.py

# Documentation drafts
*_SUMMARY.md
*_FIX.md
*_IMPLEMENTATION.md
TEMP_*.md

# Support files
*support_ticket*
*troubleshooting*

# Old data files
data/*_USD_*.json
data/old_*

# Large logs
logs/*.log.*
logs/*_old.log
"""
    
    with open(".gitignore", "a") as f:
        f.write(gitignore_additions)
    
    print("📝 Updated .gitignore with cleanup patterns")

def main():
    """Main cleanup function"""
    print("🤖 AI Crypto Trading Bot - Project Cleanup")
    print("=" * 50)
    
    # Change to project directory
    os.chdir("/home/markus/AI-crypto-bot")
    
    # Run cleanup
    removed_files, removed_dirs = cleanup_project()
    
    # Update gitignore
    update_gitignore()
    
    print("\n🎉 Project cleanup completed successfully!")
    print("\n📋 Summary of changes:")
    print(f"  • Removed {len(removed_files)} temporary/test files")
    print(f"  • Removed {len(removed_dirs)} unnecessary directories") 
    print(f"  • Cleaned old data files")
    print(f"  • Organized documentation")
    print(f"  • Updated .gitignore")
    
    print("\n🚀 Ready for git commit!")

if __name__ == "__main__":
    main()
