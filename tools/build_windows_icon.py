#!/usr/bin/env python3
"""Build a multi-resolution Windows ICO from the approved app icon."""

from __future__ import annotations

import argparse
import io
import struct
from pathlib import Path

from PIL import Image, ImageFilter


ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)


def render_frame(source: Image.Image, size: int) -> bytes:
    frame = source.resize((size, size), Image.Resampling.LANCZOS)
    if size <= 32:
        frame = frame.filter(ImageFilter.UnsharpMask(radius=0.7, percent=70))
    elif size <= 64:
        frame = frame.filter(ImageFilter.UnsharpMask(radius=0.8, percent=35))

    output = io.BytesIO()
    frame.save(output, format="PNG", optimize=True)
    return output.getvalue()


def build_ico(
    source_path: Path,
    small_source_path: Path,
    medium_source_path: Path,
    output_path: Path,
) -> None:
    with (
        Image.open(source_path) as source_image,
        Image.open(small_source_path) as small_image,
        Image.open(medium_source_path) as medium_image,
    ):
        source = source_image.convert("RGBA")
        small = small_image.convert("RGBA")
        medium = medium_image.convert("RGBA")
        frames = []
        for size in ICON_SIZES:
            frame_source = small if size <= 32 else medium if size <= 128 else source
            frames.append((size, render_frame(frame_source, size)))

    header_size = 6 + 16 * len(frames)
    offset = header_size
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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(
        struct.pack("<HHH", 0, 1, len(frames))
        + b"".join(entries)
        + b"".join(payloads)
    )
    print(f"Created {output_path} with sizes: {', '.join(map(str, ICON_SIZES))}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("assets/icon-concepts/glass-ribbon-apple-blue-v2.png"),
    )
    parser.add_argument(
        "--small-source",
        type=Path,
        default=Path("assets/icon-concepts/glass-ribbon-apple-blue-v2-32.png"),
    )
    parser.add_argument(
        "--medium-source",
        type=Path,
        default=Path("assets/icon-concepts/glass-ribbon-apple-blue-v2-128.png"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("assets/CVBuilder.ico"),
    )
    args = parser.parse_args()
    build_ico(
        args.source,
        args.small_source,
        args.medium_source,
        args.output,
    )


if __name__ == "__main__":
    main()
