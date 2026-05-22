import threading
import time

import keyboard

from virtual_tcu.config.constants import Cfg

class VirtualKeyboard:
    KEY_UP = "e"
    KEY_DOWN = "q"

    def __init__(self):
        self._self_press_until = {"e": 0.0, "q": 0.0}
        self.SELF_PRESS_WINDOW_S = 0.15

    def is_self_press(self, key: str) -> bool:
        return time.time() < self._self_press_until.get(key, 0.0)

    def _press_release(self, key: str):
        try:
            self._self_press_until[key] = time.time() + self.SELF_PRESS_WINDOW_S
            keyboard.press(key)
            time.sleep(Cfg.KEY_HOLD_S)
            keyboard.release(key)
        except Exception as e:
            print(f"[KB] {e}")

    def shift_up(self):
        threading.Thread(
            target=self._press_release, args=(self.KEY_UP,), daemon=True
        ).start()

    def shift_down(self):
        threading.Thread(
            target=self._press_release, args=(self.KEY_DOWN,), daemon=True
        ).start()

    def shift_down_double(self):
        """Two Q presses with 60ms gap — skip-gear for hard braking."""
        def _double():
            self._press_release(self.KEY_DOWN)
            time.sleep(0.06)
            self._press_release(self.KEY_DOWN)
        threading.Thread(target=_double, daemon=True).start()

