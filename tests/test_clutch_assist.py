import time
from unittest.mock import MagicMock, call

import pytest
from virtual_tcu.config.store import ConfigStore
from virtual_tcu.input.keyboard_output import KeyboardOutput
from virtual_tcu.state.shift_history import ShiftHistory
from virtual_tcu.telemetry.model import Telemetry


@pytest.fixture
def mock_keyboard(monkeypatch):
    mock_press = MagicMock()
    mock_release = MagicMock()
    monkeypatch.setattr("keyboard.press", mock_press)
    monkeypatch.setattr("keyboard.release", mock_release)
    monkeypatch.setattr("time.sleep", MagicMock())
    return mock_press, mock_release


def test_keyboard_output_no_clutch(mock_keyboard):
    mock_press, mock_release = mock_keyboard
    config = ConfigStore()
    config.set("feat_clutch_assist", False)
    config.set("shift_key_up", "e")

    kb = KeyboardOutput(config)
    kb._press_release_bare = kb._press_release  # Store original method
    kb._press_release("e")

    mock_press.assert_called_once_with("e")
    mock_release.assert_called_once_with("e")


def test_keyboard_output_with_clutch(mock_keyboard):
    mock_press, mock_release = mock_keyboard
    config = ConfigStore()
    config.set("feat_clutch_assist", True)
    config.set("clutch_key", "shift")

    kb = KeyboardOutput(config)
    kb._press_release_with_clutch("e")

    assert mock_press.call_args_list == [call("shift"), call("e")]
    assert mock_release.call_args_list == [call("e"), call("shift")]
    assert kb.is_self_press("shift")
    assert kb.is_self_press("e")


def test_shift_history_sent_at():
    sh = ShiftHistory()
    td = Telemetry()
    td.gear = 2

    now = time.time()
    sh.record("UP", td, sent_at=now)

    snapshot = sh.snapshot()
    assert len(snapshot) == 1
    assert "shift_sent_at" in snapshot[0]
    assert snapshot[0]["shift_sent_at"] == now
