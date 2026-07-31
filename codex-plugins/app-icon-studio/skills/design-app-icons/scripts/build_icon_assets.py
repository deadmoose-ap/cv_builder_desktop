#!/usr/bin/env python3
"""Build macOS iconset/ICNS and Windows ICO from approved raster masters."""

from __future__ import annotations

import argparse
import io
import struct
from pathlib import Path

from PIL import Image, ImageFilter


MAC_REPRESENTATIONS = (
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
)
ICNS_CHUNKS = (
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
WINDOWS_SIZES = (16, 24, 32, 48, 64, 128, 256)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def load_rgba(path: Path) -> Image.Image:
    with Image.open(path) as image:
        result = image.convert("RGBA")
    if result.width != result.height:
        raise ValueError(f"{path} must be square, got {result.size}")
    return result


def render(source: Image.Image, size: int) -> Image.Image:
    frame = source.resize((size, size), Image.Resampling.LANCZOS)
    if size <= 32:
        return frame.filter(ImageFilter.UnsharpMask(radius=0.7, percent=70))
    if size <= 64:
        return frame.filter(ImageFilter.UnsharpMask(radius=0.8, percent=35))
    if size <= 128:
        return frame.filter(ImageFilter.UnsharpMask(radius=0.9, percent=20))
    return frame


def png_bytes(image: Image.Image) -> bytes:
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def select_source(
    size: int,
    full: Image.Image,
    small: Image.Image,
    medium: Image.Image,
) -> Image.Image:
    if size <= 32:
        return small
    if size <= 128:
        return medium
    return full


def build_iconset(
    iconset: Path,
    full: Image.Image,
    small: Image.Image,
    medium: Image.Image,
) -> None:
    iconset.mkdir(parents=True, exist_ok=True)
    for filename, size in MAC_REPRESENTATIONS:
        source = select_source(size, full, small, medium)
        render(source, size).save(iconset / filename, format="PNG", optimize=True)


def validate_png(path: Path, expected_size: int) -> bytes:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise ValueError(f"{path} is not a PNG")
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (expected_size, expected_size):
        raise ValueError(
            f"{path} must be {expected_size}x{expected_size}, got {width}x{height}"
        )
    return data


def build_icns(iconset: Path, output: Path) -> None:
    chunks = []
    for chunk_type, filename, expected_size in ICNS_CHUNKS:
        png = validate_png(iconset / filename, expected_size)
        chunks.append(
            chunk_type.encode("ascii") + struct.pack(">I", len(png) + 8) + png
        )
    payload = b"".join(chunks)
    output.write_bytes(b"icns" + struct.pack(">I", len(payload) + 8) + payload)


def build_ico(
    output: Path,
    full: Image.Image,
    small: Image.Image,
    medium: Image.Image,
) -> None:
    frames = []
    for size in WINDOWS_SIZES:
        source = select_source(size, full, small, medium)
        frames.append((size, png_bytes(render(source, size))))

    offset = 6 + 16 * len(frames)
    entries = []
    payloads = []
    for size, payload in frames:
        dimension = 0 if size == 256 else size
        entries.append(
            struct.pack(
                "<BBBBHHII",
                dimension,
                dimension,
                0,
                0,
                1,
                32,
                len(payload),
                offset,
            )
        )
        payloads.append(payload)
        offset += len(payload)

    output.write_bytes(
        struct.pack("<HHH", 0, 1, len(frames))
        + b"".join(entries)
        + b"".join(payloads)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--small-source", type=Path)
    parser.add_argument("--medium-source", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--name", default="AppIcon")
    args = parser.parse_args()

    full = load_rgba(args.source)
    small = load_rgba(args.small_source) if args.small_source else full
    medium = load_rgba(args.medium_source) if args.medium_source else full
    args.output_dir.mkdir(parents=True, exist_ok=True)

    iconset = args.output_dir / f"{args.name}.iconset"
    build_iconset(iconset, full, small, medium)
    build_icns(iconset, args.output_dir / f"{args.name}.icns")
    build_ico(args.output_dir / f"{args.name}.ico", full, small, medium)
    render(medium, 128).save(
        args.output_dir / f"{args.name}-128.png", format="PNG", optimize=True
    )
    render(small, 32).save(
        args.output_dir / f"{args.name}-32.png", format="PNG", optimize=True
    )
    print(f"Created icon assets in {args.output_dir}")


if __name__ == "__main__":
    main()

