import asyncio
import json
import time
from pathlib import Path
from typing import Optional, Set

from virtual_tcu import paths
from virtual_tcu.config.constants import Cfg, DEFAULTS
from virtual_tcu.config.store import ConfigStore
from virtual_tcu.deps import AIOHTTP_OK, WSMsgType, web
from virtual_tcu.logic.tcu import TCULogic
from virtual_tcu.telemetry.logger import TelemetryLogger
from virtual_tcu.telemetry.receiver import TelemetryReceiver

_NO_UI_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Virtual TCU — Web UI unavailable</title>
</head>
<body>
  <h1>Web UI unavailable</h1>
  <p>Dashboard assets missing. Run UI build process.</p>
</body>
</html>
"""

def _dist_index() -> Optional[Path]:
    p = paths.web_dist_dir() / "index.html"
    return p if p.is_file() else None

def _dist_assets_dir() -> Optional[Path]:
    p = paths.web_dist_dir() / "assets"
    return p if p.is_dir() else None

class WebServer:
    def __init__(
        self,
        receiver: TelemetryReceiver,
        tcu: TCULogic,
        config: ConfigStore,
        logger: TelemetryLogger,
    ):
        self._recv = receiver
        self._tcu = tcu
        self._config = config
        self._logger = logger
        self._clients: Set = set()
        self._ui_available = _dist_index() is not None

    async def index(self, request):
        dist = _dist_index()
        if dist is not None:
            return web.FileResponse(dist)
        return web.Response(
            text=_NO_UI_HTML,
            content_type="text/html; charset=utf-8",
            status=503,
        )

    async def websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self._clients.add(ws)
        try:
            await ws.send_json({
                "type": "init",
                "data": {
                    "mode": self._tcu.mode.value,
                    "live": self._recv.is_live,
                    "shift_count": self._tcu.shift_count,
                    "packets_total": self._recv.packets_total,
                    "config": self._config.data,
                    "defaults": DEFAULTS,
                    "log_status": self._logger.status,
                },
            })
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_client_msg(data, ws)
                    except Exception as e:
                        print(f"[WS] msg parse error: {e}")
                elif msg.type == WSMsgType.ERROR:
                    break
        finally:
            self._clients.discard(ws)
        return ws

    async def _handle_client_msg(self, msg: dict, ws):
        t = msg.get("type")
        if t == "set_mode":
            self._tcu.set_mode(msg.get("mode", ""))
        elif t == "set_config":
            key = msg.get("key", "")
            val = msg.get("value")
            self._config.set(key, val)
            if key in ("shift_key_up", "shift_key_down"):
                self._tcu.refresh_shift_keys()
        elif t == "reset_config":
            self._config.reset()
            self._tcu.refresh_shift_keys()
            await ws.send_json({"type": "config_reset", "data": self._config.data})
        elif t == "log_start":
            self._logger.start(msg.get("mode", "events"))
            await ws.send_json({"type": "log_status", "data": self._logger.status})
        elif t == "log_stop":
            path = self._logger.stop()
            await ws.send_json({"type": "log_status", "data": self._logger.status, "last_file": path})
        elif t == "request_graph":
            await ws.send_json({"type": "graph_data", "data": self._tcu.snapshot_graph()})

    async def broadcast_loop(self):
        tcu_interval = 1.0 / 60.0
        broadcast_every_n = 2
        tick = 0
        while True:
            await asyncio.sleep(tcu_interval)
            tick += 1
            if tick % broadcast_every_n != 0 or not self._clients:
                continue

            td = self._recv.latest()
            # CRITICAL FIX: Removed self._tcu.process() call here.
            # Processing is strictly handled by TelemetryReceiver's thread callback.
            # Calling it here caused double-counting and logic corruption.
            
            payload_st = {
                "type": "state",
                "data": {
                    "mode": self._tcu.mode.value,
                    "live": self._recv.is_live,
                    "shift_count": self._tcu.shift_count,
                    "packets_total": self._recv.packets_total,
                },
            }
            
            payload_tel = None
            if td is not None:
                payload_tel = {"type": "telemetry", "data": self._tcu.snapshot(td)}

            dead = set()
            for client in tuple(self._clients):
                try:
                    if payload_tel:
                        await client.send_json(payload_tel)
                    await client.send_json(payload_st)
                except Exception:
                    dead.add(client)
            self._clients -= dead

    async def start(self):
        app = web.Application()
        assets = _dist_assets_dir()
        if assets is not None:
            app.router.add_static("/assets", assets)
        app.router.add_get("/", self.index)
        app.router.add_get("/ws", self.websocket_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, Cfg.WEB_HOST, Cfg.WEB_PORT)
        await site.start()
        print(f"  [OK] Web UI online")
        asyncio.create_task(self.broadcast_loop())

    async def stop(self):
        for ws in list(self._clients):
            await ws.close()
