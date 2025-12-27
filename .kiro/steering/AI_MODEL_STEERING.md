# AI Model Steering

### CRITICAL LIBRARY UPDATE
**IMPORTANT**: Use the NEW `google-genai` library, NOT the legacy `google-generativeai` library!

### Required Gemini Models
- **Primary Model**: `gemini-3-flash-preview`
- **Alternative Model**: `gemini-3-pro-preview`

### SDK Requirements
- **NEW Library**: `google-genai` (supports both Google AI and Vertex AI)
- **OLD Library**: `google-generativeai` (legacy, first generation SDK)
- **Location**: `global` (required for preview models)
- **Client**: Use `genai.Client()` from the new library

### Authentication Options
The new `google-genai` library supports multiple authentication methods:

#### Option 1: Service Account with Vertex AI (Recommended for Production)
```python
import google.genai as genai
from google.oauth2 import service_account

# Load service account credentials
credentials = service_account.Credentials.from_service_account_file(
    'path/to/service-account.json',
    scopes=['https://www.googleapis.com/auth/cloud-platform']
)

# Create client with service account - MUST use vertexai=True for service accounts
client = genai.Client(
    vertexai=True,  # CRITICAL: Use Vertex AI for service account authentication
    project=GOOGLE_CLOUD_PROJECT,
    location='global',
    credentials=credentials
)
```

#### Option 2: API Key with Google AI Studio
```python
import google.genai as genai

# Create client with API key - uses Google AI Studio (public API)
client = genai.Client(
    vertexai=False,  # Use Google AI Studio with API key
    api_key=api_key  # Project and location ignored with vertexai=False
)
```

#### Option 3: Default Credentials with Vertex AI
```python
import google.genai as genai

# Use default credentials (ADC) with Vertex AI
client = genai.Client(
    vertexai=True,  # CRITICAL: Use Vertex AI for GCP credentials
    project=GOOGLE_CLOUD_PROJECT,
    location='global'
)
```

### Configuration Example
```python
import google.genai as genai
from google.genai import types

# Create client - Choose based on authentication method
# For Service Account (Production):
client = genai.Client(
    vertexai=True,  # CRITICAL: Use Vertex AI for service accounts
    project=GOOGLE_CLOUD_PROJECT,
    location='global',
    credentials=credentials
)

# For API Key (Development):
client = genai.Client(
    vertexai=False,  # Use Google AI Studio for API keys
    api_key=api_key
)

# Generate content
response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents=['Your prompt here'],
    config=types.GenerateContentConfig(
        temperature=0.2,
        max_output_tokens=10000
    )
)
```

### Key Requirements
1. **Use NEW Library**: `google-genai`, NOT `google-generativeai`
2. **Client Creation**: Use `genai.Client()` with correct `vertexai` setting:
   - `vertexai=True` for service accounts and Vertex AI (Enterprise/GCP)
   - `vertexai=False` for API keys and Google AI Studio (Public API)
3. **Location**: Must be `global` for preview model access (Vertex AI only)
4. **Models**: Only preview models supported with new client
5. **API Calls**: Use `client.models.generate_content()` method

### Installation
```bash
# Install the NEW library
pip install google-genai

# Remove the OLD library if present
pip uninstall google-generativeai
```

### Service Account Permissions
If using service account authentication, ensure it has:
- **AI Platform User** role
- **Generative AI User** role (if available)
- Access to preview models in your Google Cloud project

### Migration Notes
- **NEW**: `google-genai` with `import google.genai as genai` and `genai.Client()`
- **OLD**: `google-generativeai` with `import google.generativeai as genai` and `genai.GenerativeModel()`
- Preview models work with both Google AI and Vertex AI through the new client
- The new library unifies access to both Google AI and Vertex AI APIs
- Service account credentials work with the new client
- Location must be `global` for preview models
