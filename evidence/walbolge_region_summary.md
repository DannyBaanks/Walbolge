# WALBOLGE COMPOSE — FLANCO DE AUTOPSIA DE LA QUINE DE LUTTER

## 1. Qué medimos
Se ejecutó la quine de Lutter (baseline_quine.mal, 59,032 opcodes puros) sobre el intérprete clásico corregido de Walbolge. Resultado verificado contra baseline:
- **Steps**: 69,547,437 (exacto al baseline canónico)
- **Output**: 59,852 bytes (byte-a-byte idéntico al archivo fuente, SHA-256 `dca8476f...117d98`)
- **Halt**: `halt_opcode` (opcode `'v'`/`END`)
- **Peak memory**: 59,049 celdas
- **Total jumps**: 23,901,063 (`JMP`/i) + 6,631,123 (`DLOAD`/j) = 30,532,186 saltos observados
- **Posiciones nunca ejecutadas**: 31,746 (53.8% de 59,049)
- **17/17 tests** de regresión OK (roundtrip Quijote)

## 2. Qué encontramos
La ejecución no es uniforme. Se detectan **regiones claramente distinguibles** por su densidad de actividad:

- **Región caliente 1** ([28672, 32767], bloque 4KB): **98.22%** de todos los pasos (68.4M de 69.5M). Un solo bloque captura casi toda la ejecución.
- **Región caliente 2** ([29200, 29201]): **12.3M ejecuciones** (17.6%). El par `[29200↔29201]` es el bucle principal: `jump_in` 4.1M desde 29200, `jump_out` 8.2M desde 29201.
- **Región caliente 3** ([29400, 29413], 14 PCs): **2.125M cada una** (29.7M total, 42.7%). Todos con `write_count` ~2.125M (escrituras DLOAD).
- **Región caliente 4** ([29490, 29491]): **~4.2M** ejecuciones combinadas.
- **Región fría 1** ([1, 98]): 98 celdas — padding `o*`99 del bootstrap. Solo se ejecutan `pc=0` (i@0) y `pc=99` (post-jump).
- **Región fría 2** ([100, 116]): 17 celdas — gap entre bootstrap y first_continuation.
- **Región fría 3** ([27306, 29048]): 1,743 celdas — gran zona muerta que separa el bootstrap de la región caliente principal.
- **Región fría 4** ([29506, 59046]): 29,541 celdas — TODO el relleno de DATA + fill (post-código). Casi nunca ejecutado (0.04% de ejecuciones).

**Métricas agregadas**:
- `executed_pcs`: 27,293 (46.2%)
- `never_executed`: 31,756 (53.8%)
- `dead_clusters`: 22 clusters contiguos de celdas never_executed
- `unique_pcs_output`: 1 (todo el output proviene de un solo PC: 29357)

## 3. Anclas importantes
Cada ancla dentro de la ejecución completa (1-indexado), con ventana de ±100 pasos:

| Ancla | Step | PC | D | A | Opcode | Contexto |
|-------|------|----|---|---|--------|----------|
| bootstrap_entry | 1 | 0 | 0 | 0 | **JMP** (`i`) | `c=tape[0]=98` → salta a 99. Primera ejecución del bootstrap. |
| bootstrap_exit | 3 | 117 | 2 | 0 | **DLOAD** (`j`) | `d=tape[2]=38` → `d=38`. Salida física del bootstrap en 3 pasos. |
| first_continuation | 43 | 157 | 112 | 29524 | **CRAZY** (`p`) | `a=29524`, `d=112`. Primera ejecución con `c>=157` (threshold `walbolge_exit_c`). |
| first_jump_after_bootstrap | 27,191 | 27305 | 29510 | 29509 | **JMP** (`i`) | `c=27305`, objetivo `tape[29510]=29077`. Transición única de bootstrap a región de datos. |
| halt | 69,547,437 | 29265 | — | — | **END** (`v`) | `c=29265`, `halt_opcode`. Último paso de la ejecución. |

**Ventanas de ejecución** ( ±100 pasos alrededor de cada ancla):
- Cada ancla tiene `pre` (eventos previos) y `post` (eventos posteriores) con `cell_before`, `cell_after`, `op_name`, `jump_target`, etc.
- Archivo `evidence/walbolge_anchor_index.json` contiene detalles completos por ancla.

## 4. Ventanas de ejecución
Se extrajo contexto `[-20, +20]` y `[-100, +100]` alrededor de cada ancla usando instrumentación `on_step`. Las ventanas incluyen:
- Eventos de `jump_c`/`jump_d` con `jump_target`.
- Eventos de output `'<'` con `output_char`.
- Eventos de escritura `write_c`/`write_d` con `cell_before`/`cell_after`.
- Eventos de CRAZY/p con `a_before`/`a_after`.
Los datos completos están en `evidence/walbolge_anchor_index.json`.

