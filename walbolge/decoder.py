"""Decoder: .mal (ASCII) <-> opcodes. Walbolge no pierde información."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .tables import VALID_INSTRUCTIONS, opcode_at


@dataclass
class DecodedProgram:
    source: str
    positions: List[dict] = field(default_factory=list)
    opcodes: str = ""
    non_opcode_positions: List[dict] = field(default_factory=list)

    @property
    def opcode_count(self) -> int:
        return len(self.opcodes)


def decode_program(source: str) -> DecodedProgram:
    positions = []
    opcodes_chars = []
    non_opcode_positions = []

    for index, char in enumerate(source):
        op = opcode_at(ord(char), index)
        entry = {"index": index, "char": char, "opcode": op if op in VALID_INSTRUCTIONS else None}
        positions.append(entry)
        if op in VALID_INSTRUCTIONS:
            opcodes_chars.append(op)
        else:
            non_opcode_positions.append(entry)

    return DecodedProgram(
        source=source,
        positions=positions,
        opcodes="".join(opcodes_chars),
        non_opcode_positions=non_opcode_positions,
    )


def load_opcodes(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return "".join(ch for ch in text if ch in VALID_INSTRUCTIONS)