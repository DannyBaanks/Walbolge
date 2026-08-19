"""Walbolge — el inverso del Traductor de Malbolge.

Dado un programa .mal (o .op), reconstruye el texto que imprime y
descompone su estructura: bootstrap, palabras, saltos y halt.
"""
from __future__ import annotations

from .decoder import DecodedProgram, decode_program, load_opcodes
from .decompiler import decompile
from .trace import TraceEvent, TraceResult, trace_program

__version__ = "0.1.0"
__all__ = [
    "DecodedProgram", "TraceEvent", "TraceResult",
    "decode_program", "load_opcodes", "decompile", "trace_program",
    "__version__",
]