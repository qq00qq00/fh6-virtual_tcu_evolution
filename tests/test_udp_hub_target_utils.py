"""Parity checks for UDP hub target parsing (packages/shared/src/utils/udpHubTargets.ts)."""

from __future__ import annotations

import re

_TARGET_SPLIT_RE = re.compile(r"[\s,;]+")


def _normalize(entry: str) -> str | None:
    item = entry.strip()
    if not item:
        return None
    split_at = item.rfind(":")
    has_host = split_at >= 0
    host_text = item[:split_at] if has_host else "127.0.0.1"
    port_text = item[split_at + 1 :] if has_host else item
    host = (host_text or "127.0.0.1").strip()
    try:
        port = int(port_text.strip())
    except ValueError:
        return None
    if port < 1 or port > 65535 or not host:
        return None
    if host.lower() == "localhost":
        host = "127.0.0.1"
    return f"{host}:{port}"


def _split(raw: str) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()
    for entry in _TARGET_SPLIT_RE.split(raw):
        if not entry.strip():
            continue
        norm = _normalize(entry)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        tags.append(norm)
    return tags


def _serialize(tags: list[str]) -> str:
    return ", ".join(t.strip() for t in tags if t.strip())


def test_split_legacy_comma_separated():
    raw = "127.0.0.1:5556, 192.168.1.50:5555"
    assert _split(raw) == ["127.0.0.1:5556", "192.168.1.50:5555"]
    assert _serialize(_split(raw)) == "127.0.0.1:5556, 192.168.1.50:5555"


def test_normalize_port_only_defaults_host():
    assert _normalize("5556") == "127.0.0.1:5556"
