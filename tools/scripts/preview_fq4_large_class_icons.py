#!/usr/bin/env python3
"""Create preview sheets for large FQ4 class sprite resources."""
from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
DISC = ROOT / "original" / "First Queen IV - Varcia Senki (Japan).bin"
MANIFEST = ROOT / "docs" / "fq4" / "analysis" / "001" / "original-files.json"
OUT = ROOT / "docs" / "fq4" / "analysis" / "024"


def ramp(value: int, start: tuple[int, int, int], end: tuple[int, int, int], lo: int, hi: int) -> tuple[int, int, int, int]:
    q = max(0, min(1, (value - lo) / max(1, hi - lo)))
    return tuple(int(a + (b - a) * q) for a, b in zip(start, end)) + (255,)


def rgba(value: int) -> tuple[int, int, int, int]:
    if value == 0:
        return (0, 0, 0, 0)
    if value == 3:
        return (5, 8, 18, 255)
    if 1 <= value <= 15:
        return ramp(value, (35, 38, 45), (248, 248, 242), 1, 15)
    if 40 <= value <= 55:
        return ramp(value, (65, 5, 5), (225, 35, 20), 40, 55)
    if 56 <= value <= 63:
        return ramp(value, (105, 35, 0), (255, 205, 35), 56, 63)
    if 64 <= value <= 79:
        return ramp(value, (55, 58, 65), (245, 245, 238), 64, 79)
    if 96 <= value <= 127:
        return ramp(value, (105, 45, 0), (255, 215, 45), 96, 127)
    return (100, 100, 105, 255)


def load_resource(index: int, raw_disc: bytes, files: dict[str, dict[str, object]]) -> tuple[bytes, str]:
    path = f"/CHR{index >> 4:X}/C{index:02X}.P"
    extent = files[path]["extents"][0]
    lba = int(extent["lba"])
    size = int(extent["size"])
    data = b"".join(
        raw_disc[(lba + sector) * 2352 + 24 : (lba + sector) * 2352 + 2072]
        for sector in range((size + 2047) // 2048)
    )[:size]
    return data, path


def tile_offset(tile_x: int, tile_y: int, width_tiles: int, height_tiles: int, column_major: bool) -> int:
    if column_major:
        return tile_x * height_tiles + tile_y
    return tile_y * width_tiles + tile_x


def render_frame(
    data: bytes, base_tile: int, width_tiles: int, height_tiles: int, column_major: bool = False
) -> Image.Image:
    image = Image.new("RGBA", (width_tiles * 16, height_tiles * 16))
    pixels = []
    for y in range(height_tiles * 16):
        for x in range(width_tiles * 16):
            tile = base_tile + tile_offset(x // 16, y // 16, width_tiles, height_tiles, column_major)
            pixels.append(rgba(data[tile * 256 + (y % 16) * 16 + (x % 16)]))
    image.putdata(pixels)
    return image


def layout_for_tile_count(tile_count: int) -> tuple[int, int, int]:
    if tile_count >= 72 and tile_count % 9 == 0:
        return 9, 3, 3
    return 4, 2, 2


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw_disc = DISC.read_bytes()
    files = {
        item["path"].split(";")[0]: item
        for item in json.loads(MANIFEST.read_text(encoding="utf-8"))
    }
    class_ids = [174, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204]
    thumbs: list[tuple[int, int, Image.Image]] = []
    summary = []
    for class_id in class_ids:
        data, path = load_resource(class_id, raw_disc, files)
        tile_count = len(data) // 256
        tiles_per_frame, width_tiles, height_tiles = layout_for_tile_count(tile_count)
        frame_count = tile_count // tiles_per_frame
        bases = [tiles_per_frame * n for n in range(min(frame_count, 8))]
        for base_tile in bases:
            frame = render_frame(data, base_tile, width_tiles, height_tiles, column_major=tiles_per_frame == 9)
            thumbs.append((class_id, base_tile, frame.resize((width_tiles * 32, height_tiles * 32), Image.Resampling.NEAREST)))
        summary.append(
            {
                "class_id": class_id,
                "source": path,
                "bytes": len(data),
                "tiles": tile_count,
                "tiles_per_frame": tiles_per_frame,
                "candidate_frame_count": frame_count,
            }
        )

    cell_width = 178
    cell_height = 132
    columns = 5
    rows = math.ceil(len(thumbs) / columns)
    sheet = Image.new("RGB", (cell_width * columns, cell_height * rows), (235, 235, 235))
    draw = ImageDraw.Draw(sheet)
    for n, (class_id, base_tile, image) in enumerate(thumbs):
        x = (n % columns) * cell_width
        y = (n // columns) * cell_height
        sheet.paste(image, (x + 8, y + 24), image)
        draw.text((x + 8, y + 6), f"{class_id:03d} base {base_tile}", fill=(0, 0, 0))
    sheet.save(OUT / "large-class-frame-candidates.png")
    (OUT / "large-class-summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(OUT / "large-class-frame-candidates.png")


if __name__ == "__main__":
    main()
