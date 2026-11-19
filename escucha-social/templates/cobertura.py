# TEMPLATE de la skill `escucha-social`. Copiar a pipeline/cobertura.py.
# Depende de pipeline.normalize (RAW_X, load_runs) y de pipeline._common.
# Correr SIEMPRE antes de report: si imprime bloques en cero, el .docx debe declararlo.
"""Cobertura real del barrido: qué (keyword × ventana) se capturó y qué falta.

Existe porque el 2026-09-11 la cuenta de Apify tocó su tope mensual a mitad del barrido y
el hueco resultante NO fue aleatorio: las corridas se lanzan en orden de keyword, así que
se perdió todo el final de la lista —los bloques `riesgo` y `temas_org` quedaron en cero—.
Reportar proporciones sobre una base así subestima justo lo que no se buscó.

Uso:
    python -m pipeline.cobertura
"""
from __future__ import annotations

import collections

from pipeline._common import chunk_windows, load_config
from pipeline.normalize import RAW_X, load_runs


def resumen() -> dict:
    cfg = load_config()
    todas = chunk_windows(cfg["window"]["start"], cfg["window"]["end"], cfg.get("chunk", "month"))
    capturadas: dict[str, set] = collections.defaultdict(set)
    for run in load_runs(RAW_X):
        e = run.get("extra") or {}
        if e.get("keyword") and e.get("win_start"):
            capturadas[e["keyword"]].add(e["win_start"])

    # Las ventanas esperadas son las que de hecho se intentaron, no las 12 del config:
    # el primer barrido se corrió con --windows 6.
    vistas = {w for s in capturadas.values() for w in s}
    esperadas = len(vistas) or len(todas)

    filas, completas, parciales, vacias = [], [], [], []
    for k in cfg["keywords"]:
        n = len(capturadas.get(k["q"], set()))
        filas.append((k["q"], k.get("bloque", ""), n, esperadas))
        (completas if n >= esperadas else parciales if n else vacias).append(k)

    por_bloque: dict[str, list[int]] = collections.defaultdict(lambda: [0, 0])
    for q, b, n, e in filas:
        por_bloque[b][0] += n
        por_bloque[b][1] += e

    return {"filas": filas, "esperadas": esperadas, "por_bloque": dict(por_bloque),
            "completas": completas, "parciales": parciales, "vacias": vacias,
            "bloques_vacios": sorted(b for b, (a, _) in por_bloque.items() if a == 0),
            "total_kw": len(cfg["keywords"])}


def main() -> int:
    r = resumen()
    print(f"[cobertura] {len(r['completas'])} keywords completas · "
          f"{len(r['parciales'])} parciales · {len(r['vacias'])} sin nada "
          f"(de {r['total_kw']}, sobre {r['esperadas']} ventanas)")
    print("\n  bloque              capturado/esperado")
    for b, (a, e) in sorted(r["por_bloque"].items()):
        marca = "  ⛔" if a == 0 else ("  ⚠️" if a < e else "")
        print(f"  {b:18} {a:4}/{e:<4} ({100*a/e:3.0f}%){marca}")
    if r["vacias"]:
        print(f"\n  SIN DATOS ({len(r['vacias'])}):")
        for k in r["vacias"]:
            print(f"    · {k['q']}  [{k.get('bloque')}]")
    if r["bloques_vacios"]:
        print(f"\n  ⛔ Bloques enteros sin datos: {', '.join(r['bloques_vacios'])}.")
        print("     No reportes proporciones sobre esta base sin decir qué no se buscó.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
