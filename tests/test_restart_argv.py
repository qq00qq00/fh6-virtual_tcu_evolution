"""Restart argv must keep ``python -m virtual_tcu`` semantics after exec."""

import sys

from virtual_tcu.bootstrap import restart_argv


def test_restart_argv_after_module_launch(monkeypatch):
    monkeypatch.setattr(sys, "executable", r"C:\Python\python.exe")
    monkeypatch.setattr(
        sys,
        "argv",
        [r"E:\repo\virtual_tcu\__main__.py", "--backend-only"],
    )
    monkeypatch.delattr(sys, "frozen", raising=False)

    assert restart_argv() == [r"C:\Python\python.exe", "-m", "virtual_tcu", "--backend-only"]


def test_restart_argv_preserves_explicit_module_invocation(monkeypatch):
    monkeypatch.setattr(sys, "executable", "/usr/bin/python3")
    monkeypatch.setattr(sys, "argv", ["/usr/bin/python3", "-m", "virtual_tcu", "--backend-only"])
    monkeypatch.delattr(sys, "frozen", raising=False)

    assert restart_argv() == ["/usr/bin/python3", "-m", "virtual_tcu", "--backend-only"]


def test_restart_argv_frozen_exe(monkeypatch):
    monkeypatch.setattr(sys, "executable", r"C:\Apps\VirtualTCU.exe")
    monkeypatch.setattr(sys, "argv", [r"C:\Apps\VirtualTCU.exe", "--backend-only"])
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    assert restart_argv() == [r"C:\Apps\VirtualTCU.exe", "--backend-only"]
