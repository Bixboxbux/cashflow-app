"""
Institutional Flow Tracker - FastAPI Application

Main API application with WebSocket support for real-time updates.

Features:
- REST API for signal queries
- WebSocket for real-time flow updates
- Signal filtering and search
- System status endpoints

SAFETY: This API is READ-ONLY and provides no trading functionality.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

from config import CONFIG
from models import FlowSignal, FlowAlert
from api.websocket import ConnectionManager
from api.routes import router


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize FastAPI app
app = FastAPI(
    title="Institutional Flow Tracker",
    description="Real-time options flow detection for institutional activity",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "ui" / "static")), name="static")

# Configure templates
templates = Jinja2Templates(directory=str(BASE_DIR / "ui" / "templates"))

# Include routes
app.include_router(router, prefix="/api")

# WebSocket connection manager
ws_manager = ConnectionManager()


# ═══════════════════════════════════════════════════════════════════════════════
# Global State
# ═══════════════════════════════════════════════════════════════════════════════

class AppState:
    """Application state management."""

    def __init__(self):
        self.signals: List[FlowSignal] = []
        self.is_connected: bool = False
        self.is_demo_mode: bool = True
        self.last_update: datetime = None
        self.stats = {
            "total_signals": 0,
            "bullish_signals": 0,
            "bearish_signals": 0,
            "sweeps_detected": 0,
            "whales_detected": 0,
        }

    def add_signal(self, signal: FlowSignal):
        """Add a signal to the state."""
        self.signals.insert(0, signal)
        if len(self.signals) > CONFIG.ui.max_signals_display:
            self.signals = self.signals[:CONFIG.ui.max_signals_display]

        self.stats["total_signals"] += 1
        if signal.direction.value == "BULLISH":
            self.stats["bullish_signals"] += 1
        elif signal.direction.value == "BEARISH":
            self.stats["bearish_signals"] += 1
        if signal.is_sweep:
            self.stats["sweeps_detected"] += 1
        if signal.metrics.premium_paid >= 250000:
            self.stats["whales_detected"] += 1

        self.last_update = datetime.now()

    def get_signals(
        self,
        symbol: str = None,
        direction: str = None,
        signal_type: str = None,
        min_premium: float = None,
        limit: int = 100
    ) -> List[FlowSignal]:
        """Get filtered signals."""
        filtered = self.signals.copy()

        if symbol:
            filtered = [s for s in filtered if s.symbol.upper() == symbol.upper()]
        if direction:
            filtered = [s for s in filtered if s.direction.value == direction.upper()]
        if signal_type:
            filtered = [s for s in filtered if s.signal_type.value == signal_type.upper()]
        if min_premium is not None:
            filtered = [s for s in filtered if s.metrics.premium_paid >= min_premium]

        return filtered[:limit]


# Global state instance
state = AppState()


# ═══════════════════════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main dashboard."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "title": "Institutional Flow Tracker",
            "config": {
                "ws_url": f"ws://{CONFIG.ui.host}:{CONFIG.ui.port}/ws",
                "refresh_interval": CONFIG.ui.default_refresh_interval_ms,
            }
        }
    )


@app.get("/api/status")
async def get_status():
    """Get system status."""
    return {
        "success": True,
        "connected": state.is_connected,
        "demo_mode": state.is_demo_mode,
        "last_update": state.last_update.isoformat() if state.last_update else None,
        "signal_count": len(state.signals),
        "stats": state.stats,
    }


@app.get("/api/signals")
async def get_signals(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    direction: Optional[str] = Query(None, description="BULLISH, BEARISH, or NEUTRAL"),
    signal_type: Optional[str] = Query(None, description="Signal type filter"),
    min_premium: Optional[float] = Query(None, ge=0, description="Minimum premium"),
    limit: Optional[int] = Query(100, ge=1, le=500, description="Max results"),
):
    """Get filtered flow signals."""
    signals = state.get_signals(
        symbol=symbol,
        direction=direction,
        signal_type=signal_type,
        min_premium=min_premium,
        limit=limit,
    )

    return {
        "success": True,
        "count": len(signals),
        "signals": [s.to_dict() for s in signals],
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/signals/{signal_id}")
async def get_signal_detail(signal_id: str):
    """Get a specific signal by ID."""
    for signal in state.signals:
        if signal.signal_id == signal_id:
            return {
                "success": True,
                "signal": signal.to_dict(),
            }

    raise HTTPException(status_code=404, detail="Signal not found")


@app.get("/api/symbols")
async def get_active_symbols():
    """Get list of symbols with active signals."""
    symbols = {}
    for signal in state.signals:
        if signal.symbol not in symbols:
            symbols[signal.symbol] = {
                "count": 0,
                "bullish": 0,
                "bearish": 0,
                "total_premium": 0,
            }
        symbols[signal.symbol]["count"] += 1
        symbols[signal.symbol]["total_premium"] += signal.metrics.premium_paid
        if signal.direction.value == "BULLISH":
            symbols[signal.symbol]["bullish"] += 1
        elif signal.direction.value == "BEARISH":
            symbols[signal.symbol]["bearish"] += 1

    return {
        "success": True,
        "symbols": symbols,
    }


@app.get("/api/summary")
async def get_summary():
    """Get dashboard summary statistics."""
    if not state.signals:
        return {
            "success": True,
            "total": 0,
            "by_direction": {"BULLISH": 0, "BEARISH": 0, "NEUTRAL": 0},
            "by_type": {},
            "by_conviction": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "total_premium": 0,
            "avg_conviction": 0,
        }

    by_direction = {"BULLISH": 0, "BEARISH": 0, "NEUTRAL": 0}
    by_type = {}
    by_conviction = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    total_premium = 0

    for signal in state.signals:
        by_direction[signal.direction.value] += 1
        by_conviction[signal.conviction_level.value] += 1
        total_premium += signal.metrics.premium_paid

        sig_type = signal.signal_type.value
        by_type[sig_type] = by_type.get(sig_type, 0) + 1

    avg_conviction = sum(s.conviction_score for s in state.signals) / len(state.signals)

    return {
        "success": True,
        "total": len(state.signals),
        "by_direction": by_direction,
        "by_type": by_type,
        "by_conviction": by_conviction,
        "total_premium": round(total_premium, 2),
        "avg_conviction": round(avg_conviction, 1),
        "stats": state.stats,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# WebSocket
# ═══════════════════════════════════════════════════════════════════════════════

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    await ws_manager.connect(websocket)

    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()

            # Handle ping/pong
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


async def broadcast_signal(signal: FlowSignal):
    """Broadcast a new signal to all connected clients."""
    state.add_signal(signal)
    await ws_manager.broadcast({
        "type": "new_signal",
        "signal": signal.to_dict(),
        "timestamp": datetime.now().isoformat(),
    })


# ═══════════════════════════════════════════════════════════════════════════════
# Health Check
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "demo_mode": state.is_demo_mode,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Error Handlers
# ═══════════════════════════════════════════════════════════════════════════════

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc),
        }
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Exports for Main
# ═══════════════════════════════════════════════════════════════════════════════

def get_app_state():
    """Get the global app state."""
    return state


def get_ws_manager():
    """Get the WebSocket manager."""
    return ws_manager
