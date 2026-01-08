# Manifold Markets Alert Bot

A simple, robust console-based alert bot that monitors Manifold Markets for suspicious trading activity.

## Features

Detects 4 types of signals (priority order):

1. **WHALE_BET** - Large bets ≥5x the market's recent average
2. **NEW_ACCOUNT_LARGE_BET** - Accounts <7 days old placing above-average bets
3. **SHARP_MOVEMENT** - Probability changes ≥10% in under 5 minutes
4. **HIGH_SKILL_USER** - Bets from users with strong profit track records

## Installation

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Basic usage (45s scan interval)
python main.py

# Custom scan interval (30 seconds)
python main.py --interval 30

# With debug logging
python main.py --debug

# Full options
python main.py --interval 45 --bets 100 --debug
```

### Command Line Options

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--interval` | `-i` | 45 | Scan interval in seconds |
| `--bets` | `-b` | 100 | Number of bets to fetch per scan |
| `--debug` | `-d` | false | Enable debug logging |

## Alert Format

```
============================================================
[ALERT] WHALE_BET
Market: Will AI achieve AGI by 2030?
User: trader123
Bet Amount: M5,000
Probability: 45.2% -> 52.8%
Timestamp: 2025-01-15 14:32:18 UTC
Details: 8.3x market avg (avg: M602)
============================================================
```

## Architecture

```
manifold-alert-bot/
├── main.py           # Main loop + console output
├── data_fetcher.py   # Manifold API interactions
├── signal_engine.py  # Detection logic
├── requirements.txt  # Dependencies
└── README.md         # This file
```

## Configuration

Default thresholds (can be modified in `signal_engine.py`):

- **Whale threshold**: 5x market average
- **New account age**: 7 days
- **Sharp movement**: 10% in 5 minutes
- **Min bet for whale alert**: M100
- **Min profit for high-skill**: M500

## API Rate Limits

The bot respects Manifold's rate limit of 500 requests/minute. Built-in rate limiting ensures safe operation.

## Stopping the Bot

Press `Ctrl+C` to gracefully stop the bot. A session summary will be displayed.

## License

MIT
