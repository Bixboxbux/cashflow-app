"""
Institutional Flow Tracker - API Routes

Additional API endpoints for advanced queries.
"""

from fastapi import APIRouter, Query
from typing import Optional, List
from datetime import datetime

router = APIRouter()


@router.get("/sectors")
async def get_sectors():
    """Get flow summary by sector."""
    from config import SECTOR_MAPPINGS

    return {
        "success": True,
        "sectors": list(SECTOR_MAPPINGS.keys()),
        "mappings": SECTOR_MAPPINGS,
    }


@router.get("/thresholds")
async def get_thresholds():
    """Get current detection thresholds."""
    from config import (
        PREMIUM_THRESHOLDS,
        VOLUME_THRESHOLDS,
        SWEEP_THRESHOLDS,
    )

    return {
        "success": True,
        "premium": {
            "mega_whale": PREMIUM_THRESHOLDS.MEGA_WHALE,
            "whale": PREMIUM_THRESHOLDS.WHALE,
            "notable": PREMIUM_THRESHOLDS.NOTABLE,
            "tracking_min": PREMIUM_THRESHOLDS.TRACKING_MIN,
        },
        "volume": {
            "unusual_multiplier": VOLUME_THRESHOLDS.UNUSUAL_VOLUME,
            "high_multiplier": VOLUME_THRESHOLDS.HIGH_VOLUME,
            "extreme_multiplier": VOLUME_THRESHOLDS.EXTREME_VOLUME,
        },
        "sweep": {
            "time_window_ms": SWEEP_THRESHOLDS.TIME_WINDOW_MS,
            "min_exchanges": SWEEP_THRESHOLDS.MIN_EXCHANGES,
            "min_premium": SWEEP_THRESHOLDS.MIN_SWEEP_PREMIUM,
        },
    }


@router.get("/filters")
async def get_filter_options():
    """Get available filter options."""
    from config.thresholds import SignalType, FlowDirection, ConvictionLevel

    return {
        "success": True,
        "signal_types": [t.value for t in SignalType],
        "directions": [d.value for d in FlowDirection],
        "conviction_levels": [c.value for c in ConvictionLevel],
        "premium_ranges": [
            {"label": "All", "min": 0},
            {"label": "> $25K", "min": 25000},
            {"label": "> $50K", "min": 50000},
            {"label": "> $100K", "min": 100000},
            {"label": "> $250K", "min": 250000},
            {"label": "> $1M", "min": 1000000},
        ],
    }
