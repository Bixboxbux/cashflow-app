#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# Institutional Flow Tracker - Linux/Mac Launch Script
# ═══════════════════════════════════════════════════════════════════════════
#
# Usage:
#   ./launch.sh              # Demo mode (default)
#   ./launch.sh --live       # Live mode with IBKR
#   ./launch.sh --port 8000  # Custom port
#
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Default values
PORT=8080
HOST="127.0.0.1"
LIVE=false
DEBUG=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --live|-l) LIVE=true; shift ;;
        --debug) DEBUG=true; shift ;;
        --port|-p) PORT="$2"; shift 2 ;;
        --host|-h) HOST="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Banner
echo ""
echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                              ║${NC}"
echo -e "${CYAN}║    ${GREEN}🐋  INSTITUTIONAL FLOW TRACKER${CYAN}                           ║${NC}"
echo -e "${CYAN}║                                                              ║${NC}"
echo -e "${CYAN}║    ${YELLOW}⚠️  READ-ONLY MODE - NO AUTOMATED TRADING${CYAN}                ║${NC}"
echo -e "${CYAN}║                                                              ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python
PYTHON=""
for cmd in python3 python; do
    if command -v $cmd &> /dev/null; then
        version=$($cmd --version 2>&1)
        if [[ $version == *"Python 3."* ]]; then
            PYTHON=$cmd
            echo -e "${GREEN}[✓]${NC} Found $version"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${YELLOW}[!]${NC} Python 3.10+ required"
    exit 1
fi

# Create virtual environment
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    pip install --upgrade pip > /dev/null
    pip install -r requirements.txt
    echo -e "${GREEN}[✓]${NC} Dependencies installed"
else
    source "$VENV_DIR/bin/activate"
fi

# Build args
ARGS="--port $PORT --host $HOST"
if [ "$LIVE" = true ]; then
    ARGS="$ARGS --live"
    echo -e "${YELLOW}[!]${NC} Live mode - IBKR connection required"
else
    echo -e "${GREEN}[✓]${NC} Demo mode - No IBKR needed"
fi

if [ "$DEBUG" = true ]; then
    ARGS="$ARGS --debug"
fi

# Launch
echo ""
echo -e "${GREEN}Starting Flow Tracker...${NC}"
echo -e "Dashboard: ${CYAN}http://${HOST}:${PORT}${NC}"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python main.py $ARGS
