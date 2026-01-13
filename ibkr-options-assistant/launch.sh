#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# IBKR Options Trading Assistant - Linux/Mac Launch Script
# ═══════════════════════════════════════════════════════════════════════════
#
# Usage:
#   ./launch.sh              # Normal mode (requires IBKR TWS)
#   ./launch.sh --demo       # Demo mode (no IBKR required)
#   ./launch.sh --install    # Install dependencies first
#   ./launch.sh --port 8000  # Custom port
#
# Requirements:
#   - Python 3.9+ installed
#   - TWS or IB Gateway running (for live mode)
#   - Paper Trading enabled on port 7497
#
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
PORT=8080
HOST="127.0.0.1"
DEMO=false
INSTALL=false
DEBUG=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --demo|-d)
            DEMO=true
            shift
            ;;
        --install|-i)
            INSTALL=true
            shift
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        --port|-p)
            PORT="$2"
            shift 2
            ;;
        --host|-h)
            HOST="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Print banner
print_banner() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                              ║${NC}"
    echo -e "${CYAN}║     ${GREEN}📊  IBKR OPTIONS TRADING ASSISTANT${CYAN}                      ║${NC}"
    echo -e "${CYAN}║                                                              ║${NC}"
    echo -e "${CYAN}║     Signal Analysis Dashboard for Options Traders            ║${NC}"
    echo -e "${CYAN}║                                                              ║${NC}"
    echo -e "${CYAN}║     ${YELLOW}⚠️  READ-ONLY MODE - NO AUTOMATED TRADING${CYAN}               ║${NC}"
    echo -e "${CYAN}║     📋  Paper Trading Connection Only                        ║${NC}"
    echo -e "${CYAN}║                                                              ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Display banner
print_banner

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check Python installation
echo "Checking Python installation..."
PYTHON=""
for cmd in python3 python; do
    if command -v $cmd &> /dev/null; then
        version=$($cmd --version 2>&1)
        if [[ $version == *"Python 3."* ]]; then
            PYTHON=$cmd
            print_step "Found $version"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    print_error "Python 3.9+ is required but not found!"
    echo "Please install Python 3 using your package manager:"
    echo "  - Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
    echo "  - macOS: brew install python3"
    exit 1
fi

# Create virtual environment if needed
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "Creating virtual environment..."
    $PYTHON -m venv "$VENV_DIR"
    print_step "Virtual environment created"
    INSTALL=true
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"
print_step "Virtual environment activated"

# Install dependencies if requested
if [ "$INSTALL" = true ]; then
    echo ""
    echo "Installing dependencies..."
    pip install --upgrade pip > /dev/null
    pip install -r requirements.txt
    print_step "Dependencies installed"
fi

# Build command arguments
ARGS=""

if [ "$DEMO" = true ]; then
    ARGS="$ARGS --demo"
    print_warning "Running in DEMO mode (no IBKR connection required)"
else
    echo ""
    echo -e "${YELLOW}IBKR Connection Requirements:${NC}"
    echo "  1. TWS or IB Gateway must be running"
    echo "  2. Paper Trading mode enabled"
    echo "  3. API connections enabled (port 7497)"
    echo ""
fi

ARGS="$ARGS --port $PORT --host $HOST"

if [ "$DEBUG" = true ]; then
    ARGS="$ARGS --debug"
fi

# Launch the application
echo ""
echo -e "${GREEN}Starting IBKR Options Assistant...${NC}"
echo -e "Dashboard URL: ${CYAN}http://${HOST}:${PORT}${NC}"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python main.py $ARGS
