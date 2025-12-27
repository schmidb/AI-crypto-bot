#!/usr/bin/env python3

import os
import sys
import google.genai as genai
from google.oauth2 import service_account

# Load credentials
GOOGLE_APPLICATION_CREDENTIALS = "/home/markus/intense-base-456414-u5-01cb88d878f7.json"

try:
    print("Testing gemini-3-flash-preview with GLOBAL location...")
    
    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_APPLICATION_CREDENTIALS,
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    
    client = genai.Client(
        vertexai=True,
        project="intense-base-456414-u5",
        location="global",  # <-- THE FIX!
        credentials=credentials
    )
    print("✅ Client initialized with global location")
    
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents="What is 2+2? Respond with just the number."
    )
    
    print(f"✅ SUCCESS! gemini-3-flash-preview is working with global location!")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
