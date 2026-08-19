from walbolge.paths import quine_source
"""Sondeo rápido del quine de Lutter: ¿los \n del .mal están en el tape?"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from walbolge.trace import trace_program

RAW = quine_source()
raw = RAW.read_text(encoding="utf-8")
clean = raw.replace("\n", "")
print(f"raw len={len(raw)} clean len={len(clean)}")

for label, text in (("H1 clean (sin \\n)", clean), ("H2 raw (con \\n)", raw)):
    ops = ""
    bad = 0
    for ch in text:
        if 33 <= ord(ch) <= 126:
            ops += ch
        else:
            bad += 1
    print(f"--- {label}: chars no imprimibles={bad}, opcodes a trazar={len(ops)}")
    t = trace_program(ops, max_steps=50000, max_events=200)
    print(f"    steps={t.steps} halted={t.halted} reason={t.halt_reason} "
          f"output_len={len(t.output)}")
    print(f"    output head: {t.output[:60]!r}")