import json
from pathlib import Path

from virtual_tcu import paths


def _key(car_key: tuple[int, int, int]) -> str:
    """Composite key — car_ordinal, car_class, PI disambiguate tuned variants."""
    return f"{car_key[0]}_{car_key[1]}_{car_key[2]}"


class ProfileStore:
    """Per-car JSON-backed profile storage.

    Profiles are keyed by ``(car_ordinal, car_class, pi)`` so different
    tunes of the same car model get separate saved state.
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

    def get(self, car_key: tuple[int, int, int]) -> dict | None:
        return self.data.get(_key(car_key))

    def set(self, car_key: tuple[int, int, int], profile: dict):
        self.data[_key(car_key)] = profile
        self.save()
