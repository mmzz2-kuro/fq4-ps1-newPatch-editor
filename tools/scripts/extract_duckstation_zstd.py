#!/usr/bin/env python3
"""Extract concatenated Zstandard frames from a DuckStation save state."""

from __future__ import annotations

import argparse
import ctypes
import json
from pathlib import Path

MAGIC = bytes.fromhex("28b52ffd")
CONTENT_SIZE_ERROR = (1 << 64) - 1
CONTENT_SIZE_UNKNOWN = (1 << 64) - 2


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("state", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--zstd-dll", type=Path, required=True)
    args = parser.parse_args()
    dll = ctypes.CDLL(str(args.zstd_dll.resolve()))
    dll.ZSTD_findFrameCompressedSize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    dll.ZSTD_findFrameCompressedSize.restype = ctypes.c_size_t
    dll.ZSTD_getFrameContentSize.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    dll.ZSTD_getFrameContentSize.restype = ctypes.c_ulonglong
    dll.ZSTD_decompress.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p, ctypes.c_size_t]
    dll.ZSTD_decompress.restype = ctypes.c_size_t
    dll.ZSTD_isError.argtypes = [ctypes.c_size_t]
    dll.ZSTD_isError.restype = ctypes.c_uint
    data = args.state.read_bytes()
    position = data.find(MAGIC)
    if position < 0:
        raise ValueError("Zstandard frame not found")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    index = 0
    while position < len(data) and data[position:position + 4] == MAGIC:
        source = ctypes.create_string_buffer(data[position:])
        compressed_size = dll.ZSTD_findFrameCompressedSize(source, len(data) - position)
        if dll.ZSTD_isError(compressed_size):
            raise ValueError(f"invalid compressed frame at {position:#x}")
        content_size = dll.ZSTD_getFrameContentSize(source, compressed_size)
        if content_size in (CONTENT_SIZE_ERROR, CONTENT_SIZE_UNKNOWN):
            raise ValueError(f"unknown frame content size at {position:#x}")
        output = ctypes.create_string_buffer(content_size)
        written = dll.ZSTD_decompress(output, content_size, source, compressed_size)
        if dll.ZSTD_isError(written) or written != content_size:
            raise ValueError(f"decompression failed at {position:#x}")
        path = args.output_dir / f"frame-{index:02d}.bin"
        path.write_bytes(output.raw[:written])
        frames.append({"index": index, "offset": position, "compressed_size": compressed_size,
                       "content_size": content_size, "output": str(path)})
        position += compressed_size
        index += 1
    print(json.dumps({"state": str(args.state), "frames": frames, "trailing_offset": position,
                      "trailing_size": len(data) - position}, indent=2))


if __name__ == "__main__":
    main()
