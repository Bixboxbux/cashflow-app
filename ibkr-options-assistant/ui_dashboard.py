"""
IBKR Options Trading Assistant - Web Dashboard

This module provides a professional, mobile-friendly web interface
for viewing options alerts and signal analysis.

Features:
- Real-time alert display
- Filtering by symbol, type, confidence
- Color-coded decisions (BUY=green, SELL=red, WAIT=yellow)
- Confidence bar visualization
- Dark mode interface
- Mobile-responsive design

Built with FastAPI for performance and async support.

Author: IBKR Options Assistant
License: MIT
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import json
import asyncio

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from config import CONFIG, Decision
from decision_engine import TradingAlert, DecisionEngine


# Configure module logger
logger = logging.getLogger(__name__)

# Get the directory containing this file
BASE_DIR = Path(__file__).resolve().parent

# Initialize FastAPI app
app = FastAPI(
    title="IBKR Options Assistant",
    description="Professional options trading signal analysis dashboard",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Configure templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# ══════════════════════════════════════════════════════════════════════════════
# Data Models
# ══════════════════════════════════════════════════════════════════════════════

class AlertResponse(BaseModel):
    """API response model for alerts."""
    success: bool
    count: int
    alerts: List[Dict]
    summary: Dict
    timestamp: str


class StatusResponse(BaseModel):
    """API response model for system status."""
    connected: bool
    paper_trading: bool
    last_update: str
    watchlist: List[str]
    alert_count: int


class FilterParams(BaseModel):
    """Filter parameters for alerts."""
    symbol: Optional[str] = None
    option_type: Optional[str] = None
    decision: Optional[str] = None
    min_confidence: Optional[float] = None
    max_confidence: Optional[float] = None


# ══════════════════════════════════════════════════════════════════════════════
# In-memory storage for alerts (would use database in production)
# ══════════════════════════════════════════════════════════════════════════════

class AlertStore:
    """Simple in-memory alert storage."""

    def __init__(self):
        self.alerts: List[TradingAlert] = []
        self.last_update: datetime = None
        self.is_connected: bool = False
        self.is_paper: bool = True

    def update_alerts(self, alerts: List[TradingAlert]):
        """Update stored alerts."""
        self.alerts = alerts
        self.last_update = datetime.now()

    def get_alerts(
        self,
        symbol: str = None,
        option_type: str = None,
        decision: str = None,
        min_confidence: float = None
    ) -> List[TradingAlert]:
        """Get filtered alerts."""
        filtered = self.alerts.copy()

        if symbol:
            filtered = [a for a in filtered if a.symbol.upper() == symbol.upper()]

        if option_type:
            filtered = [a for a in filtered if a.option_type == option_type.upper()]

        if decision:
            filtered = [a for a in filtered
                       if a.decision.value == decision.upper()]

        if min_confidence is not None:
            filtered = [a for a in filtered if a.confidence >= min_confidence]

        return filtered


# Global alert store
alert_store = AlertStore()


# ══════════════════════════════════════════════════════════════════════════════
# API Routes
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the main dashboard page."""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "title": "IBKR Options Assistant",
            "watchlist": CONFIG.watchlist,
            "refresh_interval": CONFIG.ui.refresh_interval
        }
    )


@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """Get system status."""
    return StatusResponse(
        connected=alert_store.is_connected,
        paper_trading=alert_store.is_paper,
        last_update=alert_store.last_update.isoformat() if alert_store.last_update else "",
        watchlist=CONFIG.watchlist,
        alert_count=len(alert_store.alerts)
    )


