import time


class DiscordRPC:
    DISCORD_CLIENT_ID = ""

    def __init__(self):
        self._rpc = None
        self._enabled = False
        self._last_update = 0.0
        if not self.DISCORD_CLIENT_ID:
            return
        try:
            from pypresence import Presence

            self._rpc = Presence(self.DISCORD_CLIENT_ID)
            self._rpc.connect()
            self._enabled = True
            print("  [OK] Discord RPC connected")
        except Exception:
            pass

    def update(self, mode: str, shift_count: int, speed_kmh: float = 0.0):
        if not self._enabled or self._rpc is None:
            return
        if (time.time() - self._last_update) < 15.0:
            return
        try:
            self._rpc.update(
                state=f"Mode: {mode}",
                details=f"{shift_count} shifts | {speed_kmh:.0f} km/h",
                large_image="logo",
                large_text="Virtual TCU for FH6",
            )
            self._last_update = time.time()
        except Exception:
            self._enabled = False

    def close(self):
        if self._rpc:
            try:
                self._rpc.close()
            except Exception:
                pass
