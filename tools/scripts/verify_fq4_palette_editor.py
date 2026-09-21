#!/usr/bin/env python3
"""Verify PLAN-039 renderer compatibility and palette overrides."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from PIL import Image

from fq4_class_sprite import (
    SpriteArchive, copy_palette_overrides, existing_rgba, load_palette_file, render_icon,
    render_index_map, save_palette_file,
)

ROOT = Path(__file__).resolve().parents[2]


def main():
    archive = SpriteArchive(
        ROOT / "original/First Queen IV - Varcia Senki (Japan).bin",
        ROOT / "docs/fq4/analysis/001/original-files.json",
        ROOT / "tools/FQ4SaveEditor/class_names.json",
    )
    old_dir = ROOT / "tools/FQ4SaveEditor/class_icons"
    mismatches = []
    for class_id in range(len(archive)):
        generated = render_icon(archive.frame(class_id))
        old = Image.open(old_dir / f"class-{class_id:03}.png").convert("RGBA")
        if generated.tobytes() != old.tobytes():
            mismatches.append(class_id)

    test_palette = {25: {3: (12, 34, 56), 40: (200, 100, 50)}}
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "palette.json"
        save_palette_file(path, test_palette)
        round_trip = load_palette_file(path)

    frame = archive.frame(25)
    baseline = render_icon(frame)
    changed = render_icon(frame, test_palette[25])
    baseline_bytes, changed_bytes = baseline.tobytes(), changed.tobytes()
    changed_pixels = sum(
        baseline_bytes[offset:offset + 4] != changed_bytes[offset:offset + 4]
        for offset in range(0, len(baseline_bytes), 4)
    )
    expected_source_pixels = sum(value in test_palette[25] for value in frame.indices)
    expected_changed_pixels = expected_source_pixels * 4  # 32x32 -> 64x64 nearest-neighbour
    layouts = {
        str(class_id): {
            "source_size": [archive.frame(class_id).width, archive.frame(class_id).height],
            "layout": archive.frame(class_id).layout_name,
        }
        for class_id in (25, 174, 211, 212, 217, 218)
    }
    index_map_alignment = {}
    for class_id in (25, 174, 211, 212, 217, 218):
        icon_bytes = render_icon(archive.frame(class_id)).tobytes()
        index_bytes = render_index_map(archive.frame(class_id)).tobytes()
        aligned = all(
            icon_bytes[offset * 4:offset * 4 + 4] == bytes(existing_rgba(class_id, index))
            for offset, index in enumerate(index_bytes)
        )
        index_map_alignment[str(class_id)] = aligned
    copy_source = {3: (1, 2, 3), 40: (4, 5, 6), 99: (7, 8, 9)}
    copy_target = {7: (10, 11, 12), 40: (13, 14, 15)}
    merged, merge_applied, merge_skipped = copy_palette_overrides(copy_source, copy_target, {3, 7, 40}, "merge")
    replaced, replace_applied, replace_skipped = copy_palette_overrides(copy_source, copy_target, {3, 7, 40}, "replace")
    selected, selected_applied, selected_skipped = copy_palette_overrides(copy_source, copy_target, {3, 7, 40}, "merge", 3)
    palette_copy_logic = {
        "merge_ok": merged == {3: (1, 2, 3), 7: (10, 11, 12), 40: (4, 5, 6)} and (merge_applied, merge_skipped) == (2, 1),
        "replace_ok": replaced == {3: (1, 2, 3), 40: (4, 5, 6)} and (replace_applied, replace_skipped) == (2, 1),
        "selected_index_ok": selected == {3: (1, 2, 3), 7: (10, 11, 12), 40: (13, 14, 15)} and (selected_applied, selected_skipped) == (1, 0),
    }
    all_output_valid = all(render_icon(archive.frame(i)).mode == "RGBA" and render_icon(archive.frame(i)).size == (64, 64) for i in range(len(archive)))
    report = {
        "class_count": len(archive),
        "fallback_pixel_mismatches": mismatches,
        "json_round_trip_ok": round_trip == test_palette,
        "single_override_changed_pixels": changed_pixels,
        "single_override_expected_pixels": expected_changed_pixels,
        "single_override_scope_ok": changed_pixels == expected_changed_pixels,
        "all_outputs_rgba_64x64": all_output_valid,
        "layout_samples": layouts,
        "index_map_alignment": index_map_alignment,
        "palette_copy_logic": palette_copy_logic,
    }
    output = ROOT / "docs/fq4/analysis/039/verification.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if mismatches or not report["json_round_trip_ok"] or not report["single_override_scope_ok"] or not all_output_valid or not all(index_map_alignment.values()) or not all(palette_copy_logic.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
