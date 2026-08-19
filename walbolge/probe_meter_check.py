from walbolge.paths import quine_source
"""Reconciliación: hitos del BOOTSTRAP METER vs traza de Walbolge (classic)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from walbolge.tables import opcode_at
from walbolge.trace import trace_program

raw = quine_source()
source = raw.read_text(encoding="utf-8")

t = trace_program(source, max_steps=28_000, max_events=28_000, classic=True)
evs = t.events
print("pasos trazados:", t.steps)

CLASICOS = {4: "JMP", 5: "OUT", 23: "IN", 39: "ROT", 40: "DLOAD", 62: "CRAZY", 68: "NOP", 81: "END"}


def opis(c):
    return CLASICOS.get((evs_tape[c] + c) % 94, "?")


evs_tape = None


def check(name, step, c, d, a, op=None, target=None):
    e = evs[step]
    cell = opcode_at(e.c, 0)  # no usado
    ok = (e.c == c and e.d == d and e.a_before == a)
    extra = ""
    if target is not None:
        ok = ok and e.jump_target == target
        extra = f" target={e.jump_target}"
    print(f"{'OK ' if ok else 'DIFF'} {name:<28} walbolge step={step} c={e.c} d={e.d} a={e.a_before} op={e.instruction}{extra}")


# bootstrap_entry
check("bootstrap_entry (step 1)", 0, 0, 0, 0, target=98)
check("paso 2 (c=99 JMP)", 1, 99, 1, 0, target=116)
# bootstrap_exit
check("bootstrap_exit (step 3)", 2, 117, 2, 0)
# first_continuation: primer c>=157
for i, e in enumerate(evs):
    if e.c >= 157:
        print(f"{'OK ' if i == 42 else 'DIFF'} first_continuation walbolge step={i} c={e.c} d={e.d} a={e.a_before} op={e.instruction}")
        break
# first_jump_after_bootstrap: primer jump_c con c_exec >= 100
for i, e in enumerate(evs):
    if e.event_type == "jump_c" and e.c >= 100:
        print(f"{'OK ' if i == 27190 else 'DIFF'} first_jump_after_bootstrap walbolge step={i} c={e.c} d={e.d} a={e.a_before} target={e.jump_target}")
        break