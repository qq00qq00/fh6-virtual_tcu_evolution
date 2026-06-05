import json
from pathlib import Path

from virtual_tcu import paths
from virtual_tcu.telemetry.car_key import storage_key


class ProfileStore:
    """Per-car JSON-backed profile storage.

    Profiles are keyed by ``(car_ordinal, car_class, pi, tune_id)`` so different
    tunes of the same car model get separate saved state. Legacy three-part keys
    (no tune_id) are still read for backward compatibility.
    """

    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path is not None else paths.profiles_file()
        self.data: dict[str, dict] = {}
        self.load()

    def load(self):
        if self.path.exists():
            try:
                self.data = json.loads(self.path.read_text())
            except Exception:
                self.data = {}

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps(self.data, indent=2))
        except Exception as e:
            print(f"[Profiles] save failed: {e}")

    def _legacy_key(self, car_key: tuple[int, ...]) -> str | None:
        if len(car_key) >= 3:
            return f"{car_key[0]}_{car_key[1]}_{car_key[2]}"
        return None

    def get(self, car_key: tuple[int, ...]) -> dict | None:
        k = storage_key(car_key)
        if k in self.data:
            return self.data[k]
        legacy = self._legacy_key(car_key)
        if legacy and legacy in self.data:
            return self.data[legacy]
        return None

    def set(self, car_key: tuple[int, ...], profile: dict):
        self.data[storage_key(car_key)] = profile
        self.save()
