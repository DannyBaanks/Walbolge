"""Decompiler: reconstruye el texto y la estructura del programa generado.

Estructura esperada de un programa del Translator:
  [bootstrap: 'i' + 'o'*99] + [continuaciones por palabra] + ['v']

Tokenización del Translator (descubierta por alineación ground-truth):
  words = processed.split(' ')  -- cada espacio es una palabra propia,
  los '\n' quedan embebidos dentro de los tokens.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .decoder import DecodedProgram, decode_program, load_opcodes
from .trace import TraceResult, trace_program

BOOTSTRAP_OPS = "i" + "o" * 99


@dataclass
class WordInfo:
    index: int
    text: str
    output_start: int
    output_end: int
    output_positions: List[int] = field(default_factory=list)
    opcode_span: List[int] = field(default_factory=list)
    behavior: Dict[str, object] = field(default_factory=dict)
    matches_word_file: Optional[bool] = None

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "text": self.text,
            "output_start": self.output_start,
            "output_end": self.output_end,
            "output_positions": self.output_positions,
            "opcode_span": self.opcode_span,
            "behavior": self.behavior,
            "matches_word_file": self.matches_word_file,
        }


@dataclass
class SegmentInfo:
    kind: str
    opcode_start: int
    opcode_end: int
    description: str = ""

    def to_dict(self) -> dict:
        return {"kind": self.kind, "opcode_start": self.opcode_start,
                "opcode_end": self.opcode_end, "description": self.description}


def detect_bootstrap(opcodes: str) -> Optional[dict]:
    if opcodes.startswith(BOOTSTRAP_OPS):
        return {"opcode_start": 0, "opcode_end": 100, "kind": "bootstrap"}
    head = opcodes[:120]
    if "i" in head:
        first_i = head.index("i")
        if opcodes[first_i:first_i + 100] == BOOTSTRAP_OPS:
            return {"opcode_start": first_i, "opcode_end": first_i + 100, "kind": "bootstrap"}
    return None


def split_words(text: str) -> List[str]:
    """Tokenización del Translator: cada run de whitespace
    (espacios y saltos de línea) es una palabra propia."""
    return re.split(r"(\s+)", text)


def _word_behavior(trace: TraceResult, start: int, end: int) -> Dict[str, object]:
    ops: Dict[str, int] = {}
    writes = 0
    steps = 0
    for ev in trace.events:
        if start <= ev.c < end:
            steps += 1
            ops[ev.instruction] = ops.get(ev.instruction, 0) + 1
            if ev.event_type in ("rotate_write", "crazy_write", "write"):
                writes += 1
    return {"steps": steps, "opcode_counts": ops, "memory_writes": writes}


def _build_words(trace: TraceResult, bootstrap_end: int) -> List[WordInfo]:
    output_events = [e for e in trace.events if e.event_type == "output"]
    output_positions = [e.c for e in output_events]
    words: List[WordInfo] = []
    prev_last_output = bootstrap_end - 1
    char_cursor = 0
    for idx, word_text in enumerate(split_words(trace.output)):
        start = trace.output.find(word_text, char_cursor)
        end = start + len(word_text)
        positions = output_positions[start:end]
        last_output = positions[-1] if positions else prev_last_output
        setup_start = prev_last_output + 1 if positions else prev_last_output + 1
        span = [setup_start, last_output + 1] if positions else [setup_start, setup_start]
        words.append(WordInfo(
            index=idx, text=word_text,
            output_start=start, output_end=end,
            output_positions=positions, opcode_span=span,
        ))
        char_cursor = end
        prev_last_output = last_output
    return words


def decompile(source_text: Optional[str] = None,
              opcodes: Optional[str] = None,
              manifest_path: Optional[str] = None,
              words_dir: Optional[str] = None,
              max_steps: int = 5_000_000,
              max_events: Optional[int] = None,
              max_jumps: Optional[int] = None,
              classic: bool = False,
              trace_limit: int = 40) -> dict:
    decoded: Optional[DecodedProgram] = None
    if source_text is not None:
        if classic:
            source_text = "".join(ch for ch in source_text if ch not in (" ", "\n"))
        decoded = decode_program(source_text)
        opcodes = decoded.opcodes
    if opcodes is None:
        raise ValueError("Se requiere source_text u opcodes.")

    trace_source = source_text if classic else opcodes
    trace: TraceResult = trace_program(trace_source, max_steps=max_steps,
                                       max_events=max_events,
                                       max_jumps=max_jumps, classic=classic)

    bootstrap = detect_bootstrap(opcodes)
    bootstrap_end = bootstrap["opcode_end"] if bootstrap else 0

    words = _build_words(trace, bootstrap_end)

    for w in words:
        w.behavior = _word_behavior(trace, w.opcode_span[0], w.opcode_span[1]) \
            if not trace.events_dropped else {"steps": 0, "opcode_counts": {},
                                              "memory_writes": 0,
                                              "note": "eventos truncados (max_events)"}

    segments: List[SegmentInfo] = []
    if bootstrap:
        segments.append(SegmentInfo("bootstrap", bootstrap["opcode_start"],
                                    bootstrap["opcode_end"],
                                    "estado ancla (i + o*99)"))
    if words:
        words_start = words[0].opcode_span[0]
        words_end = words[-1].opcode_span[1]
        segments.append(SegmentInfo("continuations", words_start, words_end,
                                    f"{len(words)} palabras, {len(trace.output)} chars"))

    halt_event = next((e for e in reversed(trace.events) if e.event_type == "halt"), None)
    if halt_event is not None:
        segments.append(SegmentInfo("halt", halt_event.c, halt_event.c + 1,
                                    "opcode 'v'"))

    manifest = None
    if manifest_path:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    roundtrip = None
    if manifest:
        roundtrip = {
            "processed_match": manifest.get("processed") == trace.output,
            "original_match": manifest.get("original") == trace.output,
            "words_match": manifest.get("words") == len(words),
            "opcodes_match": manifest.get("opcodes") == len(opcodes),
        }

    words_verification = None
    if words_dir:
        words_verification = verify_word_files(opcodes, words, words_dir)

    executed = sorted(trace.executed_positions)
    executed_ratio = len(executed) / max(1, len(opcodes))
    never_executed = sorted(set(range(len(opcodes))) - trace.executed_positions)

    return {
        "decoded": {
            "source_chars": len(decoded.source) if decoded else len(opcodes),
            "opcode_count": len(opcodes),
            "non_opcode_positions": (decoded.non_opcode_positions
                                     if decoded else []),
        },
        "bootstrap": bootstrap,
        "execution": {
            "steps": trace.steps,
            "halted": trace.halted,
            "halt_reason": trace.halt_reason,
            "output": trace.output,
            "output_len": len(trace.output),
            "output_count": len([e for e in trace.events if e.event_type == "output"]),
            "peak_memory": trace.peak_memory,
        },
        "trace_excerpt": [e.to_dict() for e in trace.events[:trace_limit]],
        "executed_positions": executed,
        "executed_ratio": round(executed_ratio, 4),
        "never_executed_count": len(never_executed),
        "never_executed": never_executed,
        "jumps": trace.jumps,
        "jumps_count": trace.jumps_count,
        "written_positions": sorted(trace.written_positions),
        "words": [w.to_dict() for w in words],
        "segments": [s.to_dict() for s in segments],
        "roundtrip_vs_manifest": roundtrip,
        "words_vs_word_files": words_verification,
    }


def _load_word_files(words_dir: str) -> List[dict]:
    word_paths = sorted(Path(words_dir).glob("*_word_*.op"))
    files = []
    for p in word_paths:
        try:
            files.append({"path": p, "name": p.stem,
                          "opcodes": load_opcodes(str(p))})
        except Exception:
            continue
    return files


def verify_word_files(opcodes: str, words: List[WordInfo], words_dir: str) -> dict:
    files = _load_word_files(words_dir)
    if not files:
        return {"status": "no_word_files", "found": 0}

    word_ops = [f["opcodes"] for f in files]
    concat = BOOTSTRAP_OPS + "".join(word_ops)
    full_match = concat == opcodes

    per_word = []
    cursor = len(BOOTSTRAP_OPS)
    for i, f in enumerate(files):
        start = cursor
        end = start + len(f["opcodes"])
        expected = (words[i].text if hasattr(words[i], "text")
                    else words[i]["text"]) if i < len(words) else "?"
        per_word.append({
            "file": f["name"],
            "word_text": expected,
            "span": [start, end],
            "matches_full": opcodes[start:end] == f["opcodes"],
        })
        cursor = end

    last_ends_with_v = bool(word_ops) and word_ops[-1].endswith("v")
    return {
        "status": "checked",
        "found": len(files),
        "concat_with_bootstrap_matches_full": full_match,
        "last_word_includes_halt_v": last_ends_with_v,
        "words_match_count": sum(1 for w in per_word if w["matches_full"]),
        "per_word": per_word,
    }