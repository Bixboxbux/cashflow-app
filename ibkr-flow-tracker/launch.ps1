# ═══════════════════════════════════════════════════════════════════════════
# Institutional Flow Tracker - Windows Launch Script (PowerShell)
# ═══════════════════════════════════════════════════════════════════════════
#
# Usage:
#   .\launch.ps1              # Demo mode (default)
#   .\launch.ps1 -Live        # Live mode with IBKR
#   .\launch.ps1 -Port 8000   # Custom port
#
# ═══════════════════════════════════════════════════════════════════════════

param(
    [switch]$Live,
    [switch]$Debug,
    [int]$Port = 8080,
    [string]$Host = "127.0.0.1"
)

# Colors
$ESC = [char]27
$GREEN = "$ESC[92m"
$YELLOW = "$ESC[93m"
$CYAN = "$ESC[96m"
$RESET = "$ESC[0m"

# Banner
Write-Host ""
Write-Host "${CYAN}╔══════════════════════════════════════════════════════════════╗${RESET}"
Write-Host "${CYAN}║                                                              ║${RESET}"
Write-Host "${CYAN}║    ${GREEN}🐋  INSTITUTIONAL FLOW TRACKER${CYAN}                           ║${RESET}"
Write-Host "${CYAN}║                                                              ║${RESET}"
Write-Host "${CYAN}║    ${YELLOW}⚠️  READ-ONLY MODE - NO AUTOMATED TRADING${CYAN}                ║${RESET}"
Write-Host "${CYAN}║                                                              ║${RESET}"
Write-Host "${CYAN}╚══════════════════════════════════════════════════════════════╝${RESET}"
Write-Host ""

# Check Python
$python = $null
foreach ($cmd in @("python3", "python", "py")) {
    try {
        $version = & $cmd --version 2>&1
        if ($version -match "Python 3\.") {
            $python = $cmd
            Write-Host "${GREEN}[✓]${RESET} Found $version"
            break
        }
    } catch { continue }
}

if (-not $python) {
    Write-Host "${YELLOW}[!]${RESET} Python 3.10+ required"
    exit 1
}

# Script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Virtual environment
$VenvDir = Join-Path $ScriptDir "venv"
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating virtual environment..."
    & $python -m venv $VenvDir
    . "$VenvDir\Scripts\Activate.ps1"
    pip install --upgrade pip | Out-Null
    pip install -r requirements.txt
    Write-Host "${GREEN}[✓]${RESET} Dependencies installed"
} else {
    . "$VenvDir\Scripts\Activate.ps1"
}

# Build args
$Args = @("--port", $Port, "--host", $Host)
if ($Live) {
    $Args += "--live"
    Write-Host "${YELLOW}[!]${RESET} Live mode - IBKR connection required"
} else {
    Write-Host "${GREEN}[✓]${RESET} Demo mode - No IBKR needed"
}

if ($Debug) { $Args += "--debug" }

# Launch
Write-Host ""
Write-Host "${GREEN}Starting Flow Tracker...${RESET}"
Write-Host "Dashboard: ${CYAN}http://${Host}:${Port}${RESET}"
Write-Host ""
Write-Host "Press Ctrl+C to stop"
Write-Host ""

& $python main.py @Args
