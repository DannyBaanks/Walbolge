"""CLI de Walbolge: walbolge <programa.mal|.op> [--manifest ...] [--words-dir ...] [--json ...]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .decoder import load_opcodes
from .decompiler import decompile


def _load_source(path: str) -> tuple:
    text = Path(path).read_text(encoding="utf-8")
    if path.endswith(".op"):
        return None, load_opcodes(path)
    return text, None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="walbolge", description=__doc__)
    parser.add_argument("input", help="Programa .mal (ASCII) o .op (opcodes)")
    parser.add_argument("--manifest", help="Manifiesto JSON con el texto original")
    parser.add_argument("--words-dir", help="Directorio con archivos word_*.op")
    parser.add_argument("--json", help="Guardar reporte completo en JSON")
    parser.add_argument("--max-steps", type=int, default=5_000_000)
    parser.add_argument("--max-events", type=int, default=None,
                        help="Limitar eventos de traza en memoria (0 = todos)")
    parser.add_argument("--max-jumps", type=int, default=100_000,
                        help="Limitar saltos guardados en el reporte (contador total aparte)")
    parser.add_argument("--classic", action="store_true",
                        help="Semántica del intérprete clásico (.mal crudo: "
                             "salta ' ' y '\\n', wrap en 59049, halt en celda no imprimible)")
    parser.add_argument("--trace-limit", type=int, default=40,
                        help="Eventos de traza a imprimir (0 = ninguno)")
    args = parser.parse_args(argv)

    source, opcodes = _load_source(args.input)
    report = decompile(source_text=source, opcodes=opcodes,
                       manifest_path=args.manifest,
                       words_dir=args.words_dir,
                       max_steps=args.max_steps,
                       max_events=args.max_events,
                       max_jumps=args.max_jumps,
                       classic=args.classic)

    print("=" * 64)
    print("WALBOLGE — decompilación inversa del Translator")
    print("=" * 64)
    d = report["decoded"]
    print(f"Fuente     : {args.input}")
    print(f"Chars      : {d['source_chars']:,} | Opcodes: {d['opcode_count']:,}"
          f" | No-opcode: {len(d['non_opcode_positions'])}")
    b = report["bootstrap"]
    print(f"Bootstrap  : {'SI (' + str(b['opcode_start']) + '-' + str(b['opcode_end']) + ')' if b else 'NO'}")
    e = report["execution"]
    print(f"Ejecución  : {e['steps']:,} pasos | halt={e['halt_reason']}"
          f" | memoria pico={e['peak_memory']:,}")
    print(f"Output     : {e['output_len']:,} chars | palabras: {len(report['words'])}")
    print(f"Posiciones : {report['executed_ratio']*100:.1f}% ejecutadas"
          f" | {report['never_executed_count']:,} nunca ejecutadas")
    if report["jumps_count"]:
        print(f"Saltos     : {report['jumps_count']:,} (guardados {len(report['jumps'])})")
    rt = report["roundtrip_vs_manifest"]
    if rt:
        print(f"Roundtrip  : processed={rt['processed_match']}"
              f" original={rt['original_match']}"
              f" words={rt['words_match']} opcodes={rt['opcodes_match']}")
    wv = report["words_vs_word_files"]
    if wv:
        print(f"Word files : status={wv['status']} found={wv.get('found')}"
              f" concat_match={wv.get('concat_with_bootstrap_matches_full')}"
              f" halt_v_in_last={wv.get('last_word_includes_halt_v')}")
    print()
    print("SEGMENTOS:")
    for s in report["segments"]:
        print(f"  [{s['kind']:>14}] opcodes {s['opcode_start']}-{s['opcode_end']}"
              f"  {s['description']}")
    print()
    print("TEXTO RECONSTRUIDO:")
    print(repr(e["output"])[:400])
    print()
    print("REGIONES (span -> output -> comportamiento):")
    print(f"  {'span':<18} {'output':<14} {'steps':>6} {'escrituras':>10}  opcodes ejecutados")
    for w in report["words"][:20]:
        b = w["behavior"]
        span = f"[{w['opcode_span'][0]},{w['opcode_span'][1]})"
        counts = " ".join(f"{k}*{v}" for k, v in sorted(b["opcode_counts"].items()))
        print(f"  {span:<18} {w['text']!r:<14} {b['steps']:>6} {b['memory_writes']:>10}  {counts}")
    if len(report["words"]) > 20:
        print(f"  ... y {len(report['words'])-20} regiones más (ver --json)")
    if wv and wv.get("per_word"):
        bad = [pw for pw in wv["per_word"] if not pw["matches_full"]]
        if bad:
            print(f"\n  DISCREPANCIAS word files: {len(bad)}")
            for pw in bad[:5]:
                print(f"    {pw['file']} span={pw['span']} texto={pw['word_text']!r}")
        else:
            print(f"\n  OK: los {wv['found']} word files alinean exactamente con el .op")

    if args.trace_limit > 0:
        print()
        print(f"TRAZA (primeros {args.trace_limit} eventos):")
        print(f"  {'step':>6} {'c':>6} {'op':>2} {'d':>6} {'a_antes':>8}  evento")
        for ev in report["trace_excerpt"]:
            out_ch = f" -> {ev['output_char']!r}" if ev["output_char"] else ""
            jmp = f" -> {ev['jump_target']}" if ev["jump_target"] is not None else ""
            print(f"  {ev['step']:>6} {ev['c']:>6} {ev['instruction']:>2} {ev['d']:>6} {ev['a_before']:>8}  {ev['event_type']}{out_ch}{jmp}")

    if args.json:
        out = Path(args.json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nReporte completo: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())