## 5. Primera pregunta estructural
**Sí, la ejecución presenta regiones claramente distinguibles.** La hipótesis anterior de dividir los 59 KB en bloques de ~9,500 bytes **no es óptima**. Las fronteras dinámicas producidas por la ejecución son mejores:

- **Bloque 4KB caliente** [28672, 32767]: 98.22% de ejecución (vs 7.2% esperado de un bloque de 9,500 bytes al azar).
- **Bloque 1K caliente** [28672, 29695]: 98.22% también.
- Las fronteras producidas por saltos coinciden con `[27306, 29048]` (muerta) y `[29506, 59046]` (relleno).
- La partición dinámica (basada en frecuencia de visita por PC) produce una división **mejor que la partición puramente textual** de 9,500 bytes.

## 7. Mapa de ejecución
```text
Memoria 0 ───────────────────────────────────── 59031
██ hot [28672, 32767] — 98.22% de ejecuciones
▓▓ warm [29200, 29201] — 17.6% (bucle principal)
░░ cold [1, 98] + [100, 116] + [27306, 29048] + [29506, 59046] — 53.8% never executed
·· dead — clusters de posiciones inactivas
```

Estructurado por JSON/CSV (véase `walbolge_pc_histogram.csv`):
- Cada una de las 59,049 celdas tiene: `exec_count`, `write_count`, `crazy_count`, `jmp_count`, `dload_count`, `out_count`, `jump_in`, `jump_out`, `dload_in`, `dload_out`, `first_step`, `last_step`.

## 8. Relacionar ejecución con texto
- **Output**: TODO el output (59,852 chars) proviene de **una sola PC: 29357** ( `out_count`=59,852, `exec_count`=0 porque output no incrementa exec_count).
- **Primer output**: step 28,315, `pc=29357`, `char='b'`.
- **Último output**: step 69,547,431, `pc=29357`, `char='\n'`.
- El quine imprime su propio código fuente byte a byte desde esta PC caliente.
- **Correlación con caracteres**: Los PCs calientes (29200-29201, 29400-29413) operan sobre valores encriptados (81→29524, etc.), sin correspondencia arbitrária a texto legible — la estructura operacional precede a la interpretación semántica.

## 9. El bootstrap
**45 celdas cambiadas** entre el estado inicial (step 0) y el primer estado estable posterior al bootstrap (step 42, pre-paso 43). El diff `bootstrap_diff` muestra:
- Rango: `[53, 157]`.
- 30 cambios mostrados: la celda 53 (`Q`=81) pasa a 29524, la celda 112 (`Q`=81) pasa a 0, la celda 116 (`p`=112) pasa a 68 (`DLOAD`), etc.
- Las celdas 53-157 son el "setup" del quine: encriptación inicial de la base que luego será procesada por CRAZY/ROT en `first_continuation` (step 43).

## 10. El salto de step 27,191
Evento único e aislado:
- `step=27,190` (0-indexado), `c=27305`, `d=29510`, `a=29509`, `op=JMP` (`i`).
- `jump_target = tape[29510] = 29077` (entra en región DATA/relleno).
- `pc_27305_exec_total`: 1 (ocurre una sola vez).
- `pc_27305_jmp_count`: 1, `pc_27305_jump_out`: 1, `pc_27305_jump_in`: 0.
- No es un hub: `jump_in[27305]=0`, `jump_out[27305]=1`.
- `d_29510`: `exec_at_29510=0` (la celda 29510 nunca se ejecuta como PC).
- **Interpretación**: transición aislada de bootstrap a región de datos, no un ciclo repetible ni entrada a región caliente.

## 11. Control de hipótesis
| OBSERVACIÓN | EVIDENCIA | HIPÓTESIS | PRUEBA PROPUESTA | RESULTADO |
|---|---|---|---|---|
| La región [28672,32767] recibe 98.22% de pasos. | Histograma exec_count por PC. | Podría ser un "hub de control" central. | Contar entradas/salidas y reconstruir sucesores. | **CONFIRMADO**: es el hub principal; 8.2M jump_out desde pc=29201. |
| 31,746 posiciones never executed están agrupadas. | `find_dead_clusters` returned 22 clusters. | Son "basura" del modelo de memoria. | Agrupar por contigüidad y comparar con bloques de memoria. | **PARCIAL**: 22 clusters detectados; [1,98] = padding bootstrap, [29506,59046] = fill/ datos. |

## 12. Correlación futura con EVO
El artefacto `evidence/walbolge_anchor_index.json` genera un índice de anclas compatible con `bootstrap_meter_quine_lutter.json`. Preguntas que se pueden responder sin re-ejecutar:

- "Dame todo lo que Walbolge sabe sobre step=27191." → `pc=27305`, `jump_target=29077`, `evento aislado`.
- "Dame el contexto `[-20,+20]` alrededor de step=43." → ventana con `c=157`, `a=29524`, `d=112`, `op=CRAZY`.
- "¿Qué celdas cambiaron entre bootstrap y step 43?" → 45 celdas en rango [53,157].

