# Local Development Setup

Complete guide for setting up the AI crypto trading bot for local development on Windows, macOS, and Linux.

## Prerequisites

- Python 3.11 or higher
- Git
- API keys from Coinbase and Google Cloud
- Text editor or IDE (VS Code recommended)

## Quick Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/AI-crypto-bot.git
cd AI-crypto-bot
```

### 2. Create Virtual Environment

#### Windows
```cmd
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

### 4. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration
nano .env  # or use your preferred editor
```

### 5. Run in Simulation Mode

```bash
# Always start in simulation mode for development
python main.py
```

## Detailed Setup Guide

### Python Environment Setup

#### Version Requirements

The bot requires Python 3.11 or higher. Check your version:

```bash
python --version
# or
python3 --version
```

#### Installing Python 3.11

**Windows:**
1. Download from [python.org](https://www.python.org/downloads/)
2. Run installer with "Add to PATH" checked
3. Verify installation: `python --version`

**macOS:**
```bash
# Using Homebrew
brew install python@3.11

# Using pyenv
pyenv install 3.11.7
pyenv local 3.11.7
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip
```

**Linux (CentOS/RHEL):**
```bash
sudo dnf install python3.11 python3.11-pip
```

### Virtual Environment Best Practices

#### Creating Isolated Environment

```bash
# Create virtual environment
python -m venv venv

# Activate environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Verify activation (should show venv path)
which python
```

#### Managing Dependencies

```bash
# Install from requirements
pip install -r requirements.txt

# Add new dependency
pip install new-package

# Update requirements file
pip freeze > requirements.txt

# Install development tools
pip install -r requirements-dev.txt
```

### Development Configuration

#### Environment Variables

Create `.env` file with development settings:

```env
# Development Configuration
SIMULATION_MODE=true                # Always true for development
TESTING=false                      # Set to true when running tests
DEBUG_MODE=true                    # Enable debug features

# API Configuration (Required)
COINBASE_API_KEY=organizations/your-org-id/apiKeys/your-key-id
COINBASE_API_SECRET=-----BEGIN EC PRIVATE KEY-----...
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Development Settings
DECISION_INTERVAL_MINUTES=5        # Faster decisions for testing
MIN_TRADE_AMOUNT=1.0              # Lower minimum for testing
LOG_LEVEL=DEBUG                   # Verbose logging
NOTIFICATIONS_ENABLED=false       # Disable notifications
WEBSERVER_SYNC_ENABLED=false      # Disable dashboard sync

# Email (Optional for development)
GMAIL_USER=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-password
```

#### Google Cloud Setup for Development

1. **Create Service Account:**
   ```bash
   gcloud iam service-accounts create crypto-bot-dev \
       --description="Development service account" \
       --display-name="Crypto Bot Dev"
   ```

2. **Grant Permissions:**
   ```bash
   gcloud projects add-iam-policy-binding your-project-id \
       --member="serviceAccount:crypto-bot-dev@your-project-id.iam.gserviceaccount.com" \
       --role="roles/aiplatform.user"
   ```

3. **Download Key:**
   ```bash
   gcloud iam service-accounts keys create ~/crypto-bot-dev-key.json \
       --iam-account=crypto-bot-dev@your-project-id.iam.gserviceaccount.com
   ```

4. **Set Environment Variable:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=~/crypto-bot-dev-key.json
   ```

### Development Tools

#### Code Quality Tools

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Code formatting
black .
isort .

# Linting
flake8 .
pylint *.py

# Type checking
mypy .

# Security scanning
bandit -r .
```

#### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

### IDE Configuration

#### VS Code Setup

Install recommended extensions:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-python.flake8",
    "ms-python.mypy-type-checker",
    "ms-vscode.vscode-json"
  ]
}
```

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pytest_cache": true,
    "venv": true
  }
}
```

Create `.vscode/launch.json` for debugging:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Main Bot",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/main.py",
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env",
      "cwd": "${workspaceFolder}"
    },
    {
      "name": "Python: Run Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/", "-v"],
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env",
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

#### PyCharm Setup

1. **Open Project:** File → Open → Select project directory
2. **Configure Interpreter:** File → Settings → Project → Python Interpreter → Add → Existing environment → Select `venv/bin/python`
3. **Configure Run Configuration:**
   - Run → Edit Configurations
   - Add new Python configuration
   - Script path: `main.py`
   - Environment variables: Load from `.env`

### Running the Bot

#### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run with debug logging
python main.py

# Run with specific log level
LOG_LEVEL=DEBUG python main.py

# Run single iteration (for testing)
python -c "
from main import main_trading_loop
main_trading_loop(single_run=True)
"
```

