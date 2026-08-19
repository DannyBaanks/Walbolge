"""Tracer paso a paso: ejecuta opcodes y registra cada evento con contexto."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .tables import (
    MAX_ADDRESS_SPACE,
    crazy_operation,
    encryption_lookup,
    opcode_at,
    reverse_normalize,
    ternary_rotate,
)


@dataclass
class TraceEvent:
    step: int
    c: int
    d: int
    a_before: int
    instruction: str
    tape_d: int
    event_type: str
    output_char: Optional[str] = None
    jump_target: Optional[int] = None
    write_c: Optional[int] = None
    write_d: Optional[int] = None
    a_after: int = 0
    cell_before: Optional[int] = None
    cell_after: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "c": self.c,
            "d": self.d,
            "a_before": self.a_before,
            "instruction": self.instruction,
            "tape_d": self.tape_d,
            "event_type": self.event_type,
            "output_char": self.output_char,
            "jump_target": self.jump_target,
            "write_c": self.write_c,
            "write_d": self.write_d,
            "a_after": self.a_after,
            "cell_before": self.cell_before,
            "cell_after": self.cell_after,
        }


@dataclass
class TraceResult:
    opcodes: str
    events: List[TraceEvent] = field(default_factory=list)
    output: str = ""
    steps: int = 0
    halted: bool = False
    halt_reason: str = ""
    events_recorded: int = 0
    events_dropped: bool = False
    jumps_count: int = 0
    executed_positions: set = field(default_factory=set)
    written_positions: set = field(default_factory=set)
    jumps: List[dict] = field(default_factory=list)
    peak_memory: int = 0

    def to_dict(self) -> dict:
        return {
            "opcodes_len": len(self.opcodes),
            "events": [e.to_dict() for e in self.events],
            "output": self.output,
            "steps": self.steps,
            "halted": self.halted,
            "halt_reason": self.halt_reason,
            "executed_positions": sorted(self.executed_positions),
            "written_positions": sorted(self.written_positions),
            "jumps_count": self.jumps_count,
            "jumps": self.jumps,
            "peak_memory": self.peak_memory,
        }


def trace_program(opcodes: str, max_steps: int = 5_000_000,
                  max_events: Optional[int] = None,
                  max_jumps: Optional[int] = None,
                  classic: bool = False,
                  on_step: Optional[callable] = None) -> TraceResult:
    """Traza opcodes (toolkit) o código fuente clásico (.mal).

    classic=True: semántica del intérprete clásico (malbolge.py):
      - el tape es el propio código fuente (sin ' ' ni '\\n')
      - memoria de MAX_ADDRESS_SPACE celdas (relleno crazy())
      - c y d envuelven en MAX_ADDRESS_SPACE
      - halt si la celda no es imprimible (33..126) o opcode 'v' (end)

    on_step: callback observacional on_step(evento, tape) llamado tras cada
      paso (no altera la semántica; no guarda eventos salvo max_events).
    """
    if classic:
        tape: List[int] = [ord(ch) for ch in opcodes if ch not in (" ", "\n")]
        while len(tape) < MAX_ADDRESS_SPACE:
            if len(tape) >= 2:
                tape.append(crazy_operation(tape[-1], tape[-2]))
            elif len(tape) == 1:
                tape.append(crazy_operation(tape[0], tape[0]))
            else:
                tape.append(0)
    else:
        tape = [ord(ch) for ch in reverse_normalize(opcodes)]
    a, c, d = 0, 0, 0
    program_length = len(opcodes)
    result = TraceResult(opcodes=opcodes, peak_memory=len(tape))

    def ensure_capacity(index: int) -> None:
        nonlocal tape
        while len(tape) <= index:
            if len(tape) >= 2:
                next_value = crazy_operation(tape[-1], tape[-2])
            elif len(tape) == 1:
                next_value = crazy_operation(tape[0], tape[0])
            else:
                next_value = 0
            tape.append(next_value)
            if len(tape) >= MAX_ADDRESS_SPACE:
                break
        if len(tape) > result.peak_memory:
            result.peak_memory = len(tape)

    steps = 0
    output_chars: List[str] = []
    halted = False
    halt_reason = ""

    while not halted:
        if steps >= max_steps:
            halted = True
            halt_reason = "max_steps"
            break
        if classic:
            if c >= MAX_ADDRESS_SPACE:
                halted = True
                halt_reason = "program_end"
                break
            if tape[c] < 33 or tape[c] > 126:
                halted = True
                halt_reason = "classic_non_printable"
                break
        elif c >= program_length:
            halted = True
            halt_reason = "program_end"
            break

        ensure_capacity(c)
        cell_value = tape[c]
        instruction = opcode_at(cell_value, c)
        result.executed_positions.add(c)
        c_exec = c
        a_before = a
        tape_d = tape[d] if d < len(tape) else 0

        event_type = "execute"
        output_char = None
        jump_target = None
        write_c = None
        write_d = None

        if instruction == "i":
            ensure_capacity(d)
            jump_target = tape[d]
            from_c = c
            c = jump_target
            ensure_capacity(c)
            event_type = "jump_c"
            result.jumps_count += 1
            if max_jumps is None or len(result.jumps) < max_jumps:
                result.jumps.append({"step": steps, "from_c": from_c, "target": jump_target})
        elif instruction == "<":
            output_char = chr(a % 256)
            output_chars.append(output_char)
            event_type = "output"
        elif instruction == "/":
            event_type = "input"
        elif instruction == "*":
            ensure_capacity(d)
            a = ternary_rotate(tape[d])
            tape[d] = a
            write_d = d
            result.written_positions.add(d)
            event_type = "rotate_write"
        elif instruction == "j":
            ensure_capacity(d)
            jump_target = tape[d]
            from_d = d
            d = jump_target
            ensure_capacity(d)
            event_type = "jump_d"
            result.jumps_count += 1
            if max_jumps is None or len(result.jumps) < max_jumps:
                result.jumps.append({"step": steps, "from_d": from_d, "target": jump_target})
        elif instruction == "p":
            ensure_capacity(d)
            a = crazy_operation(a, tape[d])
            tape[d] = a
            write_d = d
            result.written_positions.add(d)
            event_type = "crazy_write"
        elif instruction == "o":
            event_type = "nop"
        elif instruction == "v":
            halted = True
            halt_reason = "halt_opcode"
            event_type = "halt"

        encrypted = encryption_lookup(tape[c])
        if encrypted != tape[c]:
            tape[c] = encrypted
            write_c = c
            result.written_positions.add(c)

        if classic:
            c = 0 if c == MAX_ADDRESS_SPACE - 1 else c + 1
            d = 0 if d == MAX_ADDRESS_SPACE - 1 else d + 1
        else:
            c += 1
            d += 1
        steps += 1

        build_event = (on_step is not None
                       or max_events is None
                       or len(result.events) < max_events)
        if build_event:
            ev = TraceEvent(
                step=steps - 1,
                c=c_exec,
                d=d - 1 if not classic else (d - 1 if d > 0 else MAX_ADDRESS_SPACE - 1),
                a_before=a_before,
                instruction=instruction,
                tape_d=tape_d,
                event_type=event_type,
                output_char=output_char,
                jump_target=jump_target,
                write_c=write_c,
                write_d=write_d,
                a_after=a,
                cell_before=cell_value,
                cell_after=tape[c_exec],
            )
            if on_step is not None:
                on_step(ev, tape)
            if max_events is None or len(result.events) < max_events:
                result.events.append(ev)

        if instruction == "v":
            break

    result.steps = steps
    result.halted = halted
    result.halt_reason = halt_reason
    result.events_recorded = len(result.events)
    result.events_dropped = max_events is not None and steps > max_events
    result.output = "".join(output_chars)
    return result