import asyncio
import json
import uuid
from typing import List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.utils.logger import logger

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # Keep a reference to the main event loop so the scheduler can post into it
        self._loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, websocket: WebSocket):
        if self._loop is None:
            self._loop = asyncio.get_running_loop()
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total clients: {len(self.active_connections)}")
        # Immediately send a welcome / status message so the UI shows it's live
        welcome = {
            "type": "SYSTEM_READY",
            "score": 8.5,
            "recommendation": "Agent pipeline initialised — market monitoring active. Signals will appear here every 5 minutes.",
            "timestamp": "now",
            "pipeline_signals": 0,
        }
        await websocket.send_text(json.dumps(welcome))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Remaining clients: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_text(message)
            except Exception as e:
                logger.warning(f"WS send failed, dropping connection: {e}")
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    def broadcast_from_thread(self, payload: dict):
        """Called from APScheduler background threads. Posts into the main event loop safely."""
        message = json.dumps(payload)
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast(message), self._loop)
        else:
            logger.warning("Main event loop not available — WebSocket broadcast skipped.")


manager = ConnectionManager()


@router.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive (client can send pings)
            data = await websocket.receive_text()
            logger.debug(f"WS received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
