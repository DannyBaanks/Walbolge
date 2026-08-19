import sys
from pathlib import Path
from walbolge.paths import quine_source

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from walbolge.tables import crazy_operation

POW10 = 3**10
TABLE_CRAZY = ((1, 0, 0), (1, 0, 2), (2, 2, 1))


def crazy(a, b):
    result = 0
    d = 1
    for i in range(10):
        result += TABLE_CRAZY[int((b / d) % 3)][int((a / d) % 3)] * d
        d *= 3
    return result


raw = quine_source()
source = raw.read_text(encoding="utf-8")
chars = [ch for ch in source if ch not in (" ", "\n")]
print("len chars:", len(chars))

mem = [0] * POW10
for i, ch in enumerate(chars):
    mem[i] = ord(ch)
for i in range(len(chars), POW10):
    mem[i] = crazy(mem[i - 1], mem[i - 2])

mine = [ord(ch) for ch in chars]
while len(mine) < POW10:
    mine.append(crazy_operation(mine[-1], mine[-2]))

for i in range(len(chars), POW10):
    if mem[i] != mine[i]:
        print(f"DIFF en fill celda {i}: pip={mem[i]} walbolge={mine[i]} inputs pip=({mem[i-1]},{mem[i-2]}) wal=({mine[i-1]},{mine[i-2]})")
        print("  crazy( pip ):", crazy(mem[i - 1], mem[i - 2]))
        print("  crazy_operation( wal ):", crazy_operation(mine[i - 1], mine[i - 2]))
        break
else:
    print("fill idéntico")