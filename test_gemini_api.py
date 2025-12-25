#!/usr/bin/env python3

import os
import sys
import google.genai as genai
from google.genai import types
from google.oauth2 import service_account

# Load credentials
GOOGLE_APPLICATION_CREDENTIALS = "google.json"
MODEL = "gemini-3-flash-preview"

try:
    print("Testing Gemini API with new Vertex AI Service Agent role...")
    
    # Initialize with service account
    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_APPLICATION_CREDENTIALS
    )
    client = genai.Client(vertexai=True, credentials=credentials)
    print("✅ Client initialized successfully")
    
    # Test simple generation
    response = client.models.generate_content(
        model=MODEL,
        contents=["What is 2+2? Respond with just the number."],
        config=types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=10
        )
    )
    
    print(f"✅ API call successful!")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
