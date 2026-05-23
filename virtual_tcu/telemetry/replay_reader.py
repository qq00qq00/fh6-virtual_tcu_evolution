import gzip
import struct
from pathlib import Path
from typing import BinaryIO, Iterator, Tuple, Union

from virtual_tcu.telemetry.logger import LOG_MAGIC

Record = Tuple[int, bytes]


def open_replay(path: Union[str, Path]) -> BinaryIO:
    path = Path(path)
    if path.suffix == ".gz":
        return gzip.open(path, "rb")
    return path.open("rb")


def iter_replay_records(path: Union[str, Path]) -> Iterator[Record]:
    """Yield (relative_ms, raw_udp_packet) from a TCULOG01 replay file."""
    with open_replay(path) as f:
        magic = f.read(len(LOG_MAGIC))
        if magic != LOG_MAGIC:
            raise ValueError(f"invalid replay magic: {magic!r} (expected {LOG_MAGIC!r})")
        while True:
            header = f.read(6)
            if not header:
                break
            if len(header) < 6:
                raise ValueError("truncated record header")
            rel_ms, packet_len = struct.unpack("<IH", header)
            raw = f.read(packet_len)
            if len(raw) < packet_len:
                raise ValueError(
                    f"truncated packet at {rel_ms} ms "
                    f"(expected {packet_len} bytes, got {len(raw)})"
                )
            yield rel_ms, raw
