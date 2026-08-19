"""Roundtrip del Quijote: .mal -> texto == manifiesto, estructura == word files."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from walbolge.paths import translator_artifacts
from walbolge.decoder import decode_program, load_opcodes
from walbolge.decompiler import BOOTSTRAP_OPS, decompile, verify_word_files

ARTIFACTS = translator_artifacts()


def check_chapter(chapter_dir: Path) -> dict:
    num = int(chapter_dir.name.split("_")[1])
    mal_path = chapter_dir / f"quijote_ch{num:03d}_full.mal"
    op_path = chapter_dir / f"quijote_ch{num:03d}_full.op"
    manifest_path = chapter_dir / f"quijote_ch{num:03d}_manifest.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    source = mal_path.read_text(encoding="utf-8")
    decoded = decode_program(source)
    expected_op = load_opcodes(str(op_path))

    report = decompile(source_text=source, manifest_path=str(manifest_path),
                       words_dir=str(chapter_dir))

    result = {
        "chapter": num,
        "decode_matches_op": decoded.opcodes == expected_op,
        "output_matches_processed": report["execution"]["output"] == manifest["processed"],
        "output_matches_original": report["execution"]["output"] == manifest["original"],
        "words_match": len(report["words"]) == manifest["words"],
        "bootstrap_detected": report["bootstrap"] is not None,
        "halt_reason": report["execution"]["halt_reason"],
        "steps": report["execution"]["steps"],
        "executed_ratio": report["executed_ratio"],
        "output_len": report["execution"]["output_len"],
        "opcodes": len(decoded.opcodes),
        "words_count": len(report["words"]),
    }
    wv = verify_word_files(decoded.opcodes, report["words"], str(chapter_dir))
    result["word_files"] = wv
    return result


def main() -> int:
    chapters = sorted([p for p in ARTIFACTS.glob("chapter_*") if (p / "quijote_ch{0:03d}_full.mal".format(int(p.name.split("_")[1]))).exists()])
    if not chapters:
        chapters = sorted(ARTIFACTS.glob("chapter_*"))

    results = []
    failures = 0
    for chapter in chapters:
        r = check_chapter(chapter)
        results.append(r)
        status = "OK " if (r["decode_matches_op"] and r["output_matches_processed"]
                           and r["words_match"] and r["bootstrap_detected"]) else "FAIL"
        if status == "FAIL":
            failures += 1
        wf = r["word_files"].get("concat_with_bootstrap_matches_full")
        print(f"[{status}] ch{r['chapter']:03d} opcodes={r['opcodes']:>5,} "
              f"steps={r['steps']:>7,} out={r['output_len']:>4} words={r['words_count']} "
              f"exec%={r['executed_ratio']*100:5.1f} wordconcat={wf} "
              f"halt={r['halt_reason']}")

    summary = {
        "chapters": results,
        "total": len(results),
        "failures": failures,
    }
    out = Path(__file__).resolve().parent.parent / "evidence" / "roundtrip_summary.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nEvidencia: {out}")
    print(f"Total: {len(results)} capítulos | Fallos: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())