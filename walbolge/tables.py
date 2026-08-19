"""Tablas semánticas de Malbolge (espejo del toolkit malbolge-generator)."""
from __future__ import annotations

NORMAL_TRANSLATE = (
    "+b(29e*j1VMEKLyC})8&m#~W>qxdRp0wkrUo[D7,XTcA\"lI.v%{gJh4G\\-=O@5`_3i<?Z'"
    ";FNQuY]szf$!BS/|t:Pn6^Ha"
)
ENCRYPTION_TRANSLATE = (
    "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/8|jsb9m<.TVa"
    "c`uY*MK'X~xDl}REokN:#?G\"i@"
)
VALID_INSTRUCTIONS = "i</*jpov"

MAX_ADDRESS_SPACE = 59049
TERNARY_DIGITS = 10
MAX_TERNARY_POWER = 3**9
_CRAZY_TABLE = (1, 1, 2, 0, 0, 2, 0, 2, 1)


def ternary_rotate(value: int) -> int:
    return (value // 3) + (value % 3) * MAX_TERNARY_POWER


def crazy_operation(first: int, second: int) -> int:
    total = 0
    power = 1
    local_first = first
    local_second = second
    for _ in range(TERNARY_DIGITS):
        total += _CRAZY_TABLE[(local_first % 3) * 3 + (local_second % 3)] * power
        local_first //= 3
        local_second //= 3
        power *= 3
    return total


def opcode_at(value: int, index: int) -> str:
    return NORMAL_TRANSLATE[(value - 33 + index) % 94]


def encryption_lookup(value: int) -> int:
    if 33 <= value <= 126:
        return ord(ENCRYPTION_TRANSLATE[value - 33])
    return value


def reverse_normalize(opcodes: str, start_index: int = 0) -> list[str]:
    chars = []
    for offset, opcode in enumerate(opcodes):
        index = start_index + offset
        offset_value = (NORMAL_TRANSLATE.index(opcode) - index) % 94
        chars.append(chr(offset_value + 33))
    return chars