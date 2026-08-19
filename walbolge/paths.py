"""Resolucion de rutas del repositorio y de sus entradas externas.

Este repositorio analiza un programa que no le pertenece (el quine de Malbolge
de Matthias Lutter) y usa artefactos producidos por proyectos hermanos. En vez
de incrustar rutas absolutas de la maquina del autor, cada entrada externa se
resuelve aqui: primero una variable de entorno, luego una ubicacion vecina
convencional, y si no aparece se falla con un mensaje que dice exactamente que
falta y como indicarlo.
"""
from __future__ import annotations

import os
from pathlib import Path

#: Raiz del repositorio (este archivo vive en <raiz>/walbolge/paths.py).
ROOT = Path(__file__).resolve().parents[1]

EVIDENCE = ROOT / "evidence"


def _from_env_or_siblings(env_var: str, relativos, descripcion: str) -> Path:
    valor = os.environ.get(env_var)
    if valor:
        p = Path(valor).expanduser().resolve()
        if p.exists():
            return p
        raise FileNotFoundError(
            "%s apunta a %s, que no existe.\n%s" % (env_var, p, descripcion))
    for rel in relativos:
        p = (ROOT.parent / rel).resolve()
        if p.exists():
            return p
    raise FileNotFoundError(
        "No se encontro %s.\nDefine %s con su ruta, o coloca el repositorio "
        "vecino junto a este.\nBuscado en: %s"
        % (descripcion, env_var, ", ".join(str(ROOT.parent / r) for r in relativos)))


def quine_source() -> Path:
    """El quine de Lutter (`baseline_quine.mal`).

    Obra de Matthias Lutter, no de este proyecto. Se distribuye en el
    repositorio Autobolge; aqui solo se referencia.
    """
    return _from_env_or_siblings(
        "WALBOLGE_QUINE",
        [Path("Autobolge") / "quine_research" / "baseline_quine.mal"],
        "el quine de Lutter (baseline_quine.mal)")


def translator_artifacts() -> Path:
    """Artefactos del proyecto Malbolge-Translator usados por los tests."""
    return _from_env_or_siblings(
        "MALBOLGE_TRANSLATOR_ARTIFACTS",
        [Path("Malbolge-Translator") / "artifacts" / "quijote"],
        "los artefactos de Malbolge-Translator (artifacts/quijote)")
