# Walbolge

**El inverso del [Malbolge Translator](https://github.com/DannyBaanks/Malbolge-Translator).**

Malbolge Translator: texto → programa Malbolge (.mal / .op).
**Walbolge: programa Malbolge → texto + estructura (decompilación).**

El nombre es el juego de palabras de la inversión: MALBOLGE → **W**ALBOLGE.
Misma familia Bolge, dirección contraria.

## Qué hace

Dado un programa generado por el Translator:

1. **Decodifica** el `.mal` (ASCII) a opcodes posición a posición sin perder
   información (cada carácter se anota con su opcode o se marca como no-opcode).
2. **Traza** la ejecución paso a paso con la semántica exacta del toolkit
   `malbolge-generator` (misma tabla, mismo crazy/rotate, misma expansión de
   memoria y auto-encripción).
3. **Reconstruye el texto** que imprime el programa (salida de los opcodes `<`).
4. **Descompone la estructura**: bootstrap (`i` + `o*99`), palabras
   (con spans de opcodes), saltos (`i`/`j`), posiciones nunca ejecutadas
   (datos muertos) y halt (`v`).
5. **Verifica roundtrip** contra el manifiesto del Translator
   (`processed`/`original`/`words`/`opcodes`) y contra los archivos
   `word_*.op` (la concatenación bootstrap + palabras + `v` debe ser
   exactamente el `.op` completo).

## Uso

```bash
python -m walbolge "artifacts/quijote/chapter_015/quijote_ch015_full.mal" \
    --manifest "artifacts/quijote/chapter_015/quijote_ch015_manifest.json" \
    --words-dir "artifacts/quijote/chapter_015" \
    --json evidence/chapter_015_report.json
```

## Test del Quijote

```bash
python tests/test_roundtrip.py
```

Verifica para cada capítulo disponible:

- opcodes decodificados == `.op` guardado por el Translator
- texto reconstruido == texto `processed` del manifiesto
- palabras detectadas == palabras del manifiesto
- bootstrap + palabras + `v` == `.op` completo

## Familia Bolge

| Repo | Dirección |
|------|-----------|
| `Malbolge-Translator` | texto → Malbolge |
| **`Walbolge`** | Malbolge → texto (este repo) |
| `Autobolge` | búsqueda automática de quines |

## Dependencias

Ninguna. Walbolge es 100% autónomo: las tablas de traducción y la semántica
están espejadas en `walbolge/tables.py` (fuente: `malbolge-generator`).

---

## Análisis del quine de Lutter

El repositorio incluye la evidencia de una instrumentación completa del quine
de Malbolge de **Matthias Lutter** — 69,547,437 pasos, termina por opcode de
halt, emite 59,852 bytes. El quine es obra suya, no de este proyecto; aquí sólo
se mide.

Tres resultados que salieron de esa traza:

**La salida entera pasa por una sola arista.** El programa emite desde
exactamente un program counter (29357), y sólo una arista entra a esa celda:
`29358 → 29357`, recorrida **59,852 veces** — idéntico a la longitud de la
salida. Un salto por carácter emitido. La traza y el grafo de saltos son
mediciones independientes y coinciden exacto.

**Una ley de conservación de flujo, y su única violación es el halt.** Como un
salto en Malbolge aterriza en el destino y la ejecución reanuda en destino+1:

```
exec(pc+1) = exec(pc) − jump_out(pc) + jump_in(pc)
```

Se cumple en **27,313** program counters y falla en **exactamente uno**: el pc
29265, que ejecuta una sola vez en el último paso. La ley localiza la
terminación sin buscarla.

**El grafo de control son 80 aristas.** Sobre 22 orígenes y 39 destinos, para
23,901,063 eventos de salto. La celda más caliente, el pc 29201, tiene 13
destinos distintos y 8,205,432 saltos, y es la única celda caliente que nunca
se escribe.

Los datos están en `evidence/`: `walbolge_pc_histogram.csv` (una fila por celda
con exec / write / jump_in / jump_out / first_step / last_step),
`walbolge_jump_edges.json` (las 80 aristas con sus conteos) y
`walbolge_mutaciones_dirigidas.json` (mutaciones dirigidas con sus controles).

### Una hipótesis que probamos y matamos

El cociente write/exec sobre las celdas ejecutadas tiene una banda vacía: 19
celdas por debajo de 0.01, 27,274 en ≈1 o más, y **nada** entre 0.01 y 0.5.
Parecía marcar el código estático esencial. Prueba directa: mutar esas 19
cambia el comportamiento en **16 de 19**; mutar 10 celdas al azar del otro lado
lo cambia en **8 de 10**. 84% contra 80% — el cociente no discrimina.

La explicación aburrida es la correcta: en un quine el fuente *es* el dato, así
que mutar a nivel de fuente daña casi cualquier celda sin importar su función.
El resultado negativo está en `evidence/walbolge_test_19_celdas.json` junto con
el positivo, porque una hipótesis refutada es evidencia igual que una
confirmada.
