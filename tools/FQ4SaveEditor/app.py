#!/usr/bin/env python3
"""First Queen IV PS1 memory-card editor GUI."""
from __future__ import annotations

import json
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

HERE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
SCRIPTS = HERE / "scripts" if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from fq4_memcard import MemoryCard, Character, SaveFormatError, GOLD_MAX, ITEM_QUANTITY_MAX  # noqa: E402
import preset_store  # noqa: E402

CHARACTER_NAMES = json.loads((HERE / "character_names.json").read_text(encoding="utf-8"))
CLASS_NAMES = json.loads((HERE / "class_names.json").read_text(encoding="utf-8"))
CLASS_CATALOG = json.loads((HERE / "class_catalog.json").read_text(encoding="utf-8"))


def parse_number(text: str, name: str) -> int:
    value = text.strip()
    if not value:
        raise ValueError(f"{name} 값을 입력하세요.")
    return int(value, 0)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("퍼스트퀸4 PS1 세이브 에디터")
        self.geometry("1120x820")
        self.minsize(960, 720)
        self.card = None
        self.input_path = None
        self.rows = {}
        self.current = None
        self.presets = preset_store.load()
        self.images = {}
        self.item_rows = {}
        self._build()

    def _build(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")
        ttk.Button(top, text="메모리카드 열기", command=self.open_card).pack(side="left")
        ttk.Label(top, text="세이브 슬롯:").pack(side="left", padx=(18, 5))
        self.slot = ttk.Combobox(top, state="readonly", width=25)
        self.slot.pack(side="left")
        self.slot.bind("<<ComboboxSelected>>", lambda e: self.load_slot())
        ttk.Button(top, text="다른 이름으로 저장", command=self.save_as).pack(side="right")
        ttk.Button(top, text="현재 파일 저장", command=self.save_current).pack(side="right", padx=(0, 6))

        self.path_label = ttk.Label(self, text=".mcd 또는 .srm 메모리카드 파일을 여세요.", padding=(10, 0))
        self.path_label.pack(fill="x")

        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=10, pady=10)
        left = ttk.Frame(body)
        right = ttk.Frame(body, padding=12)
        body.add(left, weight=3)
        body.add(right, weight=2)

        cols = ("index", "name", "class", "level", "hp", "hr", "at", "ar", "df", "dr")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", selectmode="extended")
        heads = ("번호", "NAME", "CLASS", "LV", "HP", "HR", "AT", "AR", "DF", "DR")
        widths = (55, 135, 130, 45, 65, 45, 45, 45, 45, 45)
        for c, h, w in zip(cols, heads, widths):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=w, anchor="center")
        sy = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sy.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sy.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self.select_row)

        row = 0
        ttk.Label(right, text="캐릭터 편집", font=("맑은 고딕", 13, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 14))
        row += 1
        self.vars = {k: tk.StringVar() for k in ("index", "name", "ft", "level", "hp", "hr", "at", "ar", "df", "dr")}
        self.class_name = tk.StringVar()
        ttk.Label(right, text="레코드 번호").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Label(right, textvariable=self.vars["index"]).grid(row=row, column=1, sticky="ew")
        row += 1
        ttk.Label(right, text="이름").grid(row=row, column=0, sticky="w", pady=4)
        ttk.Label(right, textvariable=self.vars["name"]).grid(row=row, column=1, sticky="ew")
        row += 1
        ttk.Label(right, text="CLASS").grid(row=row, column=0, sticky="w", pady=4)
        self.class_box = ttk.Combobox(right, textvariable=self.class_name, state="readonly", values=[f"{i:03d}  {CLASS_NAMES[i]}" for i in range(len(CLASS_NAMES))], width=24)
        self.class_box.grid(row=row, column=1, sticky="ew")
        self.class_box.bind("<<ComboboxSelected>>", lambda e: self.update_class_preview())
        row += 1
        self.class_preview = ttk.Label(right, text="캐릭터를 선택하면 CLASS 이미지가 표시됩니다.", anchor="center", padding=5)
        self.class_preview.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(2, 5))
        row += 1
        ttk.Button(right, text="이미지 목록에서 CLASS 선택", command=self.class_picker).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(2, 8))
        row += 1
        for key, label, low, limit in (("level", "LV", 0, 255), ("hp", "HP", 1, 999), ("hr", "HR", 1, 16), ("at", "AT", 1, 99), ("ar", "AR", 1, 99), ("df", "DF", 1, 99), ("dr", "DR", 1, 99)):
            ttk.Label(right, text=label).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Spinbox(right, textvariable=self.vars[key], from_=low, to=limit, width=12).grid(row=row, column=1, sticky="ew")
            row += 1
        ttk.Button(right, text="선택 캐릭터에 적용", command=self.apply).grid(row=row, column=0, columnspan=2, sticky="ew", pady=(15, 8))
        row += 1
        ttk.Label(right, text="CLASS와 LV·HP·HR·AT·AR·DF·DR을 편집합니다.\nFT는 화면에 표시하지 않고 기존 값을 유지합니다.\n저장 시 게임 체크섬 8개를 자동 계산합니다.", foreground="#555").grid(row=row, column=0, columnspan=2, sticky="w", pady=8)
        row += 1

        preset_frame = ttk.LabelFrame(right, text="프리셋", padding=8)
        preset_frame.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        self.preset_box = ttk.Combobox(preset_frame, state="readonly")
        self.preset_box.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 7))
        self.preset_box.bind("<<ComboboxSelected>>", lambda e: self.update_preset_details())
        ttk.Button(preset_frame, text="적용", command=self.apply_preset).grid(row=1, column=0, sticky="ew", padx=(0, 3))
        ttk.Button(preset_frame, text="현재 값 저장", command=self.save_preset).grid(row=1, column=1, sticky="ew", padx=3)
        ttk.Button(preset_frame, text="삭제", command=self.delete_preset).grid(row=1, column=2, sticky="ew", padx=(3, 0))
        self.preset_details = tk.StringVar()
        ttk.Label(preset_frame, textvariable=self.preset_details, relief="sunken", anchor="nw", justify="left", padding=7).grid(row=2, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        for col in range(3):
            preset_frame.columnconfigure(col, weight=1)
        self.refresh_presets()
        row += 1

        economy = ttk.LabelFrame(right, text="자금 / 보유 아이템", padding=8)
        economy.grid(row=row, column=0, columnspan=2, sticky="nsew", pady=(8, 0))
        self.gold_var = tk.StringVar()
        ttk.Label(economy, text="자금").grid(row=0, column=0, sticky="w")
        ttk.Spinbox(economy, textvariable=self.gold_var, from_=0, to=GOLD_MAX, width=12).grid(row=0, column=1, sticky="ew", padx=4)
        ttk.Button(economy, text="자금 적용", command=self.apply_gold).grid(row=0, column=2, sticky="ew")
        ttk.Label(economy, text="게임 내 표시 자금은 입력값 × 10으로 반영됩니다.", foreground="#555").grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))
        item_cols = ("slot", "id", "qty")
        self.item_tree = ttk.Treeview(economy, columns=item_cols, show="headings", height=7, selectmode="browse")
        for c, h, w in (("slot", "칸", 45), ("id", "아이템 ID", 90), ("qty", "수량", 55)):
            self.item_tree.heading(c, text=h)
            self.item_tree.column(c, width=w, anchor="center")
        self.item_tree.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=(8, 4))
        self.item_tree.bind("<<TreeviewSelect>>", self.select_item)
        self.item_id_var = tk.StringVar()
        self.item_qty_var = tk.StringVar(value="1")
        ttk.Label(economy, text="ID").grid(row=3, column=0, sticky="w")
        ttk.Entry(economy, textvariable=self.item_id_var, width=10).grid(row=3, column=1, sticky="ew", padx=4)
        ttk.Label(economy, text="수량").grid(row=4, column=0, sticky="w")
        ttk.Spinbox(economy, textvariable=self.item_qty_var, from_=0, to=ITEM_QUANTITY_MAX, width=10).grid(row=4, column=1, sticky="ew", padx=4)
        ttk.Button(economy, text="추가/수정", command=self.apply_item).grid(row=3, column=2, rowspan=2, sticky="nsew")
        ttk.Button(economy, text="선택 삭제", command=self.delete_item).grid(row=5, column=0, columnspan=3, sticky="ew", pady=(5, 0))
        ttk.Label(economy, text="ID는 10진수 또는 0x2A 같은 16진수로 입력할 수 있습니다. 없는 아이템은 첫 빈 칸에 추가합니다.", foreground="#555", wraplength=360).grid(row=6, column=0, columnspan=3, sticky="w", pady=(6, 0))
        economy.columnconfigure(1, weight=1)
        economy.rowconfigure(1, weight=1)

        right.columnconfigure(1, weight=1)
        right.rowconfigure(row, weight=1)
        self.status = tk.StringVar(value="대기 중")
        ttk.Label(self, textvariable=self.status, relief="sunken", anchor="w", padding=5).pack(fill="x", side="bottom")

    def selected_slot(self):
        if not self.card:
            return None
        index = self.slot.current()
        if index < 0:
            return None
        return self.card.slots[index]

    def open_card(self):
        p = filedialog.askopenfilename(title="PS1 메모리카드 열기", filetypes=[("PS1 메모리카드", "*.mcd *.srm"), ("MCD 파일", "*.mcd"), ("RetroArch SRM 파일", "*.srm"), ("모든 파일", "*.*")])
        if not p:
            return
        try:
            self.card = MemoryCard.open(p)
        except Exception as e:
            messagebox.showerror("열기 실패", str(e))
            return
        self.input_path = Path(p)
        self.path_label.config(text=str(self.input_path))
        self.slot["values"] = [s.filename for s in self.card.slots]
        self.slot.current(0)
        self.load_slot()
        self.status.set(f"{len(self.card.slots)}개 FQ4 세이브를 확인했습니다.")

    def load_slot(self):
        if not self.card:
            return
        self.rows.clear()
        self.current = None
        for item in self.tree.get_children():
            self.tree.delete(item)
        slot = self.selected_slot()
        for c in slot.characters():
            item = self.tree.insert("", "end", values=(c.index, CHARACTER_NAMES[c.name_id], CLASS_NAMES[c.class_id], c.level, c.hp, c.hr, c.at, c.ar, c.df, c.dr))
            self.rows[item] = c
        self.refresh_economy()
        self.status.set(f"{slot.filename}: 편집 가능한 레코드 {len(self.rows)}개")

    def select_row(self, event=None):
        sel = self.tree.selection()
        if not sel:
            return
        self.current = sel[0]
        c = self.rows[self.current]
        for k in self.vars:
            self.vars[k].set(CHARACTER_NAMES[c.name_id] if k == "name" else str(getattr(c, k)))
        self.class_box.current(c.class_id)
        self.update_class_preview()

    def update_class_preview(self):
        class_id = self.class_box.current()
        if not 0 <= class_id < len(CLASS_CATALOG):
            self.class_preview.configure(image="", text="캐릭터를 선택하면 CLASS 이미지가 표시됩니다.")
            self.class_preview.image = None
            return
        entry = CLASS_CATALOG[class_id]
        image = tk.PhotoImage(file=str(HERE / entry["icon"]))
        self.class_preview.configure(image=image, text=f"{class_id:03d}  {CLASS_NAMES[class_id]}", compound="left")
        self.class_preview.image = image

    def refresh_presets(self):
        self.preset_box["values"] = [p["name"] for p in self.presets]
        if self.presets:
            self.preset_box.current(0)
        else:
            self.preset_box.set("")
        self.update_preset_details()

    def update_preset_details(self):
        i = self.preset_box.current()
        if i < 0 or i >= len(self.presets):
            self.preset_details.set("선택 가능한 프리셋이 없습니다.")
            return
        p = self.presets[i]
        class_text = f"{p['class_id']:03d}  {CLASS_NAMES[p['class_id']]}" if "class_id" in p else "미포함(현재 값 유지)"
        self.preset_details.set(
            f"HR {p['hr']}    HP {p['hp']}    AT {p['at']}    AR {p['ar']}    DF {p['df']}    DR {p['dr']}\n"
            f"CLASS  {class_text}\n"
            f"LV  {p.get('level', '미포함(현재 값 유지)')}"
        )

    def save_preset(self):
        if not self.current:
            return
        win = tk.Toplevel(self)
        win.title("프리셋 저장")
        win.transient(self)
        win.grab_set()
        name = tk.StringVar(value="새 프리셋")
        ttk.Label(win, text="이름").grid(row=0, column=0, padx=10, pady=10)
        ttk.Entry(win, textvariable=name, width=25).grid(row=0, column=1, padx=10)
        optional = {k: tk.BooleanVar(value=False) for k in ("level", "class_id")}
        ttk.Label(win, text="HR·HP·AT·AR·DF·DR은 항상 포함합니다.").grid(row=1, column=0, columnspan=2, padx=10, sticky="w")
        for n, (k, label) in enumerate((("level", "LV"), ("class_id", "CLASS")), 2):
            ttk.Checkbutton(win, text=f"{label} 포함", variable=optional[k]).grid(row=n, column=0, columnspan=2, sticky="w", padx=10)

        def commit():
            c = self.rows[self.current]
            p = {"name": name.get(), **{k: getattr(c, k) for k in ("hr", "hp", "at", "ar", "df", "dr")}}
            for k, v in optional.items():
                if v.get():
                    p[k] = getattr(c, k)
            try:
                p = preset_store.validate(p)
                self.presets = [x for x in self.presets if x["name"] != p["name"]] + [p]
                preset_store.save(self.presets)
            except Exception as e:
                messagebox.showerror("프리셋 오류", str(e), parent=win)
                return
            self.refresh_presets()
            self.preset_box.set(p["name"])
            self.update_preset_details()
            win.destroy()

        ttk.Button(win, text="저장", command=commit).grid(row=5, column=0, columnspan=2, pady=12)

    def delete_preset(self):
        i = self.preset_box.current()
        if i < 0:
            return
        if not messagebox.askyesno("프리셋 삭제", f"'{self.presets[i]['name']}' 프리셋을 삭제할까요?"):
            return
        self.presets.pop(i)
        preset_store.save(self.presets)
        self.refresh_presets()

    def apply_preset(self):
        i = self.preset_box.current()
        sels = self.tree.selection()
        if i < 0 or not sels:
            messagebox.showinfo("선택 필요", "프리셋과 한 명 이상의 캐릭터를 선택하세요.")
            return
        p = self.presets[i]
        if not messagebox.askyesno("프리셋 적용", f"{len(sels)}명에게 '{p['name']}' 프리셋을 적용할까요?"):
            return
        slot = self.selected_slot()
        for item in sels:
            c = self.rows[item]
            values = c.__dict__.copy()
            for k, v in p.items():
                if k != "name":
                    values[k] = v
            c = Character(**values)
            slot.update_character(c)
            self.rows[item] = c
            self.tree.item(item, values=(c.index, CHARACTER_NAMES[c.name_id], CLASS_NAMES[c.class_id], c.level, c.hp, c.hr, c.at, c.ar, c.df, c.dr))
        self.select_row()
        self.status.set(f"{len(sels)}명에게 프리셋을 적용했습니다. 파일 저장 전 상태입니다.")

    def class_picker(self):
        win = tk.Toplevel(self)
        win.title("CLASS 이미지 목록")
        win.geometry("700x600")
        win.transient(self)
        search = tk.StringVar()
        ttk.Entry(win, textvariable=search).pack(fill="x", padx=10, pady=8)
        canvas = tk.Canvas(win)
        bar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        frame = ttk.Frame(canvas)
        canvas.configure(yscrollcommand=bar.set)
        bar.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)
        canvas.create_window((0, 0), window=frame, anchor="nw")
        frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        buttons = []

        def choose(i):
            self.class_box.current(i)
            self.update_class_preview()
            win.destroy()

        for n, c in enumerate(CLASS_CATALOG):
            path = HERE / c["icon"]
            img = tk.PhotoImage(file=str(path))
            self.images[c["id"]] = img
            b = ttk.Button(frame, image=img, text=f"{c['id']:03d}  {c['name']}", compound="left", command=lambda i=c["id"]: choose(i))
            b.grid(row=n // 3, column=n % 3, sticky="ew", padx=4, pady=4)
            buttons.append((b, c))

        def filt(*_):
            q = search.get().lower()
            for b, c in buttons:
                if q in c["name"].lower() or q in str(c["id"]):
                    b.grid()
                else:
                    b.grid_remove()

        search.trace_add("write", filt)

    def apply(self):
        if not self.current:
            messagebox.showinfo("선택 필요", "먼저 캐릭터를 선택하세요.")
            return
        old = self.rows[self.current]
        try:
            c = Character(old.index, old.ft, old.name_id, self.class_box.current(), int(self.vars["level"].get()), int(self.vars["hr"].get()), int(self.vars["hp"].get()), *[int(self.vars[k].get()) for k in ("at", "ar", "df", "dr")])
            self.selected_slot().update_character(c)
        except Exception as e:
            messagebox.showerror("입력 오류", str(e))
            return
        self.rows[self.current] = c
        self.tree.item(self.current, values=(c.index, CHARACTER_NAMES[c.name_id], CLASS_NAMES[c.class_id], c.level, c.hp, c.hr, c.at, c.ar, c.df, c.dr))
        self.status.set(f"레코드 {c.index} 변경을 메모리에 적용했습니다. 파일 저장 전 상태입니다.")

    def refresh_economy(self):
        slot = self.selected_slot()
        for item in self.item_tree.get_children():
            self.item_tree.delete(item)
        self.item_rows.clear()
        if not slot:
            self.gold_var.set("")
            return
        self.gold_var.set(str(slot.gold()))
        for item in slot.items():
            iid = self.item_tree.insert("", "end", values=(item.index, f"0x{item.item_id:02X} ({item.item_id})", item.quantity))
            self.item_rows[iid] = item

    def apply_gold(self):
        slot = self.selected_slot()
        if not slot:
            return
        try:
            value = parse_number(self.gold_var.get(), "자금")
            slot.set_gold(value)
        except Exception as e:
            messagebox.showerror("자금 입력 오류", str(e))
            return
        self.gold_var.set(str(slot.gold()))
        self.status.set(f"자금을 {slot.gold()}으로 변경했습니다. 파일 저장 전 상태입니다.")

    def select_item(self, event=None):
        sel = self.item_tree.selection()
        if not sel:
            return
        item = self.item_rows[sel[0]]
        self.item_id_var.set(f"0x{item.item_id:02X}")
        self.item_qty_var.set(str(item.quantity))

    def apply_item(self):
        slot = self.selected_slot()
        if not slot:
            return
        try:
            item_id = parse_number(self.item_id_var.get(), "아이템 ID")
            quantity = parse_number(self.item_qty_var.get(), "수량")
            changed = slot.set_item_quantity(item_id, quantity)
        except Exception as e:
            messagebox.showerror("아이템 입력 오류", str(e))
            return
        self.refresh_economy()
        if changed is None:
            self.status.set(f"아이템 0x{item_id:02X}는 보유하지 않은 상태입니다.")
        elif quantity == 0:
            self.status.set(f"아이템 0x{item_id:02X}를 삭제했습니다. 파일 저장 전 상태입니다.")
        else:
            self.status.set(f"아이템 0x{item_id:02X} 수량을 {quantity}으로 변경했습니다. 파일 저장 전 상태입니다.")

    def delete_item(self):
        slot = self.selected_slot()
        sel = self.item_tree.selection()
        if not slot or not sel:
            messagebox.showinfo("선택 필요", "삭제할 아이템을 선택하세요.")
            return
        item = self.item_rows[sel[0]]
        if not messagebox.askyesno("아이템 삭제", f"아이템 0x{item.item_id:02X}를 삭제할까요?"):
            return
        try:
            slot.clear_item_slot(item.index)
        except Exception as e:
            messagebox.showerror("삭제 실패", str(e))
            return
        self.refresh_economy()
        self.status.set(f"아이템 0x{item.item_id:02X}를 삭제했습니다. 파일 저장 전 상태입니다.")

    def save_as(self):
        if not self.card:
            return
        suffix = self.input_path.suffix.lower() if self.input_path and self.input_path.suffix.lower() in (".mcd", ".srm") else ".mcd"
        initial = (self.input_path.stem + "-edited" + suffix) if self.input_path else "fq4-edited.mcd"
        p = filedialog.asksaveasfilename(title="편집본 저장", defaultextension=suffix, initialfile=initial, filetypes=[("PS1 메모리카드", "*.mcd *.srm"), ("MCD 파일", "*.mcd"), ("RetroArch SRM 파일", "*.srm")])
        if not p:
            return
        if self.input_path and Path(p).resolve() == self.input_path.resolve():
            if not messagebox.askyesno("원본 덮어쓰기", "입력 파일과 같은 경로입니다. 정말 덮어쓰시겠습니까?"):
                return
        try:
            self.card.save_as(p)
        except Exception as e:
            messagebox.showerror("저장 실패", str(e))
            return
        messagebox.showinfo("저장 완료", f"검증된 메모리카드를 저장했습니다.\n{p}")
        self.status.set(f"저장 완료: {p}")

    def save_current(self):
        if not self.card or not self.input_path:
            messagebox.showinfo("저장할 파일 없음", "먼저 메모리카드 파일을 여세요.")
            return
        if not messagebox.askyesno("현재 파일 저장", "정말로 덮어 씌우시겠습니까?"):
            return
        try:
            self.card.save_as(self.input_path)
            self.card = MemoryCard.open(self.input_path)
            self.load_slot()
        except Exception as e:
            messagebox.showerror("저장 실패", str(e))
            return
        messagebox.showinfo("저장 완료", f"현재 파일을 저장하고 검증했습니다.\n{self.input_path}")
        self.status.set(f"현재 파일 저장 완료: {self.input_path}")


if __name__ == "__main__":
    App().mainloop()
