# Python Environment Steering Document

## Python Version & Virtual Environment

### Current Setup
- **Python Version**: 3.11.2
- **Virtual Environment**: `venv` (Python's built-in virtual environment)
- **Location**: `./venv/` (Windows: `venv\` directory)
- **Platform**: Windows (win32)

### Virtual Environment Management

#### Creating Virtual Environment
```bash
# Create venv (already done)
python -m venv venv
```

#### Activating Virtual Environment
```bash
# Windows Command Prompt
venv\Scripts\activate

# Windows PowerShell
venv\Scripts\Activate.ps1

# Deactivate when done
deactivate
```

#### Installing Dependencies
```bash
# Always use venv pip for installations (Windows)
venv\Scripts\pip install -r requirements.txt

# Or if venv is activated
pip install -r requirements.txt
```

### Production Deployment

#### Supervisor Configuration (Linux Production)
- **Python Executable**: `./venv/bin/python` (Linux) / `./venv/Scripts/python.exe` (Windows)
- **Working Directory**: Current project directory
- **User**: Current user
- **Process Management**: Use supervisor for automatic restart and monitoring

#### Linux Supervisor Setup
```ini
# /etc/supervisor/conf.d/crypto-bot.conf
[program:crypto-bot]
command=/home/markus/AI-crypto-bot/venv/bin/python /home/markus/AI-crypto-bot/main.py
directory=/home/markus/AI-crypto-bot
user=markus
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/markus/AI-crypto-bot/logs/supervisor.log
environment=PATH="/home/markus/AI-crypto-bot/venv/bin"
```

#### Supervisor Commands
```bash
# Start/stop/restart the bot
sudo supervisorctl start crypto-bot
sudo supervisorctl stop crypto-bot
sudo supervisorctl restart crypto-bot

# Check status
sudo supervisorctl status crypto-bot

# View logs
sudo supervisorctl tail crypto-bot
```

#### Key Points
1. **Always use venv Python**: `./venv/bin/python` (Linux) / `./venv/Scripts/python.exe` (Windows)
2. **Never use system Python**: Avoid global Python installation for the bot
3. **Dependency isolation**: All packages installed in venv only
4. **Consistent environment**: Same venv for development and production
5. **Process Management**: Use supervisor to prevent duplicate instances and ensure automatic restart

### Development Workflow

#### Setup New Environment
```bash
# Clone repository
git clone <repo-url>
cd AI-crypto-bot

# Create virtual environment
python -m venv venv

# Activate environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Configure environment
copy .env.example .env
# Edit .env with your settings
```

#### Daily Development
```bash
# Always activate venv first (Windows)
venv\Scripts\activate

# Run bot for testing
python main.py

# Install new packages
pip install package-name
pip freeze > requirements.txt

# Deactivate when done
deactivate
```

### Package Management

#### Current Dependencies (Following AI_MODEL_STEERING.md)
- **Core**: `python-dotenv`, `requests`, `pandas`, `numpy`
- **Trading**: `coinbase-advanced-py`
- **AI**: `google-genai` (NEW unified Google AI/Vertex AI SDK), `google-auth`
- **Analysis**: `ta`, `vectorbt`, `pyarrow`
- **Scheduling**: `schedule`
- **Cloud Storage**: `google-cloud-storage`
- **Performance**: `numba`, `fastparquet`

#### Development Dependencies
- **Testing**: `pytest`, `pytest-mock`, `pytest-asyncio`, `pytest-cov`, `pytest-benchmark`
- **Code Quality**: `black`, `isort`, `flake8`, `mypy`, `bandit`
- **Development Tools**: `pre-commit`, `tox`, `sphinx`
- **Debugging**: `pdbpp`, `ipdb`
- **Profiling**: `memory-profiler`, `line-profiler`, `py-spy`

#### Adding New Dependencies
```bash
# Activate venv (Windows)
venv\Scripts\activate

# Install package
pip install new-package

# Update requirements
pip freeze > requirements.txt

# Commit changes
git add requirements.txt
git commit -m "Add new-package dependency"
```

#### Requirements File Management
```bash
# Install production dependencies only
pip install -r requirements.txt

# Install development dependencies (includes production)
pip install -r requirements-dev.txt

# Update all packages to latest versions
pip install --upgrade -r requirements.txt
pip freeze > requirements.txt

# Check for outdated packages
pip list --outdated
```

### Troubleshooting

#### Common Issues
1. **Import errors**: Ensure venv is activated or use `./venv/Scripts/python.exe`
2. **Package not found**: Install in venv, not system Python
3. **Version conflicts**: Use `pip list` to check installed versions
4. **Windows path issues**: Use backslashes `\` for Windows paths

#### Verification Commands
```bash
# Check Python version (Windows)
venv\Scripts\python.exe --version

# Check installed packages
venv\Scripts\pip.exe list

# Verify venv is isolated
venv\Scripts\python.exe -c "import sys; print(sys.path)"

# Check if specific packages are installed
venv\Scripts\pip.exe show google-generativeai
venv\Scripts\pip.exe show coinbase-advanced-py
```

### Best Practices

1. **Always use venv**: Never install packages globally
2. **Consistent activation**: Always activate venv for development
3. **Update requirements.txt**: After installing new packages
4. **Test in venv**: Run all tests with venv Python
5. **Production consistency**: Use same venv setup in production
6. **Separate dev dependencies**: Keep development tools in requirements-dev.txt
7. **Version pinning**: Use `>=` for minimum versions, exact versions for critical packages
8. **Regular updates**: Periodically update dependencies and test compatibility
9. **Use supervisor in production**: Prevent duplicate processes and ensure automatic restart
10. **Check for running processes**: Always verify no duplicate bots before manual starts

### AI Model Configuration (Following AI_MODEL_STEERING.md)

#### Required Configuration
```env
# Use NEW Google AI SDK, not legacy
LLM_PROVIDER=google_ai
LLM_MODEL=gemini-3-flash-preview
LLM_FALLBACK_MODEL=gemini-3-pro-preview
LLM_LOCATION=global

# Authentication: Use existing service account
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GOOGLE_CLOUD_PROJECT=your-project-id

# Optional: API key as fallback (not required if using service account)
# GOOGLE_AI_API_KEY=your_api_key_here
```

#### Package Requirements
- **Use**: `google-genai` (NEW unified Google AI/Vertex AI SDK)
- **Avoid**: `google-generativeai` (legacy first generation SDK)
- **Location**: Must be `global` for preview models
- **Models**: Only `gemini-3-flash-preview` and `gemini-3-pro-preview` supported
- **Authentication**: Service account with AI Platform User role works with new SDK
