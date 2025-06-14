# Uptime Management

The bot now features persistent uptime tracking that distinguishes between restarts and explicit stops across all service management systems.

## How It Works

### Uptime Persistence
- **Restarts**: Configuration changes, updates, or service restarts preserve uptime
- **Explicit Stops**: Only manual stops or explicit stop commands reset the uptime counter
- **Crash Recovery**: Automatic restarts after crashes preserve uptime

### Service Manager Support
- **Systemd**: Full support for restart vs stop distinction
- **Supervisor**: Full support for restart vs stop distinction  
- **Standalone**: Direct bot_manager.py commands

### Uptime Data Storage
- `data/cache/bot_uptime.json` - Persistent uptime tracking data
- `data/cache/bot_startup.json` - Current session information (updated with uptime data)

## Usage

### Bot Manager Script (Recommended)
Use the `bot_manager.py` script for proper uptime management:

```bash
# Start the bot
python bot_manager.py start

# Restart the bot (preserves uptime)
python bot_manager.py restart

# Stop the bot (resets uptime)
python bot_manager.py stop

# Check status and uptime
python bot_manager.py status
```

### Systemd Service (AWS EC2)
The systemd service is configured to handle graceful shutdowns:

```bash
# Restart (preserves uptime)
sudo systemctl restart crypto-bot

# Stop (resets uptime)
sudo systemctl stop crypto-bot

# Start
sudo systemctl start crypto-bot

# Enhanced commands via bot_manager
python bot_manager.py systemctl-restart  # Explicit restart
python bot_manager.py systemctl-stop     # Explicit stop
```

### Supervisor Service (Google Cloud)
The supervisor service supports proper uptime tracking:

```bash
# Restart (preserves uptime)
sudo supervisorctl restart crypto-bot
# OR use the enhanced script:
sudo /usr/local/bin/crypto-bot-restart

# Stop (resets uptime)
sudo supervisorctl stop crypto-bot
# OR use the enhanced script:
sudo /usr/local/bin/crypto-bot-stop

# Enhanced commands via bot_manager
python bot_manager.py supervisorctl-restart  # Explicit restart
python bot_manager.py supervisorctl-stop     # Explicit stop
```

### Dashboard Display
The dashboard now shows:
- **Total Uptime**: Cumulative uptime across all sessions
- **Restart Count**: Number of restarts since original start
- **Session Time**: Current session duration (if different from total)
- **Service Manager**: Detected service management system

## Technical Details

### Restart Detection
The bot automatically detects restarts by:
1. Checking environment variables (`BOT_RESTART_CONTEXT`)
2. Examining parent process information
3. Looking for existing uptime data and recent activity
4. Analyzing signal context and service manager type

### Signal Handling
- **SIGTERM**: Context-dependent (restart vs stop based on environment)
- **SIGINT**: Always treated as explicit stop (Ctrl+C)
- **Environment Variables**: `BOT_RESTART_CONTEXT=restart|stop`

### Uptime Calculation
- **Total Uptime** = Previous sessions + Current session
- **Previous Sessions** = Accumulated time from clean shutdowns
- **Current Session** = Time since current startup

### Data Structure
```json
{
  "original_start_time": "2025-06-13T10:00:00.000000",
  "current_session_start": "2025-06-13T15:30:00.000000",
  "total_uptime_seconds": 19800,
  "restart_count": 3,
  "status": "running"
}
```

## Uptime Behavior Matrix

| Command | AWS (systemd) | GCP (supervisor) | Standalone | Uptime Behavior |
|---------|---------------|------------------|------------|-----------------|
| `systemctl restart` | ✅ Preserves | N/A | N/A | **PRESERVES** |
| `systemctl stop` | ✅ Resets | N/A | N/A | **RESETS** |
| `supervisorctl restart` | N/A | ✅ Preserves | N/A | **PRESERVES** |
| `supervisorctl stop` | N/A | ✅ Resets | N/A | **RESETS** |
| `bot_manager.py restart` | ✅ Preserves | ✅ Preserves | ✅ Preserves | **PRESERVES** |
| `bot_manager.py stop` | ✅ Resets | ✅ Resets | ✅ Resets | **RESETS** |
| Process crash/kill | ✅ Preserves | ✅ Preserves | ✅ Preserves | **PRESERVES** |
| Ctrl+C (SIGINT) | ✅ Resets | ✅ Resets | ✅ Resets | **RESETS** |

## Migration

Existing bots will automatically:
1. Detect they are running for the first time with the new system
2. Initialize uptime tracking from the current session
3. Preserve uptime on subsequent restarts

No manual migration is required.

## Benefits

1. **Accurate Monitoring**: True uptime tracking across maintenance windows
2. **Better Insights**: Distinguish between planned restarts and issues
3. **Professional Display**: Dashboard shows meaningful uptime metrics
4. **Operational Clarity**: Clear distinction between stops and restarts
5. **Service Manager Agnostic**: Works with systemd, supervisor, and standalone
6. **Context Awareness**: Intelligent signal interpretation based on environment
