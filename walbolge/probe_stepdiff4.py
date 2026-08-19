from walbolge.paths import quine_source
"""Diff intercalado con volcado completo en la divergencia."""
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


raw = quine_source()
source = raw.read_text(encoding="utf-8")
chars = [ch for ch in source if ch not in (" ", "\n")]

mem = [0] * POW10
pip_init(source, mem)

mine = [ord(ch) for ch in chars]
while len(mine) < POW10:
    mine.append(crazy_operation(mine[-2], mine[-1]))

OPS = {4: "i", 5: "<", 23: "/", 39: "*", 40: "j", 62: "p", 68: "o", 81: "v"}
history = []
a, c, d = 0, 0, 0
ma, mc, md = 0, 0, 0
LIMIT = 3000
for step in range(LIMIT):
    if (mc, md, ma) != (c, d, a):
        print(f"DIVERGENCIA antes del paso {step}: pip c={c} d={d} a={a} | walbolge c={mc} d={md} a={ma}")
        for h in history[-6:]:
            print("  hist:", h)
        break
    v = (mem[c] + c) % 94
    op = OPS.get(v, "?")
    hist = {"step": step, "c": c, "d": d, "a": a, "op": op, "v": v,
            "cell": mem[c], "tape_d": mem[d] if d < len(mem) else "?"}
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
        print(f"pip halt end paso {step}")
        break
    if mem[c] >= 33 and mem[c] <= 126:
        mem[c] = ord(ENCRYPTION_TRANSLATE[mem[c] - 33])
    c = 0 if c == POW10 - 1 else c + 1
    d = 0 if d == POW10 - 1 else d + 1

    v2 = (mine[mc] + mc) % 94
    op2 = OPS.get(v2, "?")
    if op2 != op:
        print(f"DIVERGENCIA de opcode en paso {step}: pip={op}(v={v},cell={mem[c]-1 if False else mem[c]}) walbolge={op2}(v={v2})")
        break
    if v2 == 4:
        mc = mine[md]
    elif v2 == 5:
        pass
    elif v2 == 23:
        ma = POW10 - 1
    elif v2 == 39:
        ma = mine[md] = ternary_rotate(mine[md])
    elif v2 == 40:
        md = mine[md]
    elif v2 == 62:
        ma = mine[md] = crazy_operation(ma, mine[md])
    elif v2 == 81:
        print(f"walbolge halt end paso {step}")
        break
    if mine[mc] >= 33 and mine[mc] <= 126:
        mine[mc] = ord(ENCRYPTION_TRANSLATE[mine[mc] - 33])
    mc = 0 if mc == POW10 - 1 else mc + 1
    md = 0 if md == POW10 - 1 else md + 1

    hist["after"] = {"c": c, "d": d, "a": a}
    history.append(hist)
else:
    print(f"{LIMIT} pasos en lockstep")