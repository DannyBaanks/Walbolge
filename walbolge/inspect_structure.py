import json
from pathlib import Path
from walbolge.paths import EVIDENCE

base = EVIDENCE
d = json.loads((base / "walbolge_quine_structure.json").read_text(encoding="utf-8"))

print("=== EXECUTION ===")
for k, v in d["execution"].items():
    print(f"  {k}: {v}")
print("=== MEMORY ===")
m = d["memory"]
print(f"  size: {m['size']}")
print(f"  executed_pcs: {m['executed_pcs']}")
print(f"  never_executed: {m['never_executed']}")
print(f"  never_executed_share: {m['never_executed_share']}")
print(f"  dead_clusters: {len(m['dead_clusters'])} total_len={sum(c['len'] for c in m['dead_clusters'])}")
print("Clusters (start,end,len):")
for c in m["dead_clusters"][:25]:
    print(f"  [{c['start']},{c['end']}] len={c['len']}")

print("=== TOP PCS EXEC ===")
for r in d["top_pcs_exec"][:20]:
    print(f"  pc={r['pc']:>5} exec={r['exec']:>9} write={r['write']:>6} out={r['out']}")

print("=== TOP JUMP IN ===")
for r in d["top_pcs_jump_in"][:15]:
    print(f"  pc={r['pc']:>5} jump_in={r['jump_in']}")

print("=== TOP JUMP OUT ===")
for r in d["top_pcs_jump_out"][:15]:
    print(f"  pc={r['pc']:>5} jump_out={r['jump_out']}")

print("=== TOP WRITE ===")
for r in d["top_pcs_write"][:15]:
    print(f"  pc={r['pc']:>5} write={r['write']}")

print("=== BOOTSTRAP DIFF ===")
print(f"  cells_changed: {d['bootstrap_diff']['cells_changed']}")
print(f"  range=[{d['bootstrap_diff']['first_changed']},{d['bootstrap_diff']['last_changed']}]")
print("  first 30 cambios:")
for ch in d["bootstrap_diff"]["changed_first_200"][:30]:
    print(f"    cell={ch['cell']:>4} before={ch['before']:>4} after={ch['after']:>4}  char_before={chr(ch['before']) if 33<=ch['before']<=126 else '?'} -> char_after={chr(ch['after']) if 33<=ch['after']<=126 else '?'}")

print("=== OUTPUT ===")
print(f"  first_output: {d['output']['first_output']}")
print(f"  last_output:  {d['output']['last_output']}")
print(f"  unique_pcs_output: {d['output']['unique_pcs_output']}")

print("=== STEP 27191 ANALYSIS ===")
for k, v in d["step_27191_analysis"].items():
    if k != "note":
        print(f"  {k}: {v}")

print("=== BLOCKS 1K (share) ===")
for b in d["blocks"]["1024"]["blocks"]:
    bar = "#" * int(b["share"] * 200)
    print(f"  [{b['start']:>5},{b['end']:>5}] share={b['share']:.4f} {bar}")

print("=== BLOCKS 4K (share) ===")
for b in d["blocks"]["4096"]["blocks"]:
    bar = "#" * int(b["share"] * 50)
    print(f"  [{b['start']:>5},{b['end']:>5}] share={b['share']:.4f} {bar}")

print("=== BLOCKS 9500 (share) ===")
for b in d["blocks"]["9500"]["blocks"]:
    bar = "#" * int(b["share"] * 50)
    print(f"  [{b['start']:>5},{b['end']:>5}] share={b['share']:.4f} {bar}")

print(f"\nfinal_vs_initial_changed: {d['final_vs_initial_changed']}")
