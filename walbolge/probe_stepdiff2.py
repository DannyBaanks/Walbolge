from walbolge.paths import quine_source
"""Diff estado a estado: pip vs walbolge classic — primera divergencia."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from walbolge.tables import ENCRYPTION_TRANSLATE, ternary_rotate, crazy_operation

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


def pip_one_step(mem, a, c, d):
    if mem[c] < 33 or mem[c] > 126:
        return a, c, d, "halt_non_printable"
    v = (mem[c] + c) % 94
    if v == 4:
        c = mem[d]
    elif v == 5:
        pass
    elif v == 23:
        a = POW10 - 1
    elif v == 39:
        a = mem[d] = rotate(mem[d])
    elif v == 40:
        d = mem[d]
    elif v == 62:
        a = mem[d] = crazy(a, mem[d])
    elif v == 81:
        return a, c, d, "halt_end"
    if mem[c] >= 33 and mem[c] <= 126:
        mem[c] = ord(ENCRYPTION_TRANSLATE[mem[c] - 33])
    c = 0 if c == POW10 - 1 else c + 1
    d = 0 if d == POW10 - 1 else d + 1
    return a, c, d, None


raw = quine_source()
source = raw.read_text(encoding="utf-8")
tape_chars = "".join(ch for ch in source if ch not in (" ", "\n"))

mem = [0] * POW10
pip_init(source, mem)

mine_tape = [ord(ch) for ch in tape_chars]
while len(mine_tape) < POW10:
    if len(mine_tape) >= 2:
        mine_tape.append(crazy_operation(mine_tape[-2], mine_tape[-1]))
    else:
        mine_tape.append(0)

a, c, d = 0, 0, 0
ma, mc, md = 0, 0, 0

LIMIT = 3000
for step in range(LIMIT):
    if (mc, md, ma) != (c, d, a):
        print(f"divergencia en step {step}:")
        print(f"  pip      : c={c} d={d} a={a}")
        print(f"  walbolge : c={mc} d={md} a={ma}")
        break
    res = pip_one_step(mem, a, c, d)
    if res[3]:
        print(f"pip halt en step {step}: {res[3]} (c={res[1]})")
        break
    a, c, d = res[0], res[1], res[2]
    # walbolge: replicar un paso (misma lógica, copia local)
    v = (mine_tape[mc] + mc) % 94
    if v == 4:
        mc = mine_tape[md]
    elif v == 5:
        pass
    elif v == 23:
        ma = POW10 - 1
    elif v == 39:
        ma = mine_tape[md] = ternary_rotate(mine_tape[md])
    elif v == 40:
        md = mine_tape[md]
    elif v == 62:
        ma = mine_tape[md] = crazy_operation(ma, mine_tape[md])
    elif v == 81:
        print(f"walbolge halt end en step {step}")
        break
    if mine_tape[mc] >= 33 and mine_tape[mc] <= 126:
        mine_tape[mc] = ord(ENCRYPTION_TRANSLATE[mine_tape[mc] - 33])
    mc = 0 if mc == POW10 - 1 else mc + 1
    md = 0 if md == POW10 - 1 else md + 1
    if step % 500 == 0:
        print(f"  step {step}: pip c={c} d={d} a={a} | walbolge c={mc} d={md} a={ma}")
else:
    print("3000 pasos sin divergencia")