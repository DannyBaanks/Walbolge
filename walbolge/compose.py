from __future__ import annotations
from walbolge.paths import quine_source
from walbolge.paths import ROOT
"""Walbolge COMPOSE — autopsia estructural del quine de Lutter.

PASADA ÚNICA con loop inline (réplica de trace.py, validada por canónico):
  - histogramas por PC: exec, write, crazy, jmp, dload, out, jump_in/out, dload_in/out, first/last
  - ventanas [-W,+W] alrededor de 5 anclas
  - 4 snapshots de memoria (step 0, 42, 27190, 69547436)
  - log de outputs

POST-PROCESO:
  - bloques 1KB / 4KB / 9500 (agregados desde exec_count)
  - dead clusters
  - top PCs (exec, jump_in, jump_out, write)
  - diff bootstrap (snap[0] vs snap[42])
  - análisis específico del step 27,191
  - hubs in/out del grafo de saltos (top-N)
"""

import json
import csv
from collections import deque
from pathlib import Path

from .tables import MAX_ADDRESS_SPACE, crazy_operation, opcode_at

OP_NAMES = {"i": "JMP", "<": "OUT", "/": "IN", "*": "ROT",
            "j": "DLOAD", "p": "CRAZY", "o": "NOP", "v": "END"}
OP_NUMS = {"i": 4, "<": 5, "/": 23, "*": 39, "j": 40, "p": 62, "o": 68, "v": 81}
ENCRYPT_STR = ("5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72FhOA1CB6v^=I_0/"
               "8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@")
ENCRYPT_ORD = [ord(ch) for ch in ENCRYPT_STR]

CANONICAL = {"steps": 69_547_437, "output_len": 59_852,
             "halt_reason": "halt_opcode", "peak_memory": 59_049}
BLOCK_SIZES = [1024, 4096, 9500]
BLOCK_COUNTS = [59, 15, 7]


def classic_tape(source: str):
    tape = [ord(ch) for ch in source if ch not in (" ", "\n")]
    while len(tape) < MAX_ADDRESS_SPACE:
        if len(tape) >= 2:
            tape.append(crazy_operation(tape[-1], tape[-2]))
        elif len(tape) == 1:
            tape.append(crazy_operation(tape[0], tape[0]))
        else:
            tape.append(0)
    return tape


def light_event(step, c, d, a_before, a_after, ins_char,
                cell_before, cell_after, jump_target,
                write_c, write_d, output_char):
    if ins_char in OP_NAMES:
        op = OP_NUMS[ins_char]
        name = OP_NAMES[ins_char]
    else:
        op = (cell_before + c) % 94
        name = f"INVALID({op})"
    return {"step": step, "c": c, "d": d, "a_before": a_before,
            "a_after": a_after, "op": op, "op_name": name,
            "cell_before": cell_before, "cell_after": cell_after,
            "jump_target": jump_target, "write_c": write_c,
            "write_d": write_d, "output_char": output_char}


