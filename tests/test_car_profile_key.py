"""Per-tune profile keys and ratio-drift slot splitting."""

from tests.conftest import CAR_KEY, CAR_KEY_BASE, make_telemetry
from virtual_tcu.config.store import ConfigStore  # noqa: E402
from virtual_tcu.input.interface import OutputInterface  # noqa: E402
from virtual_tcu.logic.tcu import TCULogic  # noqa: E402
from virtual_tcu.storage.profiles import ProfileStore  # noqa: E402
from virtual_tcu.telemetry.car_key import storage_key  # noqa: E402
from virtual_tcu.telemetry.logger import TelemetryLogger  # noqa: E402


class _Out(OutputInterface):
    @property
    def key_up(self) -> str:
        return "e"

    @property
    def key_down(self) -> str:
        return "q"

    def is_self_press(self, key: str) -> bool:
        return False

    def shift_to(self, from_gear: int, target_gear: int):
        pass

    def shutdown(self):
        pass


def test_profile_store_legacy_three_part_key(tmp_path):
    prof = ProfileStore(path=str(tmp_path / "prof.json"))
    prof.data["100_5_800"] = {"gear_ratios": {"1": 100.0}, "gear_counts": {"1": 10}}
    prof.save()

    got = prof.get(CAR_KEY)
    assert got is not None
    assert got["gear_ratios"]["1"] == 100.0


def test_profile_store_four_part_storage_key(tmp_path):
    prof = ProfileStore(path=str(tmp_path / "prof.json"))
    prof.set(CAR_KEY, {"gear_ratios": {"1": 90.0}})

    assert storage_key(CAR_KEY) in prof.data
    assert prof.get(CAR_KEY)["gear_ratios"]["1"] == 90.0


def test_ratio_drift_splits_tune_slot(tmp_path, monkeypatch):
    import virtual_tcu.logic.tcu as tcu_mod

    clock = {"now": 1000.0}
    monkeypatch.setattr(tcu_mod.time, "time", lambda: clock["now"])

    cfg = ConfigStore(path=str(tmp_path / "cfg.json"))
    prof = ProfileStore(path=str(tmp_path / "prof.json"))
    tcu = TCULogic(_Out(), prof, cfg, TelemetryLogger())
    tcu._current_car_key = CAR_KEY
    tcu._profile_baseline_gear1[CAR_KEY] = 100.0
    tcu._calibrator.load(
        CAR_KEY,
        {"ratios": {1: 150.0, 2: 80.0}, "counts": {1: 50, 2: 50}},
    )

    td = make_telemetry(gear=1, speed_ms=30.0, current_rpm=4500.0)
    td.profile_tune_id = CAR_KEY[3]
    tcu._tune_id_by_base[CAR_KEY_BASE] = CAR_KEY[3]

    tcu._check_tune_ratio_drift(td)

    new_id = tcu._tune_id_by_base[CAR_KEY_BASE]
    assert new_id != CAR_KEY[3]
    assert tcu._current_car_key is not None
    assert tcu._current_car_key[3] == new_id
    assert tcu._profile_baseline_gear1.get(tcu._current_car_key) is None
