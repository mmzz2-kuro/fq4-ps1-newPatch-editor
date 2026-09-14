#!/usr/bin/env python3
"""Parser and safe writer for First Queen IV PS1 memory-card saves."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import struct
import tempfile

CARD_SIZE = 128 * 1024
BLOCK_SIZE = 0x2000
DIR_ENTRY_SIZE = 0x80
FQ4_PREFIX = b"BISLPS-00604-"
PAYLOAD_SIZE = 0x8000
SAVE_MAGIC = b"SC\x13\x04"
CHECKSUM_OFFSET = 0x7DA6
CHECKSUM_COUNT = 8
CHARACTER_OFFSET = 0x09A6
CHARACTER_STRIDE = 0x20
CHARACTER_COUNT = 640
SPECIES_COUNT = 150


class SaveFormatError(ValueError):
    pass


def xor128(chunk: bytes) -> int:
    value = 0
    for byte in chunk[:127]:
        value ^= byte
    return value


def payload_checksums(payload: bytes) -> bytes:
    if len(payload) != PAYLOAD_SIZE:
        raise SaveFormatError(f"FQ4 payload must be {PAYLOAD_SIZE} bytes")
    work = bytearray(payload)
    work[CHECKSUM_OFFSET:CHECKSUM_OFFSET + CHECKSUM_COUNT] = b"\0" * CHECKSUM_COUNT
    return bytes(_xor(work[i * 0x1000:(i + 1) * 0x1000]) for i in range(8))


def _xor(data: bytes) -> int:
    value = 0
    for byte in data:
        value ^= byte
    return value


def repair_payload_checksums(payload: bytearray) -> None:
    payload[CHECKSUM_OFFSET:CHECKSUM_OFFSET + CHECKSUM_COUNT] = payload_checksums(payload)


@dataclass(frozen=True)
class DirectoryEntry:
    block: int
    status: int
    size: int
    next_block: int | None
    filename: str
    checksum_ok: bool


@dataclass
class Character:
    index: int
    ft: int
    name_id: int
    class_id: int
    level: int
    hr: int
    hp: int
    at: int
    ar: int
    df: int
    dr: int


@dataclass
class FQ4Slot:
    filename: str
    start_block: int
    blocks: list[int]
    payload: bytearray

    def validate(self) -> None:
        if self.payload[:4] != SAVE_MAGIC:
            raise SaveFormatError(f"{self.filename}: unsupported save header")
        expected = payload_checksums(self.payload)
        actual = bytes(self.payload[CHECKSUM_OFFSET:CHECKSUM_OFFSET + CHECKSUM_COUNT])
        if actual != expected:
            raise SaveFormatError(
                f"{self.filename}: internal checksum mismatch "
                f"(stored {actual.hex()}, calculated {expected.hex()})"
            )

    def characters(self, include_empty: bool = False) -> list[Character]:
        result = []
        for index in range(CHARACTER_COUNT):
            off = CHARACTER_OFFSET + index * CHARACTER_STRIDE
            raw = self.payload[off:off + CHARACTER_STRIDE]
            ft, name_id = struct.unpack_from("<HH", raw)
            class_id = raw[12]
            hp = struct.unpack_from("<H", raw, 26)[0]
            if include_empty or (hp > 0 and class_id < SPECIES_COUNT and name_id < CHARACTER_COUNT):
                result.append(Character(index, ft, name_id, class_id, raw[24], raw[25], hp,
                                        raw[28], raw[29], raw[30], raw[31]))
        return result

    def update_character(self, character: Character) -> None:
        if not 0 <= character.index < CHARACTER_COUNT:
            raise SaveFormatError("character index out of range")
        for name, value, limit in (
            ("FT", character.ft, 0xFFFF), ("name ID", character.name_id, CHARACTER_COUNT - 1),
            ("class", character.class_id, SPECIES_COUNT - 1),
            ("LV", character.level, 0xFF),
        ):
            if not 0 <= value <= limit:
                raise SaveFormatError(f"{name} must be between 0 and {limit}")
        for name, value, low, high in (
            ("HR", character.hr, 1, 16), ("HP", character.hp, 1, 999),
            ("AT", character.at, 1, 99), ("AR", character.ar, 1, 99),
            ("DF", character.df, 1, 99), ("DR", character.dr, 1, 99),
        ):
            if not low <= value <= high:
                raise SaveFormatError(f"{name} must be between {low} and {high}")
        off = CHARACTER_OFFSET + character.index * CHARACTER_STRIDE
        struct.pack_into("<HH", self.payload, off, character.ft, character.name_id)
        self.payload[off + 12] = character.class_id
        self.payload[off + 24] = character.level
        self.payload[off + 25] = character.hr
        struct.pack_into("<H", self.payload, off + 26, character.hp)
        self.payload[off + 28:off + 32] = bytes((character.at, character.ar, character.df, character.dr))
        repair_payload_checksums(self.payload)


class MemoryCard:
    def __init__(self, data: bytes):
        if len(data) != CARD_SIZE:
            raise SaveFormatError(f"raw PS1 memory card must be {CARD_SIZE} bytes")
        if data[:2] != b"MC":
            raise SaveFormatError("missing raw PS1 memory-card MC header")
        self.data = bytearray(data)
        self.entries = self._read_entries()
        bad = [e.block for e in self.entries if not e.checksum_ok and e.status != 0xA0]
        if bad:
            raise SaveFormatError(f"directory checksum mismatch in block(s): {bad}")
        self.slots = self._read_fq4_slots()
        if not self.slots:
            raise SaveFormatError("no BISLPS-00604-* saves found")

    @classmethod
    def open(cls, path: str | Path) -> "MemoryCard":
        return cls(Path(path).read_bytes())

    def _read_entries(self) -> list[DirectoryEntry]:
        result = []
        for block in range(1, 16):
            off = 0x80 + (block - 1) * DIR_ENTRY_SIZE
            raw = self.data[off:off + DIR_ENTRY_SIZE]
            nxt = struct.unpack_from("<H", raw, 8)[0]
            filename = bytes(raw[10:127]).split(b"\0", 1)[0].decode("ascii", "replace")
            result.append(DirectoryEntry(
                block, raw[0], struct.unpack_from("<I", raw, 4)[0],
                None if nxt == 0xFFFF else nxt + 1, filename, raw[127] == xor128(raw)
            ))
        return result

    def _read_fq4_slots(self) -> list[FQ4Slot]:
        by_block = {e.block: e for e in self.entries}
        slots = []
        for entry in self.entries:
            if entry.status != 0x51 or not entry.filename.encode("ascii", "replace").startswith(FQ4_PREFIX):
                continue
            chain, current = [], entry.block
            while current is not None:
                if current in chain or current not in by_block:
                    raise SaveFormatError(f"{entry.filename}: broken block chain")
                chain.append(current)
                current = by_block[current].next_block
            if len(chain) != 4:
                raise SaveFormatError(f"{entry.filename}: expected four blocks, got {len(chain)}")
            payload = bytearray().join(self.data[b * BLOCK_SIZE:(b + 1) * BLOCK_SIZE] for b in chain)
            slot = FQ4Slot(entry.filename, entry.block, chain, payload)
            slot.validate()
            slots.append(slot)
        return slots

    def render(self) -> bytes:
        output = bytearray(self.data)
        for slot in self.slots:
            slot.validate()
            for i, block in enumerate(slot.blocks):
                output[block * BLOCK_SIZE:(block + 1) * BLOCK_SIZE] = slot.payload[i * BLOCK_SIZE:(i + 1) * BLOCK_SIZE]
        return bytes(output)

    def save_as(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        rendered = self.render()
        fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(rendered)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, path)
            reread = MemoryCard.open(path)
            if reread.render() != rendered:
                raise SaveFormatError("written card did not verify byte-for-byte")
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
