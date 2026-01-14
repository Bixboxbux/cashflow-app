# 🐋 Institutional Flow Tracker

A professional, real-time options flow detection system inspired by Unusual Whales, FlowAlgo, and Cheddar Flow. Detects institutional/whale activity in US equity options markets.

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🐋  INSTITUTIONAL FLOW TRACKER                           ║
║                                                              ║
║    Real-Time Options Flow Detection                          ║
║    Whale • Sweep • Block • Dark Pool                         ║
║                                                              ║
║    ⚠️  READ-ONLY MODE - NO AUTOMATED TRADING                ║
║    📋  Paper Trading Connection Only                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

## Safety First

This system is designed with **safety as the #1 priority**:

- **READ-ONLY**: No order placement, no account modifications
- **PAPER TRADING ONLY**: Refuses to connect to live trading ports
- **ALERTS ONLY**: All decisions require manual human execution
- **NO AUTOMATED TRADING**: The codebase contains no execution functions

## Features

### Signal Detection

| Signal Type | Description | Threshold |
|-------------|-------------|-----------|
| 🏦 **Institutional Flow** | Large premium trades | > $25K |
| ⚡ **Sweep** | Multi-exchange rapid execution | 2+ exchanges in <1s |
| 📦 **Block Trade** | Single large transaction | 100+ contracts |
| 🔮 **Dark Pool** | Off-exchange prints | Large hidden volume |
| 📊 **Unusual Volume** | Volume vs average | ≥ 3x average |
| ✨ **Golden Sweep** | ATM sweep with high premium | > $100K near ATM |

### Premium Classifications

| Class | Premium | Conviction Boost |
|-------|---------|------------------|
| 🐋 **Mega Whale** | > $1M | +30% |
| 🐳 **Whale** | > $250K | +20% |
| 📌 **Notable** | > $50K | +10% |
| 📍 **Tracked** | > $25K | Base |

### Flow Card Display

Each signal displays:
```
┌─────────────────────────────────────────────────────────────┐
│ INSTITUTIONAL FLOW  HOOD  → $135 Target  by Jan 23 2026   │
├─────────────────────────────────────────────────────────────┤
│ Institutional Flow • Target $135 by Jan 23, 2026 •         │
│ Unusually Increased Premiums                                │
├─────────────────────────────────────────────────────────────┤
│ ┌──────────────┐  ┌─────────────────────────────────────┐  │
│ │ POSITIONING  │  │ LEVELS / TECHNICALS                 │  │
│ │ Accumulation │  │ $117 Floor • $120 Major Resistance  │  │
│ └──────────────┘  └─────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│ + Last 5 trading days showed accumulation                   │
├─────────────────────────────────────────────────────────────┤
│ $450K Premium │ 3,500 Contracts │ 4.8x Vol │ 78% Conviction│
│ █████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░ 78% │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Demo Mode (No IBKR Required)

```bash
# Linux/Mac
./launch.sh

# Windows PowerShell
.\launch.ps1
```

Open **http://localhost:8080** in your browser.

### Live Mode (IBKR Paper Trading)

1. Start **TWS or IB Gateway** with Paper Trading account
2. Enable API connections (port 7497)
3. Run:

```bash
# Linux/Mac
./launch.sh --live

# Windows
.\launch.ps1 -Live
```

## Installation

### Requirements

- Python 3.10+
- TWS or IB Gateway (for live mode only)
- Paper Trading account (live accounts blocked)

### Manual Installation

```bash
cd ibkr-flow-tracker

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run
python main.py  # Demo mode (default)
python main.py --live  # Live mode
```

## Architecture

```
ibkr-flow-tracker/
├── config/
│   ├── settings.py         # Configuration & safety checks
│   └── thresholds.py       # Detection thresholds
├── models/
│   ├── flow_signal.py      # FlowSignal dataclass
│   └── market_data.py      # Market data models
├── core/
│   ├── ibkr_connection.py  # IBKR API (paper trading only)
│   ├── flow_detector.py    # Real-time flow detection
│   ├── flow_classifier.py  # Signal classification
│   ├── accumulation_tracker.py  # Multi-day tracking
│   └── technical_levels.py # Support/resistance calculation
├── api/
│   ├── main.py             # FastAPI application
│   ├── websocket.py        # WebSocket manager
│   └── routes.py           # API endpoints
├── ui/
│   ├── templates/
│   │   └── dashboard.html  # Dashboard template
│   └── static/
│       ├── css/flow-dashboard.css  # Dark mode styles
│       └── js/flow-dashboard.js    # Real-time updates
├── main.py                 # Application entry point
├── requirements.txt        # Dependencies
├── launch.sh               # Linux/Mac launcher
└── launch.ps1              # Windows launcher
```

## Signal Interpretation

### Direction Indicators

| Direction | Meaning | Color |
|-----------|---------|-------|
| 📈 **BULLISH** | Call buying / Put selling | Green (#00d4aa) |
| 📉 **BEARISH** | Put buying / Call selling | Red (#ff4757) |
| ➡️ **NEUTRAL** | Hedging / Mixed activity | Yellow (#ffa502) |

### Positioning Types

| Type | Description |
|------|-------------|
| **Accumulation** | Sustained bullish positioning over multiple days |
| **Distribution** | Sustained bearish positioning over multiple days |
| **Hedging** | Balanced call/put activity |
| **Speculative** | Single trade, unclear pattern |

### Conviction Levels

| Level | Score | Meaning |
|-------|-------|---------|
| **HIGH** | 75-100% | Strong alignment of multiple signals |
| **MEDIUM** | 50-74% | Moderate confidence |
| **LOW** | 0-49% | Limited signal strength |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard UI |
| `GET /api/signals` | Get filtered signals |
| `GET /api/status` | System status |
| `GET /api/summary` | Summary statistics |
| `GET /api/symbols` | Active symbols |
| `WS /ws` | WebSocket for real-time updates |
| `GET /health` | Health check |

### Query Parameters

```
GET /api/signals?symbol=HOOD&direction=BULLISH&min_premium=100000&limit=50
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `IBKR_HOST` | IBKR host | 127.0.0.1 |
| `IBKR_PORT` | IBKR port (paper only) | 7497 |
| `UI_PORT` | Dashboard port | 8080 |
| `DEMO_MODE` | Enable demo mode | true |

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

**Built for institutional flow analysis. Trade responsibly.** 🐋
