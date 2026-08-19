from walbolge.paths import quine_source
"""Diff paso a paso: loop del pip (malbolge.py) vs modo clásico de Walbolge."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from walbolge.tables import ENCRYPTION_TRANSLATE, _CRAZY_TABLE, ternary_rotate
from walbolge.trace import trace_program

POW9, POW10 = 3**9, 3**10
TABLE_CRAZY = ((1, 0, 0), (1, 0, 2), (2, 2, 1))


def crazy(a, b):
    result = 0
    d = 1
    for i in range(10):
        result += TABLE_CRAZY[int((b / d) % 3)][int((a / d) % 3)] * d
        d *= 3
    return result


def rotate(n):
    return POW9 * (n % 3) + n // 3


def pip_initialize(source, mem):
    i = 0
    for c in source:
        if c == " " or c == "\n":
            continue
        mem[i] = ord(c)
        i += 1
    while i < POW10:
        mem[i] = crazy(mem[i - 1], mem[i - 2])
        i += 1


def pip_steps(source, limit):
    mem = [0] * POW10
    pip_initialize(source, mem)
    a, c, d = 0, 0, 0
    output = []
    steps = 0
    while 1:
        if mem[c] < 33 or mem[c] > 126:
            return steps, "non_printable", "".join(output), mem
        v = (mem[c] + c) % 94
        if v == 4:
            c = mem[d]
        elif v == 5:
            output.append(chr(int(a % 256)))
        elif v == 23:
            a = POW10 - 1
        elif v == 39:
            a = mem[d] = rotate(mem[d])
        elif v == 40:
            d = mem[d]
        elif v == 62:
            a = mem[d] = crazy(a, mem[d])
        elif v == 81:
            return steps, "end", "".join(output), mem
        if mem[c] >= 33 and mem[c] <= 126:
            mem[c] = ord(ENCRYPTION_TRANSLATE[mem[c] - 33])
        c = 0 if c == POW10 - 1 else c + 1
        d = 0 if d == POW10 - 1 else d + 1
        steps += 1
        if steps >= limit:
            return steps, "limit", "".join(output), mem
        if v == 4 or v == 40:
            pass


raw = quine_source()
source = raw.read_text(encoding="utf-8")

LIMIT = 5000
steps, reason, out, mem = pip_steps(source, LIMIT)
print(f"pip: steps={steps} reason={reason} output_len={len(out)}")

t = trace_program(source, max_steps=LIMIT, max_events=LIMIT, classic=True)
print(f"walbolge: steps={t.steps} reason={t.halt_reason} output_len={len(t.output)}")

ev = [e for e in t.events]
print(f"walbolge eventos: {len(ev)} | pip eventos: {steps}")
if ev:
    print("primeros 8 eventos walbolge:")
    for e in ev[:8]:
        print(f"  step={e.step} c={e.c} d={e.d} a_before={e.a_before} op={e.instruction} type={e.event_type}")