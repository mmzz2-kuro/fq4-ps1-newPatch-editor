#!/usr/bin/env python3
"""FQ4 class palette editor."""
from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

from PIL import ImageTk


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


ROOT = app_root()
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(ROOT / "tools" / "scripts"))

from fq4_class_sprite import (  # noqa: E402
    SpriteArchive, copy_palette_overrides, existing_rgba, format_hex_color, load_palette_file,
    parse_hex_color, render_icon, render_index_icon, render_index_map,
    save_palette_file,
)


def resource_path(relative: str) -> Path:
    bundle = Path(getattr(sys, "_MEIPASS", ROOT))
    candidate = bundle / relative
    if candidate.exists():
        return candidate
    return ROOT / relative


MANIFEST = resource_path("data/original-files.json") if getattr(sys, "frozen", False) else ROOT / "docs/fq4/analysis/001/original-files.json"
NAMES = resource_path("data/class_names.json") if getattr(sys, "frozen", False) else ROOT / "tools/FQ4SaveEditor/class_names.json"
DEFAULT_DISC = ROOT / "original/First Queen IV - Varcia Senki (Japan).bin"
DEFAULT_PALETTE = ROOT / "tools/FQ4PaletteEditor/class_palettes.json" if not getattr(sys, "frozen", False) else ROOT / "class_palettes.json"
DEFAULT_OUTPUT = ROOT / "work/fq4/039/output"


class PaletteEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FQ4 캐릭터 팔레트 편집기")
        self.geometry("1050x760")
        self.minsize(900, 650)
        self.archive = None
        self.palettes = {}
        self.palette_path = DEFAULT_PALETTE
        self.class_id = None
        self.index_id = None
        self.preview_photo = None
        self.index_photo = None
        self.current_index_map = None
        self.last_copy_snapshot = None
        self.disc_var = tk.StringVar(value=str(DEFAULT_DISC) if DEFAULT_DISC.exists() else "")
        self.palette_var = tk.StringVar(value=str(DEFAULT_PALETTE))
        self.hex_var = tk.StringVar()
        self.rgb_vars = [tk.IntVar(value=0) for _ in range(3)]
        self.status_var = tk.StringVar(value="BIN 파일을 열어 주세요.")
        self._build_ui()
        if DEFAULT_PALETTE.exists():
            self._load_palette(DEFAULT_PALETTE, quiet=True)
        if DEFAULT_DISC.exists():
            self.after(100, self.open_disc)

    def _build_ui(self):
        file_frame = ttk.LabelFrame(self, text="입력과 설정", padding=8)
        file_frame.pack(fill="x", padx=10, pady=(10, 5))
        ttk.Label(file_frame, text="원본 BIN").grid(row=0, column=0, sticky="w")
        ttk.Entry(file_frame, textvariable=self.disc_var).grid(row=0, column=1, sticky="ew", padx=6)
        ttk.Button(file_frame, text="찾기", command=self.choose_disc).grid(row=0, column=2)
        ttk.Button(file_frame, text="열기", command=self.open_disc).grid(row=0, column=3, padx=(5, 0))
        ttk.Label(file_frame, text="팔레트 JSON").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(file_frame, textvariable=self.palette_var).grid(row=1, column=1, sticky="ew", padx=6, pady=(6, 0))
        ttk.Button(file_frame, text="불러오기", command=self.choose_palette).grid(row=1, column=2, pady=(6, 0))
        ttk.Button(file_frame, text="저장", command=self.save_palettes).grid(row=1, column=3, padx=(5, 0), pady=(6, 0))
        file_frame.columnconfigure(1, weight=1)

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=10, pady=5)
        left = ttk.Frame(body, padding=4)
        center = ttk.Frame(body, padding=4)
        right = ttk.Frame(body, padding=4)
        body.add(left, weight=2); body.add(center, weight=2); body.add(right, weight=3)

        ttk.Label(left, text="클래스").pack(anchor="w")
        self.class_tree = ttk.Treeview(left, columns=("id", "name"), show="headings", selectmode="browse")
        self.class_tree.heading("id", text="번호"); self.class_tree.column("id", width=55, anchor="e", stretch=False)
        self.class_tree.heading("name", text="이름"); self.class_tree.column("name", width=210)
        class_scroll = ttk.Scrollbar(left, orient="vertical", command=self.class_tree.yview)
        self.class_tree.configure(yscrollcommand=class_scroll.set)
        self.class_tree.pack(side="left", fill="both", expand=True); class_scroll.pack(side="right", fill="y")
        self.class_tree.bind("<<TreeviewSelect>>", self.select_class)

        ttk.Label(center, text="캐릭터 이미지").pack(anchor="w")
        preview_box = ttk.Frame(center, relief="sunken", padding=5)
        preview_box.pack(fill="x", pady=(4, 8))
        self.preview_label = ttk.Label(preview_box, anchor="center")
        self.preview_label.pack(fill="both", expand=True)
        ttk.Label(center, text="팔레트 레이어 인덱스").pack(anchor="w")
        index_box = ttk.Frame(center, relief="sunken", padding=5)
        index_box.pack(fill="x", pady=(4, 4))
        self.index_label = ttk.Label(index_box, anchor="center", cursor="crosshair")
        self.index_label.pack(fill="both", expand=True)
        self.index_label.bind("<Motion>", self.inspect_index_pixel)
        self.index_label.bind("<Leave>", self.leave_index_pixel)
        self.index_label.bind("<Button-1>", self.click_index_pixel)
        self.pixel_info_label = ttk.Label(center, text="인덱스 이미지에 마우스를 올리면 픽셀 정보를 표시합니다.", wraplength=260)
        self.pixel_info_label.pack(fill="x", pady=(2, 5))
        self.info_label = ttk.Label(center, text="", wraplength=260)
        self.info_label.pack(fill="x", pady=8)
        ttk.Button(center, text="선택 클래스 PNG 출력", command=self.export_one).pack(fill="x", pady=2)
        ttk.Button(center, text="전체 클래스 PNG 출력", command=self.export_all).pack(fill="x", pady=2)

        ttk.Label(right, text="사용 팔레트 인덱스").pack(anchor="w")
        self.palette_tree = ttk.Treeview(right, columns=("index", "color", "source"), show="headings", height=14, selectmode="browse")
        for col, title, width in (("index", "인덱스", 65), ("color", "현재 색상", 105), ("source", "출처", 95)):
            self.palette_tree.heading(col, text=title); self.palette_tree.column(col, width=width, anchor="center")
        self.palette_tree.pack(fill="both", expand=True, pady=(4, 8))
        self.palette_tree.bind("<<TreeviewSelect>>", self.select_index)

        edit = ttk.LabelFrame(right, text="선택 인덱스 색상", padding=8)
        edit.pack(fill="x")
        self.swatch = tk.Canvas(edit, width=48, height=30, bd=1, relief="sunken")
        self.swatch.grid(row=0, column=0, rowspan=2, padx=(0, 8))
        ttk.Label(edit, text="HEX").grid(row=0, column=1)
        self.hex_entry = ttk.Entry(edit, textvariable=self.hex_var, width=10)
        self.hex_entry.grid(row=0, column=2, padx=4)
        self.hex_entry.bind("<FocusOut>", self.sync_rgb_from_hex)
        ttk.Button(edit, text="색상 선택", command=self.pick_color).grid(row=0, column=3)
        for column, (label, variable) in enumerate(zip("RGB", self.rgb_vars), 1):
            ttk.Label(edit, text=label).grid(row=1, column=column * 2 - 1, pady=(6, 0))
            spin = ttk.Spinbox(edit, from_=0, to=255, textvariable=variable, width=4, command=self.sync_hex_from_rgb)
            spin.grid(row=1, column=column * 2, pady=(6, 0), padx=(2, 5))
            spin.bind("<FocusOut>", self.sync_hex_from_rgb)
        controls = ttk.Frame(right)
        controls.pack(fill="x", pady=6)
        ttk.Button(controls, text="사용자 색상 적용", command=self.apply_color).pack(side="left", fill="x", expand=True)
        ttk.Button(controls, text="기존 색상으로 복원", command=self.remove_color).pack(side="left", fill="x", expand=True, padx=(5, 0))
        copy_controls = ttk.Frame(right)
        copy_controls.pack(fill="x", pady=(0, 6))
        ttk.Button(copy_controls, text="다른 클래스에 적용", command=self.open_copy_dialog).pack(side="left", fill="x", expand=True)
        self.undo_copy_button = ttk.Button(copy_controls, text="마지막 복사 취소", command=self.undo_last_copy, state="disabled")
        self.undo_copy_button.pack(side="left", fill="x", expand=True, padx=(5, 0))
        ttk.Label(right, text="입력하지 않은 인덱스는 기존 추출기의 색상을 사용합니다.", wraplength=350).pack(anchor="w")

        ttk.Label(self, textvariable=self.status_var, relief="sunken", anchor="w", padding=4).pack(fill="x", side="bottom")

    def choose_disc(self):
        path = filedialog.askopenfilename(title="FQ4 원본 BIN 선택", filetypes=[("PlayStation BIN", "*.bin"), ("모든 파일", "*.*")])
        if path:
            self.disc_var.set(path); self.open_disc()

    def open_disc(self):
        try:
            self.archive = SpriteArchive(Path(self.disc_var.get()), MANIFEST, NAMES)
            for item in self.class_tree.get_children(): self.class_tree.delete(item)
            for class_id, name in enumerate(self.archive.names):
                self.class_tree.insert("", "end", iid=str(class_id), values=(f"{class_id:03}", name))
            self.status_var.set(f"클래스 {len(self.archive)}개를 열었습니다.")
            self.class_tree.selection_set("0"); self.class_tree.see("0"); self.select_class()
        except Exception as exc:
            messagebox.showerror("BIN 열기 실패", str(exc))

    def choose_palette(self):
        path = filedialog.askopenfilename(title="팔레트 JSON 불러오기", filetypes=[("JSON", "*.json"), ("모든 파일", "*.*")])
        if path: self._load_palette(Path(path))

    def _load_palette(self, path: Path, quiet=False):
        try:
            self.palettes = load_palette_file(path)
            self.palette_path = path; self.palette_var.set(str(path))
            if self.class_id is not None: self.populate_palette(); self.refresh_preview()
            self.status_var.set(f"팔레트 설정을 불러왔습니다: {path}")
        except Exception as exc:
            if not quiet: messagebox.showerror("팔레트 불러오기 실패", str(exc))

    def save_palettes(self):
        try:
            path = Path(self.palette_var.get().strip())
            if not path.name:
                chosen = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
                if not chosen: return
                path = Path(chosen); self.palette_var.set(str(path))
            save_palette_file(path, self.palettes); self.palette_path = path
            self.status_var.set(f"저장했습니다: {path}")
        except Exception as exc: messagebox.showerror("저장 실패", str(exc))

    def select_class(self, _event=None):
        selected = self.class_tree.selection()
        if not selected or not self.archive: return
        self.class_id = int(selected[0]); frame = self.archive.frame(self.class_id)
        self.info_label.configure(text=f"{self.class_id:03} {frame.name}\n배치: {frame.layout_name}\n원본 프레임: {frame.width}×{frame.height} / 출력: 64×64")
        self.populate_palette(); self.refresh_preview()

    def populate_palette(self):
        if self.class_id is None or not self.archive: return
        for item in self.palette_tree.get_children(): self.palette_tree.delete(item)
        custom = self.palettes.get(self.class_id, {})
        for index in self.archive.frame(self.class_id).used_indices:
            if index == 0:
                color, source = "투명", "고정"
            elif index in custom:
                color, source = format_hex_color(custom[index]), "사용자"
            else:
                color, source = format_hex_color(existing_rgba(self.class_id, index)[:3]), "기존"
            self.palette_tree.insert("", "end", iid=str(index), values=(index, color, source))
        choices = [x for x in self.palette_tree.get_children() if x != "0"]
        if choices: self.palette_tree.selection_set(choices[0]); self.select_index()

    def select_index(self, _event=None):
        selected = self.palette_tree.selection()
        if not selected or self.class_id is None: return
        self.index_id = int(selected[0])
        if self.index_id == 0:
            rgb = (0, 0, 0)
        else:
            rgb = self.palettes.get(self.class_id, {}).get(self.index_id, existing_rgba(self.class_id, self.index_id)[:3])
        self._set_color_fields(rgb)
        self.refresh_preview()

    def _set_color_fields(self, rgb):
        self.hex_var.set(format_hex_color(tuple(rgb)))
        for variable, value in zip(self.rgb_vars, rgb): variable.set(value)
        self.swatch.delete("all"); self.swatch.create_rectangle(0, 0, 50, 32, fill=self.hex_var.get(), outline="")

    def pick_color(self):
        if self.index_id in (None, 0): return
        chosen = colorchooser.askcolor(color=self.hex_var.get(), title=f"팔레트 인덱스 {self.index_id}")
        if chosen[0]: self._set_color_fields(tuple(round(value) for value in chosen[0]))

    def sync_hex_from_rgb(self, _event=None):
        try:
            rgb = tuple(variable.get() for variable in self.rgb_vars)
            if any(value < 0 or value > 255 for value in rgb): return
            self.hex_var.set(format_hex_color(rgb))
            self.swatch.delete("all"); self.swatch.create_rectangle(0, 0, 50, 32, fill=self.hex_var.get(), outline="")
        except (tk.TclError, ValueError):
            pass

    def sync_rgb_from_hex(self, _event=None):
        try:
            self._set_color_fields(parse_hex_color(self.hex_var.get()))
        except ValueError:
            pass

    def apply_color(self):
        if self.class_id is None or self.index_id in (None, 0): return
        try:
            rgb_values = tuple(variable.get() for variable in self.rgb_vars)
            if any(value < 0 or value > 255 for value in rgb_values): raise ValueError("RGB 값은 0~255여야 합니다.")
            rgb = rgb_values
            self.palettes.setdefault(self.class_id, {})[self.index_id] = rgb
            self._set_color_fields(rgb); self.populate_palette(); self.palette_tree.selection_set(str(self.index_id)); self.refresh_preview()
            self.status_var.set("사용자 색상을 메모리에 적용했습니다. JSON 저장 버튼으로 보존할 수 있습니다.")
        except Exception as exc: messagebox.showerror("색상 입력 오류", str(exc))

    def remove_color(self):
        if self.class_id is None or self.index_id in (None, 0): return
        self.palettes.get(self.class_id, {}).pop(self.index_id, None)
        if not self.palettes.get(self.class_id): self.palettes.pop(self.class_id, None)
        current = self.index_id; self.populate_palette(); self.palette_tree.selection_set(str(current)); self.select_index(); self.refresh_preview()

    def open_copy_dialog(self):
        if self.class_id is None or not self.archive: return
        source = self.palettes.get(self.class_id, {})
        if not source:
            messagebox.showinfo("복사할 색상 없음", "현재 클래스에 사용자 지정 색상이 없습니다.")
            return
        window = tk.Toplevel(self)
        window.title("사용자 팔레트 다른 클래스에 적용")
        window.geometry("650x600")
        window.transient(self); window.grab_set()
        search_var = tk.StringVar()
        scope_var = tk.StringVar(value="all")
        mode_var = tk.StringVar(value="merge")
        ttk.Label(window, text=f"원본: {self.class_id:03} {self.archive.names[self.class_id]}", padding=(10, 10, 10, 4)).pack(anchor="w")
        search_frame = ttk.Frame(window, padding=(10, 4))
        search_frame.pack(fill="x")
        ttk.Label(search_frame, text="검색").pack(side="left")
        search_entry = ttk.Entry(search_frame, textvariable=search_var)
        search_entry.pack(side="left", fill="x", expand=True, padx=(6, 0))
        tree_frame = ttk.Frame(window, padding=(10, 4))
        tree_frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(tree_frame, columns=("id", "name", "custom"), show="headings", selectmode="extended")
        tree.heading("id", text="번호"); tree.column("id", width=60, anchor="e", stretch=False)
        tree.heading("name", text="이름"); tree.column("name", width=360)
        tree.heading("custom", text="사용자 설정"); tree.column("custom", width=90, anchor="center", stretch=False)
        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set); tree.pack(side="left", fill="both", expand=True); scroll.pack(side="right", fill="y")

        def fill_tree(*_args):
            selected = set(tree.selection())
            for item in tree.get_children(): tree.delete(item)
            query = search_var.get().strip().lower()
            for class_id, name in enumerate(self.archive.names):
                if class_id == self.class_id: continue
                if query and query not in str(class_id) and query not in f"{class_id:03}" and query not in name.lower(): continue
                tree.insert("", "end", iid=str(class_id), values=(f"{class_id:03}", name, len(self.palettes.get(class_id, {}))))
            restorable = [item for item in selected if tree.exists(item)]
            if restorable: tree.selection_set(restorable)

        search_var.trace_add("write", fill_tree); fill_tree()
        selection_buttons = ttk.Frame(window, padding=(10, 2))
        selection_buttons.pack(fill="x")
        ttk.Button(selection_buttons, text="현재 목록 전체 선택", command=lambda: tree.selection_set(*tree.get_children())).pack(side="left")
        ttk.Button(selection_buttons, text="선택 해제", command=lambda: tree.selection_remove(*tree.selection())).pack(side="left", padx=5)
        options = ttk.LabelFrame(window, text="적용 옵션", padding=8)
        options.pack(fill="x", padx=10, pady=5)
        ttk.Radiobutton(options, text="현재 클래스의 모든 사용자 색상", variable=scope_var, value="all").grid(row=0, column=0, sticky="w")
        selected_text = f"현재 선택 인덱스만 ({self.index_id})" if self.index_id not in (None, 0) else "현재 선택 인덱스만"
        selected_radio = ttk.Radiobutton(options, text=selected_text, variable=scope_var, value="selected")
        selected_radio.grid(row=1, column=0, sticky="w")
        if self.index_id in (None, 0) or self.index_id not in source: selected_radio.configure(state="disabled")
        ttk.Separator(options, orient="vertical").grid(row=0, column=1, rowspan=2, sticky="ns", padx=15)
        ttk.Radiobutton(options, text="병합: 대상의 다른 사용자 색상 유지", variable=mode_var, value="merge").grid(row=0, column=2, sticky="w")
        ttk.Radiobutton(options, text="교체: 대상의 사용자 색상을 먼저 제거", variable=mode_var, value="replace").grid(row=1, column=2, sticky="w")

        def apply_copy():
            target_ids = [int(item) for item in tree.selection()]
            if not target_ids:
                messagebox.showinfo("대상 선택", "적용할 클래스를 하나 이상 선택해 주세요.", parent=window); return
            selected_index = self.index_id if scope_var.get() == "selected" else None
            calculations = {}
            applied = skipped = 0
            for target_id in target_ids:
                result, count, missed = copy_palette_overrides(
                    source, self.palettes.get(target_id, {}),
                    set(self.archive.frame(target_id).used_indices), mode_var.get(), selected_index,
                )
                calculations[target_id] = result; applied += count; skipped += missed
            summary = f"대상 클래스: {len(target_ids)}개\n적용될 색상: {applied}개\n미사용으로 건너뜀: {skipped}개\n\n계속하시겠습니까?"
            if not messagebox.askyesno("팔레트 적용 확인", summary, parent=window): return
            self.last_copy_snapshot = {target_id: deepcopy(self.palettes.get(target_id)) for target_id in target_ids}
            for target_id, values in calculations.items():
                if values: self.palettes[target_id] = values
                else: self.palettes.pop(target_id, None)
            self.undo_copy_button.configure(state="normal")
            self.status_var.set(f"{len(target_ids)}개 클래스에 사용자 색상 {applied}개를 적용했습니다. 저장 전 상태입니다.")
            window.destroy()
            messagebox.showinfo("적용 완료", f"클래스 {len(target_ids)}개\n적용 {applied}개\n건너뜀 {skipped}개")

        ttk.Button(window, text="선택 클래스에 적용", command=apply_copy).pack(fill="x", padx=10, pady=(4, 10))
        search_entry.focus_set()

    def undo_last_copy(self):
        if not self.last_copy_snapshot: return
        count = len(self.last_copy_snapshot)
        for class_id, previous in self.last_copy_snapshot.items():
            if previous is None: self.palettes.pop(class_id, None)
            else: self.palettes[class_id] = previous
        self.last_copy_snapshot = None; self.undo_copy_button.configure(state="disabled")
        if self.class_id is not None: self.populate_palette(); self.refresh_preview()
        self.status_var.set(f"마지막 팔레트 복사 작업({count}개 클래스)을 취소했습니다.")

    def refresh_preview(self):
        if self.class_id is None or not self.archive: return
        frame = self.archive.frame(self.class_id)
        image = render_icon(frame, self.palettes.get(self.class_id)).resize((192, 192), resample=0)
        index_image = render_index_icon(frame, self.index_id).resize((192, 192), resample=0)
        self.current_index_map = render_index_map(frame)
        self.preview_photo = ImageTk.PhotoImage(image)
        self.index_photo = ImageTk.PhotoImage(index_image)
        self.preview_label.configure(image=self.preview_photo)
        self.index_label.configure(image=self.index_photo)

    def _event_pixel(self, event):
        if self.current_index_map is None: return None
        width, height = self.index_label.winfo_width(), self.index_label.winfo_height()
        image_size = 192
        left, top = max(0, (width - image_size) // 2), max(0, (height - image_size) // 2)
        if not (left <= event.x < left + image_size and top <= event.y < top + image_size): return None
        x = min(63, (event.x - left) * 64 // image_size)
        y = min(63, (event.y - top) * 64 // image_size)
        return x, y, int(self.current_index_map.getpixel((x, y)))

    def _index_description(self, x, y, index):
        if index == 0:
            return f"좌표 ({x}, {y}) · 인덱스 0 · 투명 · 고정"
        custom = self.palettes.get(self.class_id, {}) if self.class_id is not None else {}
        if index in custom:
            rgb, source = custom[index], "사용자"
        else:
            rgb, source = existing_rgba(self.class_id, index)[:3], "기존"
        return f"좌표 ({x}, {y}) · 인덱스 {index} · {format_hex_color(rgb)} · {source}"

    def inspect_index_pixel(self, event):
        pixel = self._event_pixel(event)
        if pixel: self.pixel_info_label.configure(text=self._index_description(*pixel))

    def leave_index_pixel(self, _event=None):
        self.pixel_info_label.configure(text="인덱스 이미지에 마우스를 올리면 픽셀 정보를 표시합니다.")

    def click_index_pixel(self, event):
        pixel = self._event_pixel(event)
        if not pixel: return
        _x, _y, index = pixel
        item = str(index)
        if self.palette_tree.exists(item):
            self.palette_tree.selection_set(item); self.palette_tree.see(item); self.select_index()

    def export_one(self):
        if self.class_id is None or not self.archive: return
        path = filedialog.asksaveasfilename(initialfile=f"class-{self.class_id:03}.png", defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not path: return
        render_icon(self.archive.frame(self.class_id), self.palettes.get(self.class_id)).save(path)
        self.status_var.set(f"출력했습니다: {path}")

    def export_all(self):
        if not self.archive: return
        folder = filedialog.askdirectory(title="전체 클래스 PNG 출력 폴더", initialdir=str(DEFAULT_OUTPUT))
        if not folder: return
        output = Path(folder); output.mkdir(parents=True, exist_ok=True)
        try:
            for class_id in range(len(self.archive)):
                render_icon(self.archive.frame(class_id), self.palettes.get(class_id)).save(output / f"class-{class_id:03}.png")
            self.status_var.set(f"클래스 {len(self.archive)}개를 출력했습니다: {output}")
            messagebox.showinfo("출력 완료", f"클래스 {len(self.archive)}개를 출력했습니다.")
        except Exception as exc: messagebox.showerror("출력 실패", str(exc))


if __name__ == "__main__":
    PaletteEditor().mainloop()
