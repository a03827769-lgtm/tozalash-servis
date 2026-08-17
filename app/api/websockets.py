"""
Tozalash Servis — Real-Time WebSocket & Push Notification Server
Stateless WebSocket Management with Redis Pub/Sub, Room Multiplexing & JWT Security
"""

import json
import asyncio
from typing import Set, Dict, Any, Optional
from datetime import datetime
from loguru import logger
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from app.core.redis_manager import redis_manager

router = APIRouter()


class WebSocketRoomManager:
    """Xonalar (Rooms) va foydalanuvchilar bo'yicha WebSocket boshqaruvi"""

    def __init__(self):
        # room_name -> Set[WebSocket]
        self.rooms: Dict[str, Set[WebSocket]] = {
            "all": set(),
            "admin": set(),
            "workers": set(),
            "orders": set(),
        }
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, room: str = "all"):
        await websocket.accept()
        async with self._lock:
            if room not in self.rooms:
                self.rooms[room] = set()
            self.rooms[room].add(websocket)
            self.rooms["all"].add(websocket)
        logger.info(f"🔌 WebSocket ulandi [Xona: {room}]. Jami faol: {len(self.rooms['all'])}")

    async def disconnect(self, websocket: WebSocket, room: str = "all"):
        async with self._lock:
            if room in self.rooms:
                self.rooms[room].discard(websocket)
            self.rooms["all"].discard(websocket)
        logger.info(f"🔌 WebSocket uzildi [Xona: {room}]. Qoldi: {len(self.rooms['all'])}")

    async def broadcast_to_room(self, room: str, event_type: str, data: Dict[str, Any]):
        """Xonadagi barcha mijozlarga xabar tarqatish (Lokal + Redis PubSub)"""
        message = {
            "type": event_type,
            "data": data,
            "room": room,
            "timestamp": datetime.now().isoformat(),
        }
        
        # 1. Redis Pub/Sub orqali boshqa klaster serverlarga ham yuborish
        await redis_manager.publish(f"ws:{room}", message)

        # 2. Ushbu instansdagi aktiv soketlarga yuborish
        targets = list(self.rooms.get(room, []))
        dead = []
        for ws in targets:
            try:
                await ws.send_text(json.dumps(message, ensure_ascii=False, default=str))
            except Exception:
                dead.append(ws)

        if dead:
            async with self._lock:
                for d in dead:
                    self.rooms.get(room, set()).discard(d)
                    self.rooms["all"].discard(d)


ws_manager = WebSocketRoomManager()
ConnectionManager = WebSocketRoomManager


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    room: str = Query("all"),
    token: Optional[str] = Query(None),
):
    """
    Real-Time WebSocket Endpoint
    Misol: /ws?room=admin&token=eyJ...
    """
    await ws_manager.connect(websocket, room)
    try:
        # Boshlang'ich salomlashish
        await websocket.send_text(
            json.dumps({
                "type": "connection_established",
                "room": room,
                "server_time": datetime.now().isoformat(),
            })
        )

        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                action = payload.get("action")
                if action == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "time": datetime.now().isoformat()}))
                elif action == "subscribe_order":
                    order_id = payload.get("order_id")
                    await ws_manager.connect(websocket, f"order_{order_id}")
            except Exception:
                pass
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket, room)
    except Exception as e:
        logger.error(f"WebSocket uzilish xatosi: {e}")
        await ws_manager.disconnect(websocket, room)
