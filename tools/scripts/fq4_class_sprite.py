#!/usr/bin/env python3
"""Independent FQ4 class-sprite reader and palette renderer."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from PIL import Image

SECTOR_SIZE = 2352
USER_DATA_OFFSET = 24
USER_DATA_SIZE = 2048


def ramp(value: int, start: tuple[int, int, int], end: tuple[int, int, int], low: int, high: int):
    ratio = max(0.0, min(1.0, (value - low) / max(1, high - low)))
    return tuple(int(a + (b - a) * ratio) for a, b in zip(start, end)) + (255,)


def default_rgba(value: int):
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


def existing_rgba(class_id: int, value: int):
    """Return the exact fallback palette used by the existing extractor."""
    if class_id == 0:
        if value == 0:
            return (0, 0, 0, 0)
        if value == 3:
            return (4, 8, 18, 255)
        if 1 <= value <= 15:
            return ramp(value, (5, 10, 18), (52, 58, 68), 1, 15)
        if 16 <= value <= 31:
            return ramp(value, (45, 95, 135), (218, 245, 255), 16, 31)
        if 40 <= value <= 47:
            return ramp(value, (70, 35, 4), (190, 105, 18), 40, 47)
        if 48 <= value <= 63:
            return ramp(value, (75, 34, 0), (220, 128, 22), 48, 63)
        if 80 <= value <= 95:
            return ramp(value, (70, 78, 86), (248, 248, 244), 80, 95)
        if 96 <= value <= 119:
            return ramp(value, (28, 115, 50), (60, 210, 85), 96, 119)
        if 120 <= value <= 127:
            return ramp(value, (160, 92, 45), (255, 199, 135), 120, 127)
    if class_id == 10:
        if value == 0:
            return (0, 0, 0, 0)
        if value == 3:
            return (4, 6, 12, 255)
        if 1 <= value <= 15:
            return ramp(value, (5, 8, 12), (35, 35, 38), 1, 15)
        if 16 <= value <= 31:
            return ramp(value, (60, 105, 125), (170, 220, 235), 16, 31)
        if 40 <= value <= 47:
            return ramp(value, (145, 84, 8), (255, 212, 55), 40, 47)
        if 48 <= value <= 63:
            return ramp(value, (95, 42, 0), (238, 116, 12), 48, 63)
        if 80 <= value <= 95:
            return ramp(value, (12, 118, 26), (88, 235, 48), 80, 95)
        if 96 <= value <= 119:
            return ramp(value, (8, 95, 22), (48, 190, 38), 96, 119)
        if 120 <= value <= 127:
            return ramp(value, (172, 100, 55), (255, 207, 150), 120, 127)
    return default_rgba(value)


def parse_hex_color(text: str) -> tuple[int, int, int]:
    value = text.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError("색상은 #RRGGBB 형식이어야 합니다.")
    try:
        rgb = tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError as exc:
        raise ValueError("색상은 #RRGGBB 형식이어야 합니다.") from exc
    return rgb  # type: ignore[return-value]


def format_hex_color(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def layout(class_id: int, data: bytes):
    tiles = len(data) // 256
    if class_id == 217:
        return 0, 6, 6, True, "6x6 base 0"
    if class_id == 218:
        return 0, 8, 8, True, "8x8 base 0"
    if 211 <= class_id <= 216:
        return 64, 4, 4, True, "4x4 base 64"
    if tiles >= 72 and tiles % 9 == 0:
        return 36, 3, 3, True, "3x3 base 36"
    if tiles >= 20:
        return 16, 2, 2, True, "2x2 base 16"
    return 0, 2, 2, True, "2x2 base 0"


def tile_offset(tile_x: int, tile_y: int, width: int, height: int, column_major: bool):
    return tile_x * height + tile_y if column_major else tile_y * width + tile_x


def frame_indices(data: bytes, base: int, width: int, height: int, column_major: bool) -> bytes:
    result = bytearray()
    for y in range(height * 16):
        for x in range(width * 16):
            tile = base + tile_offset(x // 16, y // 16, width, height, column_major)
            result.append(data[tile * 256 + (y % 16) * 16 + (x % 16)])
    return bytes(result)


def fit_large_icon(image: Image.Image) -> Image.Image:
    bbox = image.getbbox()
    if bbox:
        image = image.crop(bbox)
    if image.width > 64 or image.height > 64:
        scale = min(64 / image.width, 64 / image.height)
        image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.Resampling.NEAREST)
    canvas = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    canvas.alpha_composite(image, ((64 - image.width) // 2, (64 - image.height) // 2))
    return canvas


def fit_large_index_map(image: Image.Image) -> Image.Image:
    """Apply the icon crop/scale/centering rules while preserving index values."""
    bbox = image.getbbox()
    if bbox:
        image = image.crop(bbox)
    if image.width > 64 or image.height > 64:
        scale = min(64 / image.width, 64 / image.height)
        image = image.resize(
            (max(1, int(image.width * scale)), max(1, int(image.height * scale))),
            Image.Resampling.NEAREST,
        )
    canvas = Image.new("L", (64, 64), 0)
    canvas.paste(image, ((64 - image.width) // 2, (64 - image.height) // 2))
    return canvas


@dataclass(frozen=True)
class SpriteFrame:
    class_id: int
    name: str
    indices: bytes
    width: int
    height: int
    layout_name: str

    @property
    def used_indices(self) -> list[int]:
        return sorted(set(self.indices))


class SpriteArchive:
    def __init__(self, disc_path: Path, manifest_path: Path, names_path: Path):
        self.disc_path = Path(disc_path)
        self.raw = self.disc_path.read_bytes()
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        self.files = {entry["path"].split(";")[0]: entry for entry in manifest}
        self.names = json.loads(Path(names_path).read_text(encoding="utf-8-sig"))
        self._cache: dict[int, SpriteFrame] = {}

    def __len__(self):
        return len(self.names)

    def resource(self, class_id: int) -> bytes:
        path = f"/CHR{class_id >> 4:X}/C{class_id:02X}.P"
        record = self.files[path]
        chunks = []
        for extent in record["extents"]:
            sectors = (extent["size"] + USER_DATA_SIZE - 1) // USER_DATA_SIZE
            chunks.extend(
                self.raw[(extent["lba"] + n) * SECTOR_SIZE + USER_DATA_OFFSET:
                         (extent["lba"] + n) * SECTOR_SIZE + USER_DATA_OFFSET + USER_DATA_SIZE]
                for n in range(sectors)
            )
        return b"".join(chunks)[:record["size"]]

    def frame(self, class_id: int) -> SpriteFrame:
        if class_id not in self._cache:
            data = self.resource(class_id)
            base, width, height, column_major, description = layout(class_id, data)
            indices = frame_indices(data, base, width, height, column_major)
            self._cache[class_id] = SpriteFrame(class_id, self.names[class_id], indices, width * 16, height * 16, description)
        return self._cache[class_id]


def render_icon(frame: SpriteFrame, overrides: Mapping[int, tuple[int, int, int]] | None = None) -> Image.Image:
    overrides = overrides or {}
    pixels = []
    for index in frame.indices:
        if index != 0 and index in overrides:
            pixels.append((*overrides[index], 255))
        else:
            pixels.append(existing_rgba(frame.class_id, index))
    image = Image.new("RGBA", (frame.width, frame.height))
    image.putdata(pixels)
    if frame.width >= 48 and frame.height >= 48:
        return fit_large_icon(image)
    return image.resize((64, 64), Image.Resampling.NEAREST)


def render_index_map(frame: SpriteFrame) -> Image.Image:
    """Return the exact 64x64 palette-index map corresponding to render_icon."""
    image = Image.frombytes("L", (frame.width, frame.height), frame.indices)
    if frame.width >= 48 and frame.height >= 48:
        return fit_large_index_map(image)
    return image.resize((64, 64), Image.Resampling.NEAREST)


def index_display_color(value: int) -> tuple[int, int, int, int]:
    if value == 0:
        return (42, 42, 46, 255)
    return ((value * 73) % 206 + 50, (value * 151) % 206 + 50, (value * 199) % 206 + 50, 255)


def render_index_icon(frame: SpriteFrame, selected_index: int | None = None) -> Image.Image:
    index_map = render_index_map(frame)
    pixels = []
    for value in index_map.tobytes():
        base = index_display_color(value)
        if selected_index is not None and value != selected_index:
            pixels.append(tuple(channel // 4 for channel in base[:3]) + (255,))
        elif selected_index is not None:
            pixels.append((255, 255, 255, 255))
        else:
            pixels.append(base)
    image = Image.new("RGBA", (64, 64))
    image.putdata(pixels)
    return image


def load_palette_file(path: Path) -> dict[int, dict[int, tuple[int, int, int]]]:
    if not path.exists():
        return {}
    document = json.loads(path.read_text(encoding="utf-8"))
    result: dict[int, dict[int, tuple[int, int, int]]] = {}
    for class_key, entries in document.get("classes", {}).items():
        class_id = int(class_key)
        result[class_id] = {int(index): parse_hex_color(color) for index, color in entries.items() if int(index) != 0}
    return result


def save_palette_file(path: Path, palettes: Mapping[int, Mapping[int, tuple[int, int, int]]]):
    classes = {}
    for class_id in sorted(palettes):
        values = {str(index): format_hex_color(rgb) for index, rgb in sorted(palettes[class_id].items()) if index != 0}
        if values:
            classes[str(class_id)] = values
    document = {"version": 1, "format": "FQ4 class palette overrides", "classes": classes}
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def copy_palette_overrides(
    source: Mapping[int, tuple[int, int, int]],
    target: Mapping[int, tuple[int, int, int]],
    target_used_indices: set[int],
    mode: str = "merge",
    selected_index: int | None = None,
) -> tuple[dict[int, tuple[int, int, int]], int, int]:
    """Copy source overrides to a target, limited to indices used by the target."""
    if mode not in ("merge", "replace"):
        raise ValueError("mode must be 'merge' or 'replace'")
    candidates = {
        index: rgb for index, rgb in source.items()
        if index != 0 and (selected_index is None or index == selected_index)
    }
    result = dict(target) if mode == "merge" else {}
    applicable = {index: rgb for index, rgb in candidates.items() if index in target_used_indices}
    result.update(applicable)
    return result, len(applicable), len(candidates) - len(applicable)