#### Component Testing

```bash
# Test configuration loading
python -c "from config import Config; c = Config(); print('Config loaded successfully')"

# Test Coinbase API connection
python -c "
from coinbase_client import CoinbaseClient
client = CoinbaseClient()
accounts = client.get_accounts()
print(f'Connected to Coinbase: {len(accounts)} accounts')
"

# Test Google AI connection
python -c "
from llm_analyzer import LLMAnalyzer
analyzer = LLMAnalyzer()
result = analyzer.analyze_with_llm('Test prompt')
print('Google AI connection successful')
"

# Test portfolio operations
python -c "
from portfolio import Portfolio
portfolio = Portfolio()
print(f'Portfolio loaded: {portfolio.calculate_total_value()} EUR')
"
```

### Testing

#### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_portfolio.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run with specific markers
pytest -m "not slow"
```

#### Test Configuration

Create `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --disable-warnings
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

#### Writing Tests

Example test structure:

```python
# tests/unit/test_example.py
import pytest
from unittest.mock import Mock, patch
from your_module import YourClass

class TestYourClass:
    def setup_method(self):
        """Setup for each test method"""
        self.instance = YourClass()
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        result = self.instance.some_method()
        assert result is not None
    
    @patch('your_module.external_dependency')
    def test_with_mock(self, mock_dependency):
        """Test with mocked dependencies"""
        mock_dependency.return_value = "mocked_value"
        result = self.instance.method_using_dependency()
        assert result == "expected_result"
```

### Debugging

#### Debug Configuration

```python
# Add to main.py for debugging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add breakpoints
import pdb; pdb.set_trace()  # Python debugger
```

#### Common Debug Scenarios

```bash
# Debug configuration issues
python -c "
from config import Config
import os
print('Environment variables:')
for key in ['COINBASE_API_KEY', 'GOOGLE_CLOUD_PROJECT']:
    print(f'{key}: {os.getenv(key, \"NOT SET\")}')
"

# Debug API connections
python -c "
import requests
response = requests.get('https://api.coinbase.com/api/v3/brokerage/time')
print(f'Coinbase API status: {response.status_code}')
"

# Debug portfolio state
python -c "
from portfolio import Portfolio
import json
portfolio = Portfolio()
print(json.dumps(portfolio.to_dict(), indent=2))
"
```

### Performance Profiling

#### Memory Profiling

```bash
# Install memory profiler
pip install memory-profiler

# Profile memory usage
python -m memory_profiler main.py

# Line-by-line profiling
@profile
def your_function():
    # Your code here
    pass
```

#### CPU Profiling

```bash
# Install profiling tools
pip install py-spy line-profiler

# Profile running process
py-spy top --pid <process_id>

# Generate flame graph
py-spy record -o profile.svg -- python main.py
```

### Development Workflow

#### Daily Development

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Pull latest changes
git pull origin main

# 3. Update dependencies if needed
pip install -r requirements.txt

# 4. Run tests
pytest

# 5. Start development
python main.py

# 6. Before committing
black .
isort .
flake8 .
pytest
```

#### Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Develop and test
# ... make changes ...
pytest tests/

# 3. Format and lint
black .
isort .
flake8 .

# 4. Commit changes
git add .
git commit -m "Add new feature"

# 5. Push and create PR
git push origin feature/new-feature
```

### Troubleshooting

#### Common Issues

**1. Import Errors:**
```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Ensure virtual environment is activated
which python
```

**2. API Connection Issues:**
```bash
# Test network connectivity
ping api.coinbase.com
ping googleapis.com

# Check firewall/proxy settings
curl -I https://api.coinbase.com/api/v3/brokerage/time
```

**3. Permission Issues:**
```bash
# Check file permissions
ls -la .env
ls -la path/to/service-account.json

# Fix permissions if needed
chmod 600 .env
chmod 600 path/to/service-account.json
```

**4. Virtual Environment Issues:**
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Debug Logging

Enable comprehensive logging:

```python
import logging
import sys

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Reduce noise from external libraries
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
```

This comprehensive guide ensures a smooth local development experience for the AI crypto trading bot.