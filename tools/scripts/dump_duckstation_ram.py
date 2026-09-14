#!/usr/bin/env python3
"""Dump PS1 RAM through DuckStation's local GDB server."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

from gdb_runtime_probe import GDB


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2345)
    parser.add_argument("--base", type=lambda value: int(value, 0), default=0x80000000)
    parser.add_argument("--size", type=lambda value: int(value, 0), default=0x200000)
    parser.add_argument("--chunk", type=lambda value: int(value, 0), default=0x1000)
    parser.add_argument("--retries", type=int, default=40)
    args = parser.parse_args()
    error: Exception | None = None
    for _ in range(args.retries):
        try:
            gdb = GDB(args.host, args.port)
            break
        except OSError as exc:
            error = exc
            time.sleep(0.25)
    else:
        raise RuntimeError(f"GDB server connection failed: {error}")
    gdb.cmd("qSupported")
    gdb.cmd("?")
    image = bytearray()
    for offset in range(0, args.size, args.chunk):
        length = min(args.chunk, args.size - offset)
        reply = gdb.cmd(f"m{args.base + offset:x},{length:x}")
        if reply.startswith("E"):
            raise RuntimeError(f"memory read failed at {args.base + offset:#x}: {reply}")
        image.extend(bytes.fromhex(reply))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(image)
    print(json.dumps({
        "output": str(args.output),
        "base": hex(args.base),
        "size": len(image),
        "sha256": hashlib.sha256(image).hexdigest(),
    }, indent=2))


if __name__ == "__main__":
    main()
