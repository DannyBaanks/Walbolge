from walbolge.paths import quine_source
"""Diff: pip paso a paso vs eventos de trace_program(classic=True)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from walbolge.tables import ENCRYPTION_TRANSLATE
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


def pip_init(source, mem):
    i = 0
    for c in source:
        if c == " " or c == "\n":
            continue
        mem[i] = ord(c)
        i += 1
    while i < POW10:
        mem[i] = crazy(mem[i - 1], mem[i - 2])
        i += 1


raw = quine_source()
source = raw.read_text(encoding="utf-8")

mem = [0] * POW10
pip_init(source, mem)

t = trace_program(source, max_steps=3000, max_events=3000, classic=True)
evs = t.events

a, c, d = 0, 0, 0
LIMIT = min(3000, len(evs))
for step in range(LIMIT):
    e = evs[step]
    # comparar estado POST-paso pip vs walbolge reconstruido
    pip_c, pip_d, pip_a = c, d, a
    if mem[c] < 33 or mem[c] > 126:
        print(f"pip halt non_printable en paso {step}")
        break
    v = (mem[c] + c) % 94
    op = None
    if v == 4:
        c = mem[d]; op = "i"
    elif v == 5:
        op = "<"
    elif v == 23:
        a = POW10 - 1; op = "/"
    elif v == 39:
        a = mem[d] = rotate(mem[d]); op = "*"
    elif v == 40:
        d = mem[d]; op = "j"
    elif v == 62:
        a = mem[d] = crazy(a, mem[d]); op = "p"
    elif v == 81:
        print(f"pip halt end en paso {step}")
        break
    if mem[c] >= 33 and mem[c] <= 126:
        mem[c] = ord(ENCRYPTION_TRANSLATE[mem[c] - 33])
    c = 0 if c == POW10 - 1 else c + 1
    d = 0 if d == POW10 - 1 else d + 1

    w_c = 0 if e.c == POW10 - 1 else e.c + 1
    w_d = 0 if e.d == POW10 - 1 else e.d + 1
    if (c, d, a) != (w_c, w_d, e.a_after):
        print(f"DIVERGENCIA real en paso {step}:")
        print(f"  pip      : c={c} d={d} a={a} op={op}")
        print(f"  walbolge : c={w_c} d={w_d} a={e.a_after} op={e.instruction}")
        print(f"  eventos previos:")
        for prev in evs[max(0, step - 3):step + 1]:
            print(f"    c={prev.c} d={prev.d} a={prev.a_before}->{prev.a_after} op={prev.instruction} type={prev.event_type}")
        break
else:
    print(f"{LIMIT} pasos en lockstep sin divergencia")