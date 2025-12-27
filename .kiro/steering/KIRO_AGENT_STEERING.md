# AI Model Steering

### Required Gemini Models
- **Primary Model**: `gemini-3-flash-preview`
- **Alternative Model**: `gemini-3-pro-preview`

### SDK Requirements
- **Google AI SDK**: Latest version required (not Vertex AI SDK)
- **Location**: `global` (required for preview models)
- **API Endpoint**: Direct Google AI API, not Vertex AI

### Configuration Example
```python
import google.generativeai as genai

# Configure with global location for preview models
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-3-flash-preview')
```

### Key Requirements
1. Use Google AI SDK (`google-generativeai`), not Vertex AI SDK
2. Set location to `global` for preview model access
3. Ensure API key has access to preview models
4. Use direct Google AI API endpoints

### Migration Notes
- Preview models are only available through Google AI SDK
- Vertex AI SDK does not support these preview models
- Location must be `global` - regional endpoints don't support preview models