@app.get("/api/alerts")
async def get_alerts(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    option_type: Optional[str] = Query(None, description="CALL or PUT"),
    decision: Optional[str] = Query(None, description="BUY, SELL, or WAIT"),
    min_confidence: Optional[float] = Query(None, ge=0, le=100, description="Min confidence"),
    limit: Optional[int] = Query(100, ge=1, le=500, description="Max results")
):
    """Get filtered alerts."""
    try:
        alerts = alert_store.get_alerts(
            symbol=symbol,
            option_type=option_type,
            decision=decision,
            min_confidence=min_confidence
        )

        # Limit results
        alerts = alerts[:limit]

        # Convert to dictionaries
        alert_dicts = [a.to_dict() for a in alerts]

        # Calculate summary
        decision_engine = DecisionEngine()
        summary = decision_engine.get_alerts_summary(alerts)

        return {
            "success": True,
            "count": len(alerts),
            "alerts": alert_dicts,
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/alerts/{alert_id}")
async def get_alert_detail(alert_id: str):
    """Get detailed information for a specific alert."""
    for alert in alert_store.alerts:
        if alert.alert_id == alert_id:
            return {
                "success": True,
                "alert": alert.to_dict()
            }

    raise HTTPException(status_code=404, detail="Alert not found")


@app.get("/api/symbols")
async def get_symbols():
    """Get list of symbols with alerts."""
    symbols = set()
    for alert in alert_store.alerts:
        symbols.add(alert.symbol)

    return {
        "success": True,
        "symbols": sorted(list(symbols)),
        "watchlist": CONFIG.watchlist
    }


@app.get("/api/expirations")
async def get_expirations(symbol: Optional[str] = None):
    """Get list of unique expiration dates."""
    expirations = set()

    for alert in alert_store.alerts:
        if symbol is None or alert.symbol == symbol.upper():
            expirations.add(alert.expiration)

    return {
        "success": True,
        "expirations": sorted(list(expirations))
    }


@app.get("/api/summary")
async def get_summary():
    """Get summary statistics across all alerts."""
    if not alert_store.alerts:
        return {
            "success": True,
            "total_alerts": 0,
            "by_decision": {"BUY": 0, "SELL": 0, "WAIT": 0},
            "by_type": {"CALL": 0, "PUT": 0},
            "by_symbol": {},
            "avg_confidence": 0,
            "actionable_pct": 0
        }

    alerts = alert_store.alerts

    by_decision = {"BUY": 0, "SELL": 0, "WAIT": 0}
    by_type = {"CALL": 0, "PUT": 0}
    by_symbol = {}

    for alert in alerts:
        by_decision[alert.decision.value] += 1
        by_type[alert.option_type] += 1
        by_symbol[alert.symbol] = by_symbol.get(alert.symbol, 0) + 1

    avg_confidence = sum(a.confidence for a in alerts) / len(alerts)
    actionable = sum(1 for a in alerts if a.is_actionable)
    actionable_pct = (actionable / len(alerts)) * 100 if alerts else 0

    return {
        "success": True,
        "total_alerts": len(alerts),
        "by_decision": by_decision,
        "by_type": by_type,
        "by_symbol": by_symbol,
        "avg_confidence": round(avg_confidence, 1),
        "actionable_pct": round(actionable_pct, 1)
    }


# ══════════════════════════════════════════════════════════════════════════════
# Dashboard Helper Functions
# ══════════════════════════════════════════════════════════════════════════════

def update_alert_store(alerts: List[TradingAlert], connected: bool = True):
    """Update the global alert store with new alerts."""
    alert_store.update_alerts(alerts)
    alert_store.is_connected = connected


def get_decision_color(decision: Decision) -> str:
    """Get color for decision display."""
    colors = {
        Decision.BUY: "#10b981",    # Green
        Decision.SELL: "#ef4444",   # Red
        Decision.WAIT: "#f59e0b"    # Yellow/Amber
    }
    return colors.get(decision, "#6b7280")


def get_confidence_gradient(confidence: float) -> str:
    """Get gradient color based on confidence level."""
    if confidence >= 85:
        return "linear-gradient(90deg, #10b981 0%, #059669 100%)"  # Green
    elif confidence >= 75:
        return "linear-gradient(90deg, #22c55e 0%, #10b981 100%)"  # Light green
    elif confidence >= 65:
        return "linear-gradient(90deg, #f59e0b 0%, #d97706 100%)"  # Amber
    elif confidence >= 50:
        return "linear-gradient(90deg, #f97316 0%, #ea580c 100%)"  # Orange
    else:
        return "linear-gradient(90deg, #ef4444 0%, #dc2626 100%)"  # Red


# Register template filters
templates.env.globals['get_decision_color'] = get_decision_color
templates.env.globals['get_confidence_gradient'] = get_confidence_gradient


# ══════════════════════════════════════════════════════════════════════════════
# Health Check
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# ══════════════════════════════════════════════════════════════════════════════
# Error Handlers
# ══════════════════════════════════════════════════════════════════════════════

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc)
        }
    )
