#!/usr/bin/env python3

import os
import shutil

def test_template_sync():
    """Test the template syncing logic"""
    web_dashboard_dir = "/var/www/html/crypto-bot"
    templates_dir = "dashboard_templates"
    
    print(f"Current working directory: {os.getcwd()}")
    print(f"Templates directory exists: {os.path.exists(templates_dir)}")
    
    if os.path.exists(templates_dir):
        print(f"Contents of {templates_dir}:")
        files = os.listdir(templates_dir)
        for file in files:
            print(f"  - {file}")
        
        html_files = [f for f in files if f.endswith(".html")]
        print(f"HTML files found: {html_files}")
        
        for file in html_files:
            src = f"{templates_dir}/{file}"
            dst = f"{web_dashboard_dir}/{file}"
            print(f"Would copy: {src} -> {dst}")
            
            # Check if source exists and is readable
            if os.path.exists(src):
                print(f"  Source exists: {src}")
                try:
                    shutil.copy2(src, dst)
                    print(f"  Successfully copied {file}")
                except Exception as e:
                    print(f"  Error copying {file}: {e}")
            else:
                print(f"  Source does not exist: {src}")
    else:
        print(f"Templates directory does not exist: {templates_dir}")

if __name__ == "__main__":
    test_template_sync()
