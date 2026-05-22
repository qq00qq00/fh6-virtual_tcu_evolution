import json
from pathlib import Path
from typing import Optional

from virtual_tcu.config.constants import Cfg

class ProfileStore:
    def __init__(self, path: str = Cfg.PROFILES_FILE):
        self.path = Path(path)
        self.data: dict = {}
        self.load()

    def load(self):
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text())
            except Exception:
                self.data = {}

    def save(self):
        try:
            self.path.write_text(json.dumps(self.data, indent=2))
        except Exception as e:
            print(f"[Profiles] save failed: {e}")

    def get(self, car_ordinal: int) -> Optional[dict]:
        return self.data.get(str(car_ordinal))

    def set(self, car_ordinal: int, profile: dict):
        self.data[str(car_ordinal)] = profile
        self.save()
