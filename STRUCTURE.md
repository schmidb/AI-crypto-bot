# Project Structure

## Core Files
- `main.py` - Main bot entry point
- `config.py` - Configuration management
- `coinbase_client.py` - Coinbase API client
- `llm_analyzer.py` - AI analysis engine
- `trading_strategy.py` - Trading strategy implementation
- `data_collector.py` - Market data collection

## Utilities
- `utils/dashboard_updater.py` - Dashboard data updates
- `utils/webserver_sync.py` - Web server synchronization
- `utils/logger.py` - Logging utilities
- `utils/portfolio.py` - Portfolio management
- `utils/strategy_evaluator.py` - Strategy evaluation
- `utils/tax_report.py` - Tax reporting
- `utils/trade_logger.py` - Trade logging

## Dashboard
- `dashboard/` - Web dashboard files
- `deploy_dashboard.py` - Dashboard deployment script

## Configuration
- `.env` - Environment variables (not in git)
- `.env.example` - Environment template
- `requirements.txt` - Python dependencies
- `crypto-bot.service` - Systemd service file

## Data
- `data/` - Runtime data and analysis files
- `logs/` - Application logs

## Virtual Environment
- `venv/` - Python virtual environment (not in git)