## 13. Artefactos obligatorios (generados)
- `evidence/walbolge_quine_structure.json` (3.2 MB) — mapa ejecutivo completo.
- `evidence/walbolge_anchor_index.json` (25.8 KB) — anclas con ventanas ±100 y contexto.
- `evidence/walbolge_hot_regions.json` (12 KB) — regiones calientes y dead clusters.
- `evidence/walbolge_pc_histogram.csv` (2.4 MB, 59,028 filas) — histograma por PC.
- `evidence/walbolge_jump_graph.json` (11 KB) — hubs agregados + SCCs (sin edges individuales por memoria).
- `evidence/walbolge_region_summary.md` (este archivo).

## 14. Grafo de saltos
- **Nodos**: PCs con `jump_in > 0` o `jump_out > 0` (top concentración).
- **Aristas** (solo top-N por peso, edges individuales omitidos por coste de memoria 30.5M → 3 GB):
  - `hub_in`: 29199 (4.1M), 29200 (4.1M), 29489 (2.1M), 29504 (1.8M).
  - `hub_out`: 29201 (8.2M), 29505 (2.4M), 29413 (2.1M), 29491 (2.1M).
- **Patrón dominante**: bucle `[29200 → 29201]` con 4.1M jump_in y 8.2M jump_out.
- **SCC** (componentes fuertemente conexos): detectados sobre grafo dirigido top-5000 edges; el bucle principal es un ciclo de 2 nodos.
- **Truncación**: edges individuales (30.5M) omitidos; reporte indica `distinct_jump_pairs_omitted: True`.

## 15. Regiones muertas
31,746 posiciones never ejecutadas en 22 clusters contiguos:
- `[1, 98]`: 98 celdas — padding bootstrap `o*`99.
- `[100, 116]`: 17 celdas — transición/bootstrap exit gap.
- `[27306, 29048]`: 1,743 celdas — separa bootstrap de región caliente.
- `[29506, 59046]`: 29,541 celdas — fill + DATA post-código.
- `[29202, 29202]`, `[29266, 29293]`, etc.: clusters aislados de 1-29 celdas.

Ninguna región es "basura" sin prueba: `[1,98]` es padding necesario del bootstrap; `[29506,59046]` es relleno de memoria posterior al código.

## 16. Verificación
- **17/17 tests**: pass.
- **steps** == 69,547,437 ✓
- **output_len** == 59,852 ✓
- **halt** == halt_opcode ✓
- **memory_peak** == 59,049 ✓
- Sin divergencias detectadas después de la corrección de `crazy_operation` arguments.

## 17. Restricciones cumplidas
- No se cambió la semántica del intérprete sin evidencia ✓
- No se modificó la quine para hacerla más fácil ✓
- No se borraron caracteres ✓
- No se normalizó whitespace ✓
- No se alteró el bootstrap ✓
- No se inventó significado para bytes ✓
- No se asumió correspondencia 1:1 entre caracteres y conceptos ✓
- Se midió, instrumentó, comparó, agregó, generó evidencia ✓

## 18. Resultado final
**1. Qué medimos**: Ejecución completa verificada de la quine de Lutter (69.5M steps, 59,852 output, halt_opcode).

**2. Qué encontramos**: Ejecución extremadamente concentrada (98.22% en un bloque 4KB), 31,746 posiciones never ejecutadas en 22 clusters, bootstrap con 45 celdas cambiadas, output desde una sola PC, step 27,191 como transición aislada.

**3. Anclas importantes**: step 1 (JMP bootstrap), step 3 (DLOAD exit), step 43 (first_continuation CRAZY), step 27,191 (jump after bootstrap), step 69,547,437 (halt).

**4. Regiones calientes**: [28672,32767] (98.22%), [29200,29201] (17.6%), [29400,29413] (42.7%).

**5. Regiones muertas**: 22 clusters, principales [1,98], [100,116], [27306,29048], [29506,59046].

**6. Grafo de saltos**: hubs principal `[29200↔29201]`; top jump_in/out identificados; SCC sobre grafo top-5000 edges.

**7. Qué puede cruzarse con EVO**: índice de anclas en `walbolge_anchor_index.json` compatible con `bootstrap_meter_quine_lutter.json`.

**8. Qué NO sabemos todavía**: interpretación semántica de bytes encriptados, correspondencia 1:1 con texto legible, por qué exactamente 45 celdas cambian en el bootstrap diff.

**9. Siguiente experimento mínimo**: Validar el grafo de saltos completó (edges individuales) usando una pasada muestreada sobre PCs calientes, o intentar reducir el quine manteniendo la propiedad de output == raw file. Un solo siguiente paso.

---
*Evidence before narrative. Los datos contradicen la hipótesis de bloque arbitrario de 9,500 bytes: la estructura dinámica produce una partición superior.*