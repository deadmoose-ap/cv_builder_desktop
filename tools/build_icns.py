#!/usr/bin/env python3
"""Build a modern PNG-backed ICNS file from a macOS .iconset directory."""

from __future__ import annotations

import argparse
import struct
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
CHUNKS = (
    ("ic12", "icon_32x32@2x.png", 64),
    ("ic07", "icon_128x128.png", 128),
    ("ic13", "icon_128x128@2x.png", 256),
    ("ic08", "icon_256x256.png", 256),
    ("ic04", "icon_16x16.png", 16),
    ("ic14", "icon_256x256@2x.png", 512),
    ("ic09", "icon_512x512.png", 512),
    ("ic05", "icon_32x32.png", 32),
    ("ic10", "icon_512x512@2x.png", 1024),
    ("ic11", "icon_16x16@2x.png", 32),
)


def read_png(path: Path, expected_size: int) -> bytes:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError(f"{path} is not a PNG file")
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (expected_size, expected_size):
        raise ValueError(
            f"{path} must be {expected_size}x{expected_size}, "
            f"got {width}x{height}"
        )
    return data


def build_icon(iconset: Path, output: Path) -> None:
    chunks = []
    for chunk_type, filename, expected_size in CHUNKS:
        png = read_png(iconset / filename, expected_size)
        chunks.append(
            chunk_type.encode("ascii") + struct.pack(">I", len(png) + 8) + png
        )

    payload = b"".join(chunks)
    output.write_bytes(b"icns" + struct.pack(">I", len(payload) + 8) + payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("iconset", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build_icon(args.iconset, args.output)
    print(f"Created {args.output}")


if __name__ == "__main__":
    main()
