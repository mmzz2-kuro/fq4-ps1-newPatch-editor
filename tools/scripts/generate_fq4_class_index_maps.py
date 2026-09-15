#!/usr/bin/env python3
"""Generate readable pixel-index maps for sampled FQ4 class sprites."""
from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

import extract_fq4_class_icons as icons

ROOT = Path(__file__).resolve().parents[2]
UI = ROOT / "tools" / "FQ4SaveEditor"
OUT = ROOT / "docs" / "fq4" / "analysis" / "032"
SEED = 20260914
SAMPLE_COUNT = 10


def load_resource(class_id: int, raw_disc: bytes, files: dict[str, dict[str, object]]) -> bytes:
    path = f"/CHR{class_id >> 4:X}/C{class_id:02X}.P"
    extent = files[path]["extents"][0]
    lba = int(extent["lba"])
    size = int(extent["size"])
    return b"".join(
        raw_disc[(lba + sector) * 2352 + 24 : (lba + sector) * 2352 + 2072]
        for sector in range((size + 2047) // 2048)
    )[:size]


def frame_indices(class_id: int, data: bytes) -> tuple[bytes, dict[str, object]]:
    base_tile, width_tiles, height_tiles, column_major, status = icons.layout(class_id, data)
    frame, _ = icons.render_frame(data, base_tile, width_tiles, height_tiles, column_major, class_id)
    return frame, {
        "base_tile": base_tile,
        "width_tiles": width_tiles,
        "height_tiles": height_tiles,
        "column_major": column_major,
        "image_status": status,
        "tile_count": len(data) // 256,
    }


def score_candidate(indices: set[int], selected: list[dict[str, object]]) -> tuple[int, int]:
    used = set()
    for item in selected:
        used.update(item["indices"])
    new_count = len(indices - used)
    overlap = len(indices & used)
    return new_count, -overlap


def choose_samples(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    rng = random.Random(SEED)
    pool = candidates[:]
    rng.shuffle(pool)
    selected = [max(pool, key=lambda item: len(item["indices"]))]
    pool.remove(selected[0])
    while len(selected) < SAMPLE_COUNT and pool:
        best = max(pool, key=lambda item: (score_candidate(item["indices"], selected), rng.random()))
        selected.append(best)
        pool.remove(best)
    return sorted(selected, key=lambda item: item["class_id"])


def render_index_map(class_id: int, name: str, frame: bytes, layout: dict[str, object], path: Path) -> None:
    width = int(layout["width_tiles"]) * 16
    height = int(layout["height_tiles"]) * 16
    cell = 16 if max(width, height) <= 48 else 10
    image = Image.new("RGB", (width * cell, height * cell), (245, 245, 245))
    draw = ImageDraw.Draw(image)
    for y in range(height):
        for x in range(width):
            value = frame[y * width + x]
            color = (255, 255, 255) if value == 0 else icons.rgba_for_class(class_id, value)[:3]
            x0 = x * cell
            y0 = y * cell
            draw.rectangle([x0, y0, x0 + cell - 1, y0 + cell - 1], fill=color)
            if value:
                text_color = (0, 0, 0) if sum(color) > 430 else (255, 255, 255)
                draw.text((x0 + 1, y0 + 1), str(value), fill=text_color)
    image.save(path)


def make_sheet(samples: list[dict[str, object]], names: list[str]) -> None:
    thumbs = []
    for item in samples:
        class_id = int(item["class_id"])
        image = Image.open(OUT / f"class-{class_id:03d}-index-map.png").convert("RGB")
        image.thumbnail((260, 260), Image.Resampling.NEAREST)
        thumbs.append((class_id, names[class_id], image))
    cols = 2
    cell_w = 420
    cell_h = 315
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (235, 235, 235))
    draw = ImageDraw.Draw(sheet)
    for n, (class_id, name, image) in enumerate(thumbs):
        x = (n % cols) * cell_w
        y = (n // cols) * cell_h
        draw.rectangle([x + 2, y + 2, x + cell_w - 4, y + cell_h - 4], outline=(185, 185, 185), fill=(224, 224, 224))
        draw.text((x + 10, y + 8), f"{class_id:03d}  {name}", fill=(0, 0, 0))
        sheet.paste(image, (x + 10, y + 32))
    sheet.save(OUT / "random-index-map-samples.png")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    raw_disc = icons.DISC.read_bytes()
    files = {
        item["path"].split(";")[0]: item
        for item in json.loads(icons.MANIFEST.read_text(encoding="utf-8"))
    }
    names = json.loads((UI / "class_names.json").read_text(encoding="utf-8-sig"))
    candidates = []
    for class_id in range(len(names)):
        data = load_resource(class_id, raw_disc, files)
        frame, layout = frame_indices(class_id, data)
        index_counts = Counter(frame)
        indices = {value for value in index_counts if value != 0}
        candidates.append(
            {
                "class_id": class_id,
                "name": names[class_id],
                "frame": frame,
                "indices": indices,
                "index_counts": dict(sorted(index_counts.items())),
                "layout": layout,
            }
        )
    samples = choose_samples(candidates)
    report_samples = []
    for item in samples:
        class_id = int(item["class_id"])
        render_index_map(
            class_id,
            str(item["name"]),
            item["frame"],
            item["layout"],
            OUT / f"class-{class_id:03d}-index-map.png",
        )
        report_samples.append(
            {
                "class_id": class_id,
                "name": item["name"],
                "indices": sorted(item["indices"]),
                "unique_index_count": len(item["indices"]),
                "layout": item["layout"],
                "index_counts": item["index_counts"],
            }
        )
    make_sheet(samples, names)
    covered = sorted({value for item in samples for value in item["indices"]})
    (OUT / "index-map-sample-report.json").write_text(
        json.dumps(
            {
                "seed": SEED,
                "sample_count": len(samples),
                "covered_indices": covered,
                "covered_index_count": len(covered),
                "samples": report_samples,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"sample_count": len(samples), "covered_index_count": len(covered), "output": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
