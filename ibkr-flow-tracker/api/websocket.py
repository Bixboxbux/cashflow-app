"""
Institutional Flow Tracker - WebSocket Manager

Manages WebSocket connections for real-time updates.
"""

import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections.

    Features:
    - Connection tracking
    - Broadcast to all clients
    - Individual messaging
    - Graceful disconnect handling
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: List[WebSocket] = []
        self._connection_count = 0

    async def connect(self, websocket: WebSocket):
        """
        Accept and track a new WebSocket connection.

        Args:
            websocket: The WebSocket to connect
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        self._connection_count += 1
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket to disconnect
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """
        Send a message to a specific client.

        Args:
            message: The message dict to send
            websocket: The target WebSocket
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected clients.

        Args:
            message: The message dict to broadcast
        """
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_text(self, message: str):
        """
        Broadcast a text message to all connected clients.

        Args:
            message: The text message to broadcast
        """
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting text: {e}")
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)

    @property
    def connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)

    @property
    def total_connections(self) -> int:
        """Get total connections since start."""
        return self._connection_count

    def get_stats(self) -> Dict[str, int]:
        """Get connection statistics."""
        return {
            "active": self.connection_count,
            "total": self.total_connections,
        }
