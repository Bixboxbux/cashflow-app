# IBKR Options Trading Assistant

A professional, read-only options signal analysis dashboard for Interactive Brokers. This system monitors options chains and generates alerts based on unusual activity patterns—**without ever placing trades automatically**.

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     📊  IBKR OPTIONS TRADING ASSISTANT                      ║
║                                                              ║
║     Signal Analysis Dashboard for Options Traders            ║
║                                                              ║
║     ⚠️  READ-ONLY MODE - NO AUTOMATED TRADING               ║
║     📋  Paper Trading Connection Only                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

## Safety First

This system is designed with **safety as the #1 priority**:

- **READ-ONLY**: No order placement, no account modifications
- **PAPER TRADING ONLY**: Refuses to connect to live trading ports
- **ALERTS ONLY**: All decisions require manual human execution
- **TRANSPARENT**: All confidence scores show detailed breakdowns

## Features

### Signal Detection

The system monitors for 4 types of options signals:

| Signal | Description | Threshold |
|--------|-------------|-----------|
| 📊 **Unusual Volume** | Volume significantly above average | ≥ 3x normal |
| 📈 **OI Acceleration** | Rapid open interest increase | ≥ 20% change |
| ⚡ **IV Spike** | Implied volatility surge | ≥ 15% increase |
| 🎯 **Delta Momentum** | Price movement aligned with delta | Directional confirmation |

### Decision Engine

Generates recommendations based on weighted signal analysis:

- **BUY**: Confidence ≥ 65% + Bullish signals
- **SELL**: Confidence ≥ 65% + Bearish signals
- **WAIT**: Confidence < 65% or unclear direction

Confidence scores factor in:
- Signal strength and count
- Volatility penalty (high IV = lower confidence)
- Liquidity bonus (high volume = higher confidence)
- Spread penalty (wide bid-ask = lower confidence)
- Convergence bonus (multiple aligned signals)

### Dashboard

Beautiful, mobile-friendly web interface:

- Dark mode design
- Color-coded decisions (green/red/yellow)
- Visual confidence bars
- Filtering by symbol, type, decision, confidence
- Real-time auto-refresh
- Responsive for mobile devices

## Quick Start

### Option 1: Demo Mode (No IBKR Required)

Try the dashboard with simulated data:

```bash
# Linux/Mac
./launch.sh --demo

# Windows PowerShell
.\launch.ps1 -Demo
```

Open http://localhost:8080 in your browser.

### Option 2: Live Mode (IBKR Paper Trading)

1. **Start TWS or IB Gateway** with Paper Trading account
2. **Enable API connections** in TWS:
   - File → Global Configuration → API → Settings
   - Check "Enable ActiveX and Socket Clients"
   - Check "Read-Only API"
   - Port: 7497 (Paper Trading)
3. **Run the assistant**:

```bash
# Linux/Mac
./launch.sh

# Windows PowerShell
.\launch.ps1
```

## Installation

### Requirements

- Python 3.9 or higher
- TWS or IB Gateway (for live mode)
- Paper Trading account (live accounts blocked)

### Manual Installation

```bash
# Clone or download the project
cd ibkr-options-assistant

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run
python main.py --demo  # or without --demo for live
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `IBKR_HOST` | IBKR host address | 127.0.0.1 |
| `IBKR_PORT` | IBKR port (7497=paper) | 7497 |
| `IBKR_CLIENT_ID` | Client ID | 1 |
| `UI_PORT` | Dashboard port | 8080 |
| `WATCHLIST` | Comma-separated symbols | NVDA,AAPL,MSFT... |

### Watchlist

Default symbols monitored:
- NVDA, AAPL, MSFT, GOOGL, AMZN
- META, TSLA, AMD, SPY, QQQ

Edit `config.py` to customize.

## Project Structure

```
ibkr-options-assistant/
├── config.py               # Configuration settings
├── data_fetcher_ibkr.py    # IBKR connection & data fetching
├── options_chain_engine.py # Options chain processing
├── signal_engine.py        # Signal detection (4 types)
├── decision_engine.py      # BUY/SELL/WAIT decisions
├── ui_dashboard.py         # FastAPI web dashboard
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── launch.sh               # Linux/Mac launcher
├── launch.ps1              # Windows launcher
├── static/
│   ├── css/styles.css      # Dashboard styles
│   └── js/app.js           # Dashboard JavaScript
├── templates/
│   └── index.html          # Dashboard template
└── logs/
    ├── system.log          # System logs
    └── alerts.log          # Alert history
