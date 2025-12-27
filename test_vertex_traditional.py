#!/usr/bin/env python3

import vertexai
from vertexai.generative_models import GenerativeModel

try:
    print("Testing traditional Vertex AI approach...")
    
    # Initialize Vertex AI
    vertexai.init(project="intense-base-456414-u5", location="global")
    print("✅ Vertex AI initialized")
    
    # Create model
    model = GenerativeModel("gemini-1.5-flash")
    print("✅ Model created")
    
    # Test generation
    response = model.generate_content("What is 2+2? Just the number.")
    print(f"✅ Response: {response.text}")
    
except Exception as e:
    print(f"❌ Error: {e}")
