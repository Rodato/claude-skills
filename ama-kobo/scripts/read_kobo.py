#!/usr/bin/env python3
"""
Lector CANÓNICO de CSV KoboToolbox para el pipeline AMA.

Concentra los gotchas de lectura que se reinventan en cada sesión (ver la skill
`ama-kobo`, reference `lectura-kobo.md`):

  1. Separador `;` y `dtype=str`  → preserva ceros a la izquierda en los IDs.
  2. Filtro por `_submission_time` (NO `start`) → la encuesta se abre en la
     mañana y se sube en la noche del mismo día.
  3. Columna de grado DUPLICADA (`col`, `col.1`, `col.2`, `col `) unificada con
     `bfill` → distintas escuelas usan distintas versiones del form.

No reemplaza a `validate_kobo.py` / `crosscheck.py` — es el "leé bien el CSV"
que va antes de cualquier análisis. Sin dependencias del repo (solo pandas).

Uso como módulo:
    from read_kobo import read_latest_kobo
    df = read_latest_kobo("data/kobo/*Leticia*.csv",
                          grade_col="¿En qué grado estás?",
                          date="2026-02-23")

Uso como CLI (imprime shape + columnas resueltas):
    python3 read_kobo.py "data/kobo/*Cobija*.csv" --date 2026-02-23
"""
from __future__ import annotations

import argparse
import glob
import os
import sys

import pandas as pd


def find_latest_csv(pattern: str) -> str:
    """CSV más reciente que matchea el patrón (por mtime). Sale si no hay ninguno."""
    matches = glob.glob(pattern)
    if not matches:
        print(f"ERROR: ningún CSV con el patrón: {pattern}", file=sys.stderr)
        sys.exit(1)
    matches.sort(key=os.path.getmtime, reverse=True)
    return matches[0]


def resolve_dup_column(df: pd.DataFrame, base_name: str) -> pd.DataFrame:
    """
    Une con bfill las columnas duplicadas que apuntan a la misma pregunta:
      base_name · base_name+'.1'/'.2'/… (pandas) · base_name+' ' (form con espacio).
    Devuelve el df con una sola columna `base_name` (primera no-nula por fila).
    """
    candidates = [
        c for c in df.columns
        if c == base_name
        or c.startswith(base_name + ".")
        or c.rstrip() == base_name
    ]
    if len(candidates) <= 1:
        return df
    merged = df[candidates].bfill(axis=1).iloc[:, 0]
    df = df.drop(columns=[c for c in candidates if c != base_name])
    df[base_name] = merged
    return df


def read_latest_kobo(
    pattern: str,
    grade_col: str | None = "¿En qué grado estás?",
    dup_cols: list[str] | None = None,
    date: str | None = None,
) -> pd.DataFrame:
    """
    Lee el CSV Kobo más reciente aplicando las 3 reglas canónicas.

    pattern    glob por ciudad, p.ej. "data/kobo/*Leticia*.csv".
    grade_col  columna de grado a unificar con bfill (None para omitir).
    dup_cols   otras columnas a unificar (nombre, colegio, id…). Opcional.
    date       filtro YYYY-MM-DD sobre `_submission_time` (None = todas).
    """
    path = find_latest_csv(pattern)
    df = pd.read_csv(path, sep=";", dtype=str)          # regla 1

    if date:                                            # regla 2
        if "_submission_time" not in df.columns:
            print("AVISO: sin columna _submission_time — no se filtra por fecha.",
                  file=sys.stderr)
        else:
            df = df[df["_submission_time"].str[:10] == date].copy()

    for col in ([grade_col] if grade_col else []) + (dup_cols or []):  # regla 3
        df = resolve_dup_column(df, col)

    return df.reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Lector canónico de CSV Kobo (AMA).")
    ap.add_argument("pattern", help='glob por ciudad, p.ej. "data/kobo/*Cobija*.csv"')
    ap.add_argument("--grade-col", default="¿En qué grado estás?")
    ap.add_argument("--date", default=None, help="filtro YYYY-MM-DD sobre _submission_time")
    args = ap.parse_args()

    df = read_latest_kobo(args.pattern, grade_col=args.grade_col, date=args.date)
    print(f"filas={len(df)}  columnas={len(df.columns)}")
    if args.grade_col in df.columns:
        vc = df[args.grade_col].value_counts(dropna=False).head(15)
        print(f"\n[{args.grade_col}] (top 15):")
        print(vc.to_string())


if __name__ == "__main__":
    main()