```

## Example Alert

```
╭──────────────────────────────────────────────────────────╮
│  NVDA                                    BUY             │
│  📈 CALL                                                 │
├──────────────────────────────────────────────────────────┤
│  Strike: $200          Expiration: Jan 16, 2026 (3 DTE)  │
├──────────────────────────────────────────────────────────┤
│  Confidence: ████████████████████░░░░░░░░░░  78.5%       │
├──────────────────────────────────────────────────────────┤
│  Underlying    $198.50      │  Option Price  $5.30       │
│  Volume        15,420 (4.8x)│  Open Interest 45,000      │
│  IV            52.3%        │  Delta         0.520       │
│  Bid/Ask       $5.20/$5.40  │  Spread        3.7%        │
├──────────────────────────────────────────────────────────┤
│  Signals (2):                                            │
│  📊 Vol 85% | Volume 4.8x average                        │
│  📈 OI  72% | OI increased 28%                           │
╰──────────────────────────────────────────────────────────╯
```

## Signal Interpretation Guide

### Unusual Volume 📊
**What it means**: More contracts trading than normal
**Possible causes**: Informed trading, hedging, news anticipation
**Caution**: High volume alone doesn't indicate direction

### OI Acceleration 📈
**What it means**: New positions being established
**Possible causes**: Institutional positioning, anticipation of move
**Caution**: Could be hedges against existing positions

### IV Spike ⚡
**What it means**: Market expects larger price movement
**Possible causes**: Earnings, FDA decisions, legal rulings
**Caution**: High IV = expensive options, may already be priced in

### Delta Momentum 🎯
**What it means**: Underlying moving favorably for option
**Possible causes**: Trend continuation, momentum
**Caution**: Trends can reverse quickly

## API Endpoints

The dashboard exposes a REST API:

| Endpoint | Description |
|----------|-------------|
| `GET /api/alerts` | Get filtered alerts |
| `GET /api/alerts/{id}` | Get alert details |
| `GET /api/status` | System status |
| `GET /api/summary` | Summary statistics |
| `GET /api/symbols` | Available symbols |
| `GET /health` | Health check |

API documentation: http://localhost:8080/api/docs

## Troubleshooting

### "Connection refused" error
- Ensure TWS/Gateway is running
- Check port is 7497 (Paper Trading)
- Enable API in TWS settings

### "Safety violation" error
- You're trying to connect to a live account
- Use Paper Trading account only

### No data appearing
- Check TWS data subscriptions
- Verify market hours (options only during market)
- Try demo mode first

### Dashboard not loading
- Check if port 8080 is available
- Try different port: `--port 8000`

## Disclaimer

```
╔══════════════════════════════════════════════════════════════╗
║                         DISCLAIMER                           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  This software is for EDUCATIONAL and INFORMATIONAL         ║
║  purposes only. It is NOT financial advice.                  ║
║                                                              ║
║  • All trading decisions are made by YOU                     ║
║  • Past signals do not guarantee future results              ║
║  • Options trading involves significant risk                 ║
║  • You could lose your entire investment                     ║
║                                                              ║
║  Always conduct your own research and consult with a         ║
║  qualified financial advisor before trading.                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

## License

MIT License - See LICENSE file for details.

---

**Built with safety in mind. Trade responsibly.**
