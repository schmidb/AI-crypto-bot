#!/usr/bin/env python3
"""
Simple HTTP server for the AI Crypto Bot Dashboard
Run this script to serve the dashboard locally for testing
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Change to the project directory
project_dir = Path(__file__).parent
os.chdir(project_dir)

PORT = 8080
DASHBOARD_DIR = "dashboard/static"

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DASHBOARD_DIR, **kwargs)
    
    def end_headers(self):
        # Add CORS headers for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    if not os.path.exists(DASHBOARD_DIR):
        print(f"Error: Dashboard directory '{DASHBOARD_DIR}' not found!")
        sys.exit(1)
    
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"🚀 AI Crypto Bot Dashboard Server")
        print(f"📊 Serving dashboard at: http://localhost:{PORT}")
        print(f"📁 Directory: {os.path.abspath(DASHBOARD_DIR)}")
        print(f"🔄 Press Ctrl+C to stop the server")
        print("-" * 50)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            httpd.shutdown()
