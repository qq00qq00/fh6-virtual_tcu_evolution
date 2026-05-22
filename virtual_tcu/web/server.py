import asyncio
import json
import time
from pathlib import Path
from typing import Optional, Set

from virtual_tcu.config.constants import Cfg, DEFAULTS
from virtual_tcu.config.store import ConfigStore
from virtual_tcu.deps import AIOHTTP_OK, WSMsgType, web
from virtual_tcu.logic.tcu import TCULogic
from virtual_tcu.telemetry.logger import TelemetryLogger
from virtual_tcu.telemetry.receiver import TelemetryReceiver

_DIST_DIR = Path(__file__).with_name("dist")
_LEGACY_INDEX = Path(__file__).with_name("index.html")


def _dist_index() -> Optional[Path]:
    p = _DIST_DIR / "index.html"
    return p if p.is_file() else None


def _dist_assets_dir() -> Optional[Path]:
    p = _DIST_DIR / "assets"
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
        self._ui_mode = "dist" if _dist_index() else "legacy"

    async def index(self, request):
        dist = _dist_index()
        if dist is not None:
            return web.FileResponse(dist)
        return web.Response(
            text=_LEGACY_INDEX.read_text(encoding="utf-8"),
            content_type="text/html",
        )

    async def websocket_handler(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self._clients.add(ws)
        try:
            await ws.send_json(
                {
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
                }
            )
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        await self._handle_client_msg(data, ws)
                    except Exception as e:
                        print(f"[WS] msg error: {e}")
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
        elif t == "reset_config":
            self._config.reset()
            await ws.send_json({"type": "config_reset", "data": self._config.data})
        elif t == "log_start":
            mode = msg.get("mode", "events")
            self._logger.start(mode)
            await ws.send_json({"type": "log_status", "data": self._logger.status})
        elif t == "log_stop":
            path = self._logger.stop()
            await ws.send_json(
                {"type": "log_status", "data": self._logger.status, "last_file": path}
            )
        elif t == "request_graph":
            await ws.send_json(
                {"type": "graph_data", "data": self._tcu.snapshot_graph()}
            )
        elif t == "export_profile":
            export = {
                "version": "v12",
                "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "config": self._config.data,
            }
            await ws.send_json({"type": "profile_export", "data": export})
        elif t == "import_profile":
            try:
                imported = msg.get("data", {})
                if isinstance(imported, dict) and "config" in imported:
                    for k, v in imported["config"].items():
                        if k in DEFAULTS:
                            self._config.set(k, v)
                    await ws.send_json(
                        {
                            "type": "profile_imported",
                            "ok": True,
                            "data": self._config.data,
                        }
                    )
                else:
                    await ws.send_json(
                        {
                            "type": "profile_imported",
                            "ok": False,
                            "error": "invalid format",
                        }
                    )
            except Exception as e:
                await ws.send_json(
                    {"type": "profile_imported", "ok": False, "error": str(e)}
                )

    async def broadcast_loop(self):
        tcu_interval = 1.0 / 60.0
        broadcast_every_n = 2
        tick = 0
        last_packet_id = -1
        while True:
            await asyncio.sleep(tcu_interval)
            tick += 1
            td = self._recv.latest()
            current_id = self._recv.packets_total
            if td is not None and self._recv.is_live and current_id != last_packet_id:
                self._tcu.process(td, self._recv.latest_raw())
                last_packet_id = current_id
            if tick % broadcast_every_n != 0:
                continue
            if not self._clients:
                continue
            payload_tel = {"type": "telemetry", "data": self._tcu.snapshot(td)}
            payload_st = {
                "type": "state",
                "data": {
                    "mode": self._tcu.mode.value,
                    "live": self._recv.is_live,
                    "shift_count": self._tcu.shift_count,
                    "packets_total": self._recv.packets_total,
                },
            }
            dead = set()
            for client in list(self._clients):
                try:
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
        ui = f"Vue dist ({_DIST_DIR})" if self._ui_mode == "dist" else "legacy index.html"
        print(f"  [OK] Web UI ({ui})")
        asyncio.create_task(self.broadcast_loop())
