"""Convert a PNG (or other Pillow-supported image) to a multi-res Windows ICO."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError as err:
    print("Install Pillow first: pip install pillow", file=sys.stderr)
    raise SystemExit(1) from err

SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("icon.png")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).with_name("icon.ico")
    if not src.is_file():
        print(f"Source not found: {src}", file=sys.stderr)
        raise SystemExit(1)
    img = Image.open(src).convert("RGBA")
    # Windows ICO requires square frames; largest must be >= 256x256 for electron-builder.
    side = max(img.size)
    square = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    square.paste(img, ((side - img.width) // 2, (side - img.height) // 2))
    img = square
    img.save(out, format="ICO", sizes=SIZES)
    print(f"Wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
