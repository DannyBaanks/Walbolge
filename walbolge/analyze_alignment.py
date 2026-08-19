from walbolge.paths import translator_artifacts
from walbolge.paths import EVIDENCE
"""Alineación ground-truth: word files vs .op completo.

Encuentra dónde bootstrap + Σ(words) + 'v' diverge del .op completo
(esa divergencia = bridges/anclas insertados por el Translator).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from walbolge.decoder import load_opcodes
from walbolge.decompiler import BOOTSTRAP_OPS

CHAPTER = translator_artifacts() / "chapter_015"
NUM = 15

full_op = load_opcodes(str(CHAPTER / f"quijote_ch{NUM:03d}_full.op"))
manifest = json.loads((CHAPTER / f"quijote_ch{NUM:03d}_manifest.json").read_text(encoding="utf-8"))

word_paths = sorted(CHAPTER.glob("quijote_ch015_word_*.json"))
word_files = []
for wp in word_paths:
    meta = json.loads(wp.read_text(encoding="utf-8"))
    op_path = wp.with_suffix(".op")
    ops = load_opcodes(str(op_path))
    word_files.append({"index": meta["index"], "word": meta["word"], "opcodes": ops})

print(f"Word files: {len(word_files)} | full.op len: {len(full_op)}")

concat_words = "".join(w["opcodes"] for w in word_files)
candidate = BOOTSTRAP_OPS + concat_words + "v"
print(f"bootstrap+suma(words)+'v' len: {len(candidate)}")

divergence = -1
for i, (a, b) in enumerate(zip(candidate, full_op)):
    if a != b:
        divergence = i
        break

if divergence == -1 and len(candidate) == len(full_op):
    print("ALINEACIÓN EXACTA: bootstrap + Σ words + 'v' == full.op")
else:
    print(f"Primera divergencia en opcode position {divergence}")

cursor = len(BOOTSTRAP_OPS)
regions = [{"kind": "BOOTSTRAP", "start": 0, "end": cursor, "label": "i+o*99"}]
for w in word_files:
    start = cursor
    end = start + len(w["opcodes"])
    regions.append({"kind": "WORD", "start": start, "end": end,
                    "label": repr(w["word"]), "index": w["index"],
                    "matches_full": full_op[start:end] == w["opcodes"]})
    cursor = end

if full_op[cursor:cursor+1] == "v":
    regions.append({"kind": "HALT", "start": cursor, "end": cursor + 1, "label": "'v'"})
    cursor += 1

if cursor < len(full_op):
    regions.append({"kind": "TAIL_UNKNOWN", "start": cursor, "end": len(full_op),
                    "label": "opcodes extra no explicados"})

gaps = []
prev_end = len(BOOTSTRAP_OPS)
for r in regions[1:]:
    if r["start"] > prev_end:
        gaps.append({"kind": "UNKNOWN", "start": prev_end, "end": r["start"],
                     "label": "región no alineada"})
    prev_end = r["end"]

print("\nREGIONES (alineación ground-truth):")
for r in regions + gaps:
    span = f"[{r['start']:>6},{r['end']:>6})"
    label = r["label"]
    extra = ""
    if r["kind"] == "WORD":
        ok = "OK " if r.get("matches_full") else "DIFF"
        extra = f" {ok} full.op[{r['start']}:{r['end']}] == word file"
    print(f"  {r['kind']:<14} {span} {label!r:<22} {extra}")

word_texts = "".join(w["word"] for w in word_files)
print(f"\nConcatenación de textos de palabras == processed: {word_texts == manifest['processed']}")
print(f"Concatenación == original:                      {word_texts == manifest['original']}")
print(f"len(concat textos): {len(word_texts)} | len(processed): {len(manifest['processed'])}")

if word_texts != manifest["processed"]:
    for i, (a, b) in enumerate(zip(word_texts, manifest["processed"])):
        if a != b:
            print(f"  primer diff de texto en índice {i}: {a!r} vs {b!r}")
            break

with open(str(EVIDENCE / "alignment_chapter_015.json"), "w",
          encoding="utf-8") as f:
    json.dump({"regions": regions, "gaps": gaps,
               "word_texts_match_processed": word_texts == manifest["processed"],
               "divergence": divergence}, f, indent=2, ensure_ascii=False)
print("\nGuardado: evidence/alignment_chapter_015.json")