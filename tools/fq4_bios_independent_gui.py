#!/usr/bin/env python3
"""FQ4 standard-BIOS Korean ROM builder GUI."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
import shutil
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

FROZEN = bool(getattr(sys, "frozen", False))
ROOT = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parents[1]
DEV_ROOT = None if FROZEN else ROOT
if DEV_ROOT is not None:
    sys.path.insert(0, str(DEV_ROOT / "tools/scripts"))
import build_fq4_bios_independent as engine  # noqa: E402

ENGINE = ROOT / "tools/scripts/build_fq4_bios_independent.py"
DISCOVERY_ROOT = Path.cwd() if FROZEN else ROOT
DEFAULTS = {
    "original": next((DISCOVERY_ROOT / "original").glob("*.bin"), Path()),
    "patch": next(iter(sorted((DISCOVERY_ROOT / "korean-patch").glob("*.xdelta"), reverse=True)), Path()),
    "bios": DISCOVERY_ROOT / "korean-patch/SCPH1001.BIN",
    "xdelta": DISCOVERY_ROOT / "korean-patch/xdelta.exe",
}


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("퍼스트퀸4 일반 BIOS용 ROM 만들기")
        self.geometry("780x650")
        self.minsize(700, 600)
        self.process: subprocess.Popen[str] | None = None
        self.vars = {name: tk.StringVar(value=str(DEFAULTS.get(name, ""))) for name in ("original", "patch", "bios", "xdelta", "output")}
        self.status = tk.StringVar(value="파일을 선택한 뒤 만들기 버튼을 누르세요.")
        self.expand_species_limit = tk.BooleanVar(value=False)
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build_ui(self) -> None:
        root = ttk.Frame(self, padding=18)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="퍼스트퀸4 일반 BIOS용 한글 ROM", font=("맑은 고딕", 16, "bold")).pack(anchor="w")
        ttk.Label(root, text="선택한 한글패치의 구조를 검사한 뒤 일반 BIOS용 한글 글꼴 로더를 적용합니다.").pack(anchor="w", pady=(3, 16))
        form = ttk.Frame(root)
        form.pack(fill="x")
        rows = (("original", "일본판 원본 BIN", "bin"), ("patch", "한글패치 xdelta", "patch"), ("bios", "한글 BIOS", "bios"), ("xdelta", "xdelta.exe", "exe"), ("output", "출력 BIN", "save"))
        self.entries = []
        for row, (name, label, kind) in enumerate(rows):
            ttk.Label(form, text=label, width=18).grid(row=row, column=0, sticky="w", pady=5)
            entry = ttk.Entry(form, textvariable=self.vars[name])
            entry.grid(row=row, column=1, sticky="ew", padx=(0, 8), pady=5)
            self.entries.append(entry)
            ttk.Button(form, text="찾아보기", command=lambda n=name, k=kind: self._browse(n, k)).grid(row=row, column=2, pady=5)
        form.columnconfigure(1, weight=1)
        options = ttk.LabelFrame(root, text="선택 기능", padding=(12, 8))
        options.pack(fill="x", pady=(14, 0))
        self.species_checkbox = ttk.Checkbutton(
            options,
            text="부대 종족 제한을 18종 수준으로 확장 (실험적)",
            variable=self.expand_species_limit,
        )
        self.species_checkbox.pack(anchor="w")
        ttk.Label(
            options,
            text="종족별 그래픽 비용에 따라 실제 허용 수가 달라질 수 있습니다. 기본 동작은 확인됐으며 장시간 플레이 검증이 더 필요합니다.",
            wraplength=720,
        ).pack(anchor="w", pady=(4, 0))
        self.progress = ttk.Progressbar(root, mode="indeterminate")
        self.progress.pack(fill="x", pady=(18, 7))
        ttk.Label(root, textvariable=self.status).pack(anchor="w")
        self.log = tk.Text(root, height=12, wrap="word", state="disabled", font=("Consolas", 9))
        self.log.pack(fill="both", expand=True, pady=(8, 12))
        buttons = ttk.Frame(root)
        buttons.pack(fill="x")
        self.run_button = ttk.Button(buttons, text="일반 BIOS용 ROM 만들기", command=self._start)
        self.run_button.pack(side="right")
        self.cancel_button = ttk.Button(buttons, text="취소", command=self._cancel, state="disabled")
        self.cancel_button.pack(side="right", padx=8)

    def _browse(self, name: str, kind: str) -> None:
        if kind == "save":
            value = filedialog.asksaveasfilename(defaultextension=".bin", filetypes=(("BIN 이미지", "*.bin"), ("모든 파일", "*.*")))
        else:
            filters = {"bin": (("BIN 이미지", "*.bin"),), "patch": (("xdelta 패치", "*.xdelta"),), "bios": (("BIOS BIN", "*.bin"),), "exe": (("실행 파일", "*.exe"),)}[kind]
            value = filedialog.askopenfilename(filetypes=filters + (("모든 파일", "*.*"),))
        if value:
            self.vars[name].set(value)

    def _append(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _start(self) -> None:
        values = {name: value.get().strip() for name, value in self.vars.items()}
        if any(not value for value in values.values()):
            messagebox.showerror("입력 확인", "모든 파일 경로를 선택해 주세요.")
            return
        output = Path(values["output"])
        overwrite = output.exists() or output.with_suffix(".cue").exists()
        if overwrite and not messagebox.askyesno("덮어쓰기", "출력 BIN 또는 CUE가 이미 있습니다. 덮어쓸까요?"):
            return
        if FROZEN:
            command = [sys.executable, "--engine-json"]
        else:
            command = [sys.executable, str(ENGINE)]
        command += ["--original", values["original"], "--patch", values["patch"], "--bios", values["bios"], "--xdelta-exe", values["xdelta"], "--output", values["output"]]
        if overwrite:
            command.append("--overwrite")
        if self.expand_species_limit.get():
            command.append("--expand-party-species-limit")
        self.run_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        for entry in self.entries:
            entry.configure(state="disabled")
        self.species_checkbox.configure(state="disabled")
        self.progress.start(12)
        self.status.set("작업을 시작합니다…")
        self._append("작업 시작")
        threading.Thread(target=self._worker, args=(command, output), daemon=True).start()

    def _worker(self, command: list[str], output: Path) -> None:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", creationflags=flags)
        success = None
        assert self.process.stdout is not None
        for line in self.process.stdout:
            line = line.rstrip()
            try:
                event = json.loads(line)
                message = event.get("message", line)
                if event.get("stage") == "profile":
                    message += (f"\n  프로필: {event['profile']}\n  xdelta SHA-256: {event['patch_sha256']}"
                                f"\n  EXE LBA: {event['exe_lba']} / DUMMY LBA: {event['dummy_lba']}"
                                f"\n  초기화 훅: 0x{event['init_call']:08X} / 글리프 훅: 0x{event['krom_hook']:08X}")
                if event.get("stage") == "complete":
                    success = event
            except json.JSONDecodeError:
                message = line
            self.after(0, self._event, message)
        code = self.process.wait()
        self.process = None
        self.after(0, self._finished, code, success, output)

    def _event(self, message: str) -> None:
        self.status.set(message)
        self._append(message)

    def _finished(self, code: int, success: dict | None, output: Path) -> None:
        self.progress.stop()
        self.run_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        for entry in self.entries:
            entry.configure(state="normal")
        self.species_checkbox.configure(state="normal")
        if code == 0 and success:
            self.status.set("완료")
            messagebox.showinfo("완료", f"일반 BIOS용 ROM을 만들었습니다.\n\n{output}\n프로필: {success['profile']}\n교정 sector: {success['repaired_sectors']}\nSHA-256: {success['sha256']}")
        elif code < 0:
            self.status.set("취소됨")
            self._cleanup_temp(output)
        else:
            self.status.set("실패 — 로그를 확인하세요.")
            self._cleanup_temp(output)
            messagebox.showerror("실패", "ROM을 만들지 못했습니다. 로그에서 입력 파일과 오류 내용을 확인해 주세요.")

    def _cleanup_temp(self, output: Path) -> None:
        for path in (output.with_name(f".{output.name}.fq4-building.bin"), output.with_suffix(".cue").with_name(f".{output.with_suffix('.cue').name}.fq4-building.cue")):
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        report = output.parent / f".{output.stem}.fq4-report"
        try:
            if report.is_dir():
                shutil.rmtree(report)
        except OSError:
            pass

    def _cancel(self) -> None:
        if self.process is not None and messagebox.askyesno("작업 취소", "현재 작업을 취소할까요?"):
            self.process.terminate()
            self._append("취소를 요청했습니다.")

    def _close(self) -> None:
        if self.process is not None:
            messagebox.showinfo("작업 중", "작업을 취소한 뒤 창을 닫아 주세요.")
            return
        self.destroy()


if __name__ == "__main__":
    if "--engine-json" in sys.argv:
        sys.argv.remove("--engine-json")
        engine.main()
    else:
        App().mainloop()
