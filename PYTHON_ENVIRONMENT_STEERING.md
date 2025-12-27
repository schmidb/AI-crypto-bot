# Python Environment Steering Document

## Python Version & Virtual Environment

### Current Setup
- **Python Version**: 3.11.2
- **Virtual Environment**: `venv` (Python's built-in virtual environment)
- **Location**: `/home/markus/AI-crypto-bot/venv/`

### Virtual Environment Management

#### Creating Virtual Environment
```bash
# Create venv (already done)
python3 -m venv venv
```

#### Activating Virtual Environment
```bash
# Activate venv for development
source venv/bin/activate

# Deactivate when done
deactivate
```

#### Installing Dependencies
```bash
# Always use venv pip for installations
./venv/bin/pip install -r requirements.txt

# Or if venv is activated
pip install -r requirements.txt
```

### Production Deployment

#### Supervisor Configuration
- **Python Executable**: `/home/markus/AI-crypto-bot/venv/bin/python`
- **Working Directory**: `/home/markus/AI-crypto-bot`
- **User**: `markus`

#### Key Points
1. **Always use venv Python**: `./venv/bin/python` for production
2. **Never use system Python**: Avoid `/usr/bin/python3` for the bot
3. **Dependency isolation**: All packages installed in venv only
4. **Consistent environment**: Same venv for development and production

### Development Workflow

#### Setup New Environment
```bash
# Clone repository
git clone <repo-url>
cd AI-crypto-bot

# Create virtual environment
python3 -m venv venv

# Activate environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

#### Daily Development
```bash
# Always activate venv first
source venv/bin/activate

# Run bot for testing
python main.py

# Install new packages
pip install package-name
pip freeze > requirements.txt

# Deactivate when done
deactivate
```

### Package Management

#### Current Dependencies
- Core: `python-dotenv`, `requests`, `pandas`, `numpy`
- Trading: `coinbase-advanced-py`
- AI: `google-genai`, `google-auth`
- Analysis: `ta`, `vectorbt`, `pyarrow`
- Scheduling: `schedule`

#### Adding New Dependencies
```bash
# Activate venv
source venv/bin/activate

# Install package
pip install new-package

# Update requirements
pip freeze > requirements.txt

# Commit changes
git add requirements.txt
git commit -m "Add new-package dependency"
```

### Troubleshooting

#### Common Issues
1. **Import errors**: Ensure venv is activated or use `./venv/bin/python`
2. **Package not found**: Install in venv, not system Python
3. **Version conflicts**: Use `pip list` to check installed versions

#### Verification Commands
```bash
# Check Python version
./venv/bin/python --version

# Check installed packages
./venv/bin/pip list

# Verify venv is isolated
./venv/bin/python -c "import sys; print(sys.path)"
```

### Best Practices

1. **Always use venv**: Never install packages globally
2. **Consistent activation**: Always activate venv for development
3. **Update requirements.txt**: After installing new packages
4. **Test in venv**: Run all tests with venv Python
5. **Production consistency**: Use same venv setup in production
