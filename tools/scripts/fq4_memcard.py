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
SPECIES_COUNT = 220
GOLD_OFFSET = 0x0692
GOLD_MAX = 0xFFFF
ITEM_OFFSET = 0x0492
ITEM_STRIDE = 2
# The observed inventory area ends at 0x0520 in the available PS1 saves:
# (0x0520 - 0x0492) / 2 = 71 entries.
ITEM_CAPACITY = 71
ITEM_QUANTITY_MAX = 99
MAGIC_OFFSET = 0x06DE
MAGIC_END = 0x07F0  # 0x07F0.. contains other save fields.
MAGIC_MAX_PER_CLASS = 5
MAGIC_MAX_ID = 53


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
class InventoryItem:
    index: int
    item_id: int
    quantity: int

    @property
    def empty(self) -> bool:
        return self.item_id == 0 and self.quantity == 0


@dataclass(frozen=True)
class ClassMagic:
    class_id: int
    spell_ids: tuple[int, ...]


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

    def magic_sets(self) -> list[ClassMagic]:
        """Read the save's class-keyed, FF-terminated learned-magic list."""
        result = []
        seen = set()
        pos = MAGIC_OFFSET
        while pos < MAGIC_END:
            class_id = self.payload[pos]
            if class_id == 0xFF:
                return result
            if pos + 2 > MAGIC_END:
                break
            count = self.payload[pos + 1]
            if (class_id >= SPECIES_COUNT or class_id in seen or
                    count > MAGIC_MAX_PER_CLASS or pos + 2 + count >= MAGIC_END):
                break
            spells = tuple(self.payload[pos + 2:pos + 2 + count])
            if any(not 1 <= spell <= MAGIC_MAX_ID for spell in spells) or len(set(spells)) != count:
                break
            result.append(ClassMagic(class_id, spells))
            seen.add(class_id)
            pos += 2 + count
        raise SaveFormatError(f"invalid learned-magic list at payload 0x{pos:04X}")

    def spells_for_class(self, class_id: int) -> tuple[int, ...] | None:
        return next((row.spell_ids for row in self.magic_sets() if row.class_id == class_id), None)

    def set_class_spells(self, class_id: int, spell_ids: list[int] | tuple[int, ...]) -> None:
        rows = self.magic_sets()
        if class_id not in {row.class_id for row in rows}:
            raise SaveFormatError(f"class {class_id} has no learned-magic entry")
        spells = tuple(spell_ids)
        if len(spells) > MAGIC_MAX_PER_CLASS or len(set(spells)) != len(spells):
            raise SaveFormatError("a class may have up to five distinct spells")
        if any(not isinstance(spell, int) or not 1 <= spell <= MAGIC_MAX_ID for spell in spells):
            raise SaveFormatError(f"spell IDs must be 1..{MAGIC_MAX_ID}")
        packed = bytearray()
        for row in rows:
            values = spells if row.class_id == class_id else row.spell_ids
            packed.extend((row.class_id, len(values)))
            packed.extend(values)
        packed.append(0xFF)
        if len(packed) > MAGIC_END - MAGIC_OFFSET:
            raise SaveFormatError("learned-magic list has no remaining space")
        old = self.payload[MAGIC_OFFSET:MAGIC_END]
        old_end = old.find(0xFF)
        # Every sample uses zero padding after the terminator; refuse unknown data.
        if old_end < 0 or any(old[old_end + 1:]):
            raise SaveFormatError("learned-magic padding contains unknown data")
        self.payload[MAGIC_OFFSET:MAGIC_END] = packed + bytes(MAGIC_END - MAGIC_OFFSET - len(packed))
        repair_payload_checksums(self.payload)

    def gold(self) -> int:
        return struct.unpack_from("<H", self.payload, GOLD_OFFSET)[0]

    def set_gold(self, value: int) -> None:
        if not 0 <= value <= GOLD_MAX:
            raise SaveFormatError(f"gold must be between 0 and {GOLD_MAX}")
        struct.pack_into("<H", self.payload, GOLD_OFFSET, value)
        repair_payload_checksums(self.payload)

    def items(self, include_empty: bool = False) -> list[InventoryItem]:
        result = []
        for index in range(ITEM_CAPACITY):
            off = ITEM_OFFSET + index * ITEM_STRIDE
            item = InventoryItem(index, self.payload[off], self.payload[off + 1])
            if include_empty or not item.empty:
                result.append(item)
        return result

    def set_item_quantity(self, item_id: int, quantity: int) -> InventoryItem | None:
        if not 1 <= item_id <= 0xFF:
            raise SaveFormatError("item ID must be between 1 and 255")
        if not 0 <= quantity <= ITEM_QUANTITY_MAX:
            raise SaveFormatError(f"item quantity must be between 0 and {ITEM_QUANTITY_MAX}")

        empty_index = None
        for item in self.items(include_empty=True):
            if item.empty and empty_index is None:
                empty_index = item.index
            if item.item_id == item_id:
                return self._write_item(item.index, 0 if quantity == 0 else item_id, quantity)

        if quantity == 0:
            return None
        if empty_index is None:
            raise SaveFormatError("inventory has no empty slot")
        return self._write_item(empty_index, item_id, quantity)

    def clear_item_slot(self, index: int) -> None:
        self._write_item(index, 0, 0)

    def _write_item(self, index: int, item_id: int, quantity: int) -> InventoryItem:
        if not 0 <= index < ITEM_CAPACITY:
            raise SaveFormatError("inventory slot index out of range")
        if item_id == 0 and quantity != 0:
            raise SaveFormatError("empty item slot must have quantity 0")
        off = ITEM_OFFSET + index * ITEM_STRIDE
        self.payload[off] = item_id
        self.payload[off + 1] = quantity
        repair_payload_checksums(self.payload)
        return InventoryItem(index, item_id, quantity)


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
