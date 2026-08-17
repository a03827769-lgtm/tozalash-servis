"""
Tozalash Servis — WebSocket Standalone Runner
Re-exports unified ws_manager from app.api.websockets and runs standalone server
"""

import asyncio
from loguru import logger
import uvicorn
from app.api.websockets import ws_manager, router as ws_router, ConnectionManager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ConnectionManager = ws_manager.__class__


def create_ws_app():
    return ws_app


ws_app = FastAPI(title="Tozalash Servis WebSocket Server")

ws_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ws_app.include_router(ws_router)


async def run_ws_server(host: str = "0.0.0.0", port: int = 8001):
    """WebSocket serverini asinxron ishga tushirish"""
    config = uvicorn.Config(
        app=ws_app,
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    logger.success(f"🚀 Real-Time WebSocket Server ishga tushdi: ws://{host}:{port}/ws")
    await server.serve()


if __name__ == "__main__":
    asyncio.run(run_ws_server())
