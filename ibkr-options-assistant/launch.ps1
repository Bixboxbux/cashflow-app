# ═══════════════════════════════════════════════════════════════════════════
# IBKR Options Trading Assistant - Windows Launch Script (PowerShell)
# ═══════════════════════════════════════════════════════════════════════════
#
# Usage:
#   .\launch.ps1              # Normal mode (requires IBKR TWS)
#   .\launch.ps1 -Demo        # Demo mode (no IBKR required)
#   .\launch.ps1 -Install     # Install dependencies first
#   .\launch.ps1 -Port 8000   # Custom port
#
# Requirements:
#   - Python 3.9+ installed
#   - TWS or IB Gateway running (for live mode)
#   - Paper Trading enabled on port 7497
#
# ═══════════════════════════════════════════════════════════════════════════

param(
    [switch]$Demo,
    [switch]$Install,
    [switch]$Debug,
    [int]$Port = 8080,
    [string]$Host = "127.0.0.1"
)

# Colors for output
$ESC = [char]27
$GREEN = "$ESC[92m"
$YELLOW = "$ESC[93m"
$RED = "$ESC[91m"
$CYAN = "$ESC[96m"
$RESET = "$ESC[0m"

function Write-Banner {
    Write-Host ""
    Write-Host "${CYAN}╔══════════════════════════════════════════════════════════════╗${RESET}"
    Write-Host "${CYAN}║                                                              ║${RESET}"
    Write-Host "${CYAN}║     ${GREEN}📊  IBKR OPTIONS TRADING ASSISTANT${CYAN}                      ║${RESET}"
    Write-Host "${CYAN}║                                                              ║${RESET}"
    Write-Host "${CYAN}║     Signal Analysis Dashboard for Options Traders            ║${RESET}"
    Write-Host "${CYAN}║                                                              ║${RESET}"
    Write-Host "${CYAN}║     ${YELLOW}⚠️  READ-ONLY MODE - NO AUTOMATED TRADING${CYAN}               ║${RESET}"
    Write-Host "${CYAN}║     📋  Paper Trading Connection Only                        ║${RESET}"
    Write-Host "${CYAN}║                                                              ║${RESET}"
    Write-Host "${CYAN}╚══════════════════════════════════════════════════════════════╝${RESET}"
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host "${GREEN}[✓]${RESET} $Message"
}

function Write-Warning {
    param([string]$Message)
    Write-Host "${YELLOW}[!]${RESET} $Message"
}

function Write-Error {
    param([string]$Message)
    Write-Host "${RED}[✗]${RESET} $Message"
}

# Display banner
Write-Banner

# Check Python installation
Write-Host "Checking Python installation..."
$python = $null
foreach ($cmd in @("python3", "python", "py")) {
    try {
        $version = & $cmd --version 2>&1
        if ($version -match "Python 3\.") {
            $python = $cmd
            Write-Step "Found $version"
            break
        }
    } catch {
        continue
    }
}

if (-not $python) {
    Write-Error "Python 3.9+ is required but not found!"
    Write-Host "Please install Python from https://www.python.org/downloads/"
    exit 1
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Create virtual environment if needed
$VenvDir = Join-Path $ScriptDir "venv"
if (-not (Test-Path $VenvDir)) {
    Write-Host ""
    Write-Host "Creating virtual environment..."
    & $python -m venv $VenvDir
    Write-Step "Virtual environment created"
    $Install = $true
}

# Activate virtual environment
$ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
if (Test-Path $ActivateScript) {
    . $ActivateScript
    Write-Step "Virtual environment activated"
} else {
    Write-Error "Could not activate virtual environment"
    exit 1
}

# Install dependencies if requested or needed
if ($Install) {
    Write-Host ""
    Write-Host "Installing dependencies..."
    pip install --upgrade pip | Out-Null
    pip install -r requirements.txt
    Write-Step "Dependencies installed"
}

# Build command arguments
$Args = @()

if ($Demo) {
    $Args += "--demo"
    Write-Warning "Running in DEMO mode (no IBKR connection required)"
} else {
    Write-Host ""
    Write-Host "${YELLOW}IBKR Connection Requirements:${RESET}"
    Write-Host "  1. TWS or IB Gateway must be running"
    Write-Host "  2. Paper Trading mode enabled"
    Write-Host "  3. API connections enabled (port 7497)"
    Write-Host ""
}

$Args += "--port"
$Args += $Port
$Args += "--host"
$Args += $Host

if ($Debug) {
    $Args += "--debug"
}

# Launch the application
Write-Host ""
Write-Host "${GREEN}Starting IBKR Options Assistant...${RESET}"
Write-Host "Dashboard URL: ${CYAN}http://${Host}:${Port}${RESET}"
Write-Host ""
Write-Host "Press Ctrl+C to stop"
Write-Host ""

& $python main.py @Args