def analyze(source: str, anchors_1idx, window=100, max_steps=100_000_000,
            verbose=True):
    n = MAX_ADDRESS_SPACE
    exec_count = [0] * n
    write_count = [0] * n
    crazy_count = [0] * n
    jmp_count = [0] * n
    dload_count = [0] * n
    out_count = [0] * n
    first_step = [-1] * n
    last_step = [-1] * n
    jump_in = [0] * n
    jump_out = [0] * n
    dload_in = [0] * n
    dload_out = [0] * n
    output_log = []
    anchors = sorted(a - 1 for a in anchors_1idx)
    post_remaining = {}
    windows = {a: {"pre": [], "post": []} for a in anchors}
    buf = deque(maxlen=window + 5)
    snap_steps = {0, 42, 27190, 69547436}
    snapshots = {}
    total_jumps = total_dloads = total_writes = 0

    a_min = max(0, min(anchors) - window)
    a_max = max(anchors) + window

    tape = classic_tape(source)
    peak_memory = len(tape)
    a = c = d = 0
    steps = 0
    halted = False
    halt_reason = ""

    while not halted:
        if steps >= max_steps:
            halted = True
            halt_reason = "max_steps"
            break
        if c >= MAX_ADDRESS_SPACE or tape[c] < 33 or tape[c] > 126:
            halted = True
            halt_reason = "non_printable"
            break

        c_exec = c
        a_before = a
        tape_d = tape[d] if d < len(tape) else 0
        cell_value = tape[c]
        instruction = opcode_at(cell_value, c)
        jump_target = None
        write_c = None
        write_d = None
        output_char = None

        if instruction == "i":
            jump_target = tape[d]
            c = jump_target
        elif instruction == "<":
            output_char = chr(a % 256)
        elif instruction == "*":
            a = (tape[d] // 3) + (tape[d] % 3) * 19683
            tape[d] = a
            write_d = d
        elif instruction == "j":
            jump_target = tape[d]
            d = jump_target
        elif instruction == "p":
            a = crazy_operation(a, tape[d])
            tape[d] = a
            write_d = d
        elif instruction == "v":
            halted = True
            halt_reason = "halt_opcode"

        if 33 <= tape[c] <= 126:
            enc = ENCRYPT_ORD[tape[c] - 33]
            if enc != tape[c]:
                tape[c] = enc
                write_c = c

        c = 0 if c == MAX_ADDRESS_SPACE - 1 else c + 1
        d = 0 if d == MAX_ADDRESS_SPACE - 1 else d + 1
        steps += 1
        st = steps - 1

        exec_count[c_exec] += 1
        if first_step[c_exec] < 0:
            first_step[c_exec] = st
        last_step[c_exec] = st
        if write_c is not None:
            write_count[write_c] += 1
            total_writes += 1
        if write_d is not None:
            write_count[write_d] += 1
            total_writes += 1
        if instruction == "i":
            jmp_count[c_exec] += 1
            total_jumps += 1
            jump_out[c_exec] += 1
            jump_in[jump_target] += 1
        elif instruction == "j":
            dload_count[c_exec] += 1
            total_dloads += 1
            dload_out[c_exec] += 1
            dload_in[jump_target] += 1
        elif instruction == "p":
            crazy_count[c_exec] += 1
        elif instruction == "<":
            out_count[c_exec] += 1
            output_log.append((st, c_exec, output_char))

        if st in snap_steps:
            snapshots[st] = list(tape)

        if a_min <= st <= a_max:
            ed = light_event(st, c_exec, d - 1 if d > 0 else MAX_ADDRESS_SPACE - 1,
                             a_before, a, instruction, cell_value,
                             tape[c_exec] if c_exec < len(tape) else None,
                             jump_target, write_c, write_d, output_char)
            buf.append(ed)
            for ai in anchors:
                if st == ai:
                    pre = list(buf)
                    if len(pre) > window:
                        pre = pre[-window:]
                    windows[ai]["pre"] = pre
                    post_remaining[ai] = window
                elif ai in post_remaining and post_remaining[ai] > 0:
                    windows[ai]["post"].append(ed)
                    post_remaining[ai] -= 1

        if instruction == "v":
            break

    if verbose:
        print(f"pasos={steps} halt={halt_reason} jmps={total_jumps} "
              f"dloads={total_dloads} writes={total_writes}")
    return {
        "exec_count": exec_count, "write_count": write_count,
        "crazy_count": crazy_count, "jmp_count": jmp_count,
        "dload_count": dload_count, "out_count": out_count,
        "first_step": first_step, "last_step": last_step,
        "jump_in": jump_in, "jump_out": jump_out,
        "dload_in": dload_in, "dload_out": dload_out,
        "output_log": output_log, "windows": windows, "snapshots": snapshots,
        "total_jumps": total_jumps, "total_dloads": total_dloads,
        "total_writes": total_writes, "halt_reason": halt_reason,
        "peak_memory": peak_memory, "steps": steps,
    }


def find_dead_clusters(executed):
    clusters = []
    start = None
    for i, cnt in enumerate(executed):
        if cnt == 0:
            if start is None:
                start = i
        elif start is not None:
            clusters.append({"start": start, "end": i - 1, "len": i - start})
            start = None
    if start is not None:
        clusters.append({"start": start, "end": len(executed) - 1,
                         "len": len(executed) - start})
    return clusters


def main():
    base = ROOT
    raw = quine_source()
    source = raw.read_text(encoding="utf-8")
    evidence = base / "evidence"
    evidence.mkdir(parents=True, exist_ok=True)

    anchors_1idx = [1, 3, 43, 27_191, 69_547_437]
    R = analyze(source, anchors_1idx, window=100)

    # ---- verificación canónica ----
    canon_ok = (R["steps"] == CANONICAL["steps"]
                and len(R["output_log"]) == CANONICAL["output_len"]
                and R["halt_reason"] == CANONICAL["halt_reason"]
                and R["peak_memory"] == CANONICAL["peak_memory"])
    print(f"canónico OK={canon_ok} (steps={R['steps']}, out={len(R['output_log'])}, "
          f"halt={R['halt_reason']}, peak={R['peak_memory']})")
    if not canon_ok:
        print("DIVERGENCIA — abortando")
        return

    exec_count = R["exec_count"]
    write_count = R["write_count"]
    n = MAX_ADDRESS_SPACE

    # ---- top PCs ----
    top_exec = sorted(range(n), key=lambda p: exec_count[p], reverse=True)[:30]
    top_jump_in = sorted(range(n), key=lambda p: R["jump_in"][p], reverse=True)[:20]
    top_jump_out = sorted(range(n), key=lambda p: R["jump_out"][p], reverse=True)[:20]
    top_write = sorted(range(n), key=lambda p: write_count[p], reverse=True)[:20]

    # ---- bloques 1K/4K/9500 ----
    blocks = {}
    for bs, ncnt in zip(BLOCK_SIZES, BLOCK_COUNTS):
        bs_share = [0] * ncnt
        for p in range(n):
            bs_share[p // bs] += exec_count[p]
        total = R["steps"]
        blocks[str(bs)] = {
            "size": bs, "count": ncnt, "total_exec": sum(bs_share),
            "blocks": [
                {"start": i * bs, "end": min((i + 1) * bs, n) - 1,
                 "exec": bs_share[i],
                 "share": round(bs_share[i] / total, 6),
                 "writes": sum(write_count[i * bs:min((i + 1) * bs, n)])}
                for i in range(ncnt)],
        }

    # ---- dead clusters ----
    dead = find_dead_clusters(exec_count)
    executed_count = sum(1 for c in exec_count if c > 0)
    never_executed = sum(1 for c in exec_count if c == 0)

    # ---- bootstrap diff: snap[0] vs snap[42] ----
    snap0 = R["snapshots"].get(0)
    snap42 = R["snapshots"].get(42)
    snap_last = R["snapshots"].get(69_547_436)
    bootstrap_diff = None
    if snap0 is not None and snap42 is not None:
        changed = [i for i in range(n) if snap0[i] != snap42[i]]
        bootstrap_diff = {
            "cells_changed": len(changed),
            "first_changed": changed[0] if changed else None,
            "last_changed": changed[-1] if changed else None,
            "changed_first_200": [{"cell": i, "before": snap0[i], "after": snap42[i]}
                                  for i in changed[:200]],
            "truncated": len(changed) > 200,
        }
    final_diff_count = (sum(1 for i in range(n) if snap0[i] != snap_last[i])
                        if snap0 is not None and snap_last is not None else None)

    # ---- anclas ----
    anchors_json = {}
    for a1 in anchors_1idx:
        i = a1 - 1
        w = R["windows"][i]
        pre20 = [e for e in w["pre"] if e["step"] >= i - 20]
        post20 = [e for e in w["post"] if e["step"] <= i + 20]
        ev_main = w["pre"][-1] if w["pre"] else None
        first_out = next((e for e in R["output_log"] if e[0] >= i - 100), None)
        anchors_json[str(a1)] = {
            "step_1idx": a1,
            "event": ev_main,
            "window_-100_+100": {"pre": w["pre"], "post": w["post"]},
            "window_-20_+20": {"pre": pre20, "post": post20},
            "next_output_in_window": (
                {"step": first_out[0], "pc": first_out[1],
                 "char": first_out[2]} if first_out else None),
            "context": {
                "exec_at_pc": exec_count[ev_main["c"]] if ev_main else 0,
                "write_at_pc": write_count[ev_main["c"]] if ev_main else 0,
                "jmp_at_pc": R["jmp_count"][ev_main["c"]] if ev_main else 0,
                "crazy_at_pc": R["crazy_count"][ev_main["c"]] if ev_main else 0,
                "dload_at_pc": R["dload_count"][ev_main["c"]] if ev_main else 0,
                "out_at_pc": R["out_count"][ev_main["c"]] if ev_main else 0,
            } if ev_main else None,
        }

    # ---- step 27,191 específico ----
    ev_27191 = R["windows"][27190]["pre"][-1]
    pc_27191 = ev_27191["c"]
    target_27191 = ev_27191["jump_target"]
    # sucesor: el siguiente jump de pc=27305 — sin guardar edges, aproximamos:
    #   el siguiente jump con from=27305 aparece en jump_out[27305] (cuenta),
    #   pero no tenemos los destinos individuales. Documentar como limitación.
    s27 = {
        "event": ev_27191,
        "pc_27305_exec_total": exec_count[27305],
        "pc_27305_jmp_count": R["jmp_count"][27305],
        "pc_27305_jump_in": R["jump_in"][27305],
        "pc_27305_jump_out": R["jump_out"][27305],
        "pc_27305_first_step": R["first_step"][27305],
        "pc_27305_last_step": R["last_step"][27305],
        "pc_27305_write_count": write_count[27305],
        "d_29510": {
            "exec_at_29510": exec_count[29510],
            "jump_in_at_29510": R["jump_in"][29510],
            "dload_in_at_29510": R["dload_in"][29510],
        },
        "note": "edges individuales (origen->destino) no se agregaron en esta "
                 "pasada por coste de memoria (30.5M de aristas). "
                 "Hubs y métricas agregadas sí.",
    }

    # ---- estructura ----
    structure = {
        "canonical_verified": canon_ok,
        "execution": {
            "steps": R["steps"], "output_len": len(R["output_log"]),
            "halt_reason": R["halt_reason"], "peak_memory": R["peak_memory"],
            "total_jumps": R["total_jumps"], "total_dloads": R["total_dloads"],
            "total_writes": R["total_writes"],
        },
        "memory": {
            "size": n,
            "executed_pcs": executed_count,
            "never_executed": never_executed,
            "never_executed_share": round(never_executed / n, 4),
            "dead_clusters": dead,
        },
        "top_pcs_exec": [{"pc": p, "exec": exec_count[p],
                           "write": write_count[p], "out": R["out_count"][p]}
                          for p in top_exec],
        "top_pcs_jump_in": [{"pc": p, "jump_in": R["jump_in"][p]}
                            for p in top_jump_in],
        "top_pcs_jump_out": [{"pc": p, "jump_out": R["jump_out"][p]}
                             for p in top_jump_out],
        "top_pcs_write": [{"pc": p, "write": write_count[p]} for p in top_write],
        "blocks": blocks,
        "bootstrap_diff": bootstrap_diff,
        "final_vs_initial_changed": final_diff_count,
        "output": {
            "first_output": ({"step": R["output_log"][0][0],
                              "pc": R["output_log"][0][1],
                              "char": R["output_log"][0][2]}
                             if R["output_log"] else None),
            "last_output": ({"step": R["output_log"][-1][0],
                             "pc": R["output_log"][-1][1],
                             "char": R["output_log"][-1][2]}
                            if R["output_log"] else None),
            "unique_pcs_output": len({o[1] for o in R["output_log"]}),
        },
        "step_27191_analysis": s27,
    }

    (evidence / "walbolge_quine_structure.json").write_text(
        json.dumps(structure, indent=2), encoding="utf-8")
    (evidence / "walbolge_anchor_index.json").write_text(
        json.dumps(anchors_json, indent=2), encoding="utf-8")
    (evidence / "walbolge_hot_regions.json").write_text(
        json.dumps({
            "top_pcs_exec": structure["top_pcs_exec"],
            "top_pcs_jump_in": structure["top_pcs_jump_in"],
            "top_pcs_jump_out": structure["top_pcs_jump_out"],
            "top_pcs_write": structure["top_pcs_write"],
            "blocks_1k": blocks["1024"]["blocks"],
            "blocks_4k": blocks["4096"]["blocks"],
            "blocks_9500": blocks["9500"]["blocks"],
            "dead_clusters": dead,
        }, indent=2), encoding="utf-8")
    (evidence / "walbolge_jump_graph.json").write_text(
        json.dumps({
            "total_jumps": R["total_jumps"],
            "total_dloads": R["total_dloads"],
            "distinct_jump_pairs_omitted": True,
            "omission_reason": "30.5M de aristas individuales; memoria "
                                "excesiva. Solo se reportan hubs agregados.",
            "hub_in": structure["top_pcs_jump_in"],
            "hub_out": structure["top_pcs_jump_out"],
        }, indent=2), encoding="utf-8")
    # CSV del histograma
    with open(evidence / "walbolge_pc_histogram.csv", "w", newline="",
              encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["pc", "exec", "write", "crazy", "jmp", "dload", "out",
                     "jump_in", "jump_out", "dload_in", "dload_out",
                     "first_step", "last_step"])
        for p in range(n):
            if exec_count[p] or write_count[p]:
                wr.writerow([p, exec_count[p], write_count[p],
                             R["crazy_count"][p], R["jmp_count"][p],
                             R["dload_count"][p], R["out_count"][p],
                             R["jump_in"][p], R["jump_out"][p],
                             R["dload_in"][p], R["dload_out"][p],
                             R["first_step"][p], R["last_step"][p]])
    print("Artefactos escritos en evidence/")
    print(f"dead_clusters={len(dead)} | executed_pcs={executed_count}")
    print(f"first_output step={R['output_log'][0][0]} pc={R['output_log'][0][1]}")
    if bootstrap_diff:
        print(f"bootstrap diff: {bootstrap_diff['cells_changed']} celdas cambiaron "
              f"(rango [{bootstrap_diff['first_changed']},{bootstrap_diff['last_changed']}])")


if __name__ == "__main__":
    main()
