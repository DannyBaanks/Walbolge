import hashlib
import sys
from pathlib import Path
from walbolge.paths import quine_source

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from walbolge.trace import trace_program

raw_path = quine_source()
raw = raw_path.read_text(encoding="utf-8")

t = trace_program(raw, max_steps=80_000_000, max_events=1000, classic=True)
out = t.output
out_bytes = out.encode("latin-1")
raw_bytes = raw.encode("latin-1")
print("steps:", t.steps, "| halt:", t.halt_reason, "| out len:", len(out_bytes), "| raw len:", len(raw_bytes))
print("output == raw bytes:", out_bytes == raw_bytes)
print("sha256 output:", hashlib.sha256(out_bytes).hexdigest())
print("sha256 raw   :", hashlib.sha256(raw_bytes).hexdigest())
print("output[:120]:", repr(out[:120]))
