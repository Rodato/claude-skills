# TEMPLATE de la skill `escucha-social`. Copiar a pipeline/qa.py.
# Los EJES son de ejemplo (un libro de códigos de 7 ejes sobre espacio cívico): reemplazalos por el libro de códigos
# del proyecto. La maquinaria —muestra estratificada, libro de Excel con
# desplegables, κ de Cohen, κ por categoría en multi-etiqueta— es reusable tal cual.
"""Control de calidad de la codificación: doble codificación humana del 10% y concordancia.

Hay briefs que lo exigen sin matices: doble codificación de una submuestra del 10% y reporte
de concordancia, y si se usa preclasificación asistida por IA, la validación humana de esa
submuestra no es negociable.

Este módulo hace las dos mitades:

    python -m pipeline.qa --export         # arma el libro para codificar a mano
    python -m pipeline.qa --concordancia data/reports/qa/qa_codificado.xlsx

El libro que se entrega a la persona NO trae los códigos de la máquina: si los trajera, el
ejercicio mediría obediencia y no concordancia. Los códigos automáticos quedan aparte, en
data/processed/qa_maquina.csv, y solo se cruzan al calcular.

La muestra se estratifica por `posicion_enunciado` —el eje 6, donde se concentran los errores
de codificación— y se fija con `--seed` para que sea reproducible y auditable.
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path

import pandas as pd

from pipeline.classify import (
    COMB, DIMENSION, INTERSECCIONAL, NIVEL, POSICION, RESTRICCION,
    ACTOR_RESTRICTOR, TERRITORIOS,
)
from pipeline.normalize import PROCESSED, ROOT

QA_DIR = ROOT / "data" / "reports" / "qa"
MAQUINA_CSV = PROCESSED / "qa_maquina.csv"

# Campos que codifica la persona. `multi` marca los que admiten varios valores separados
# por coma; el resto es valor único y lleva lista desplegable en el Excel.
EJES = [
    ("relevante",               ["si", "no"],      False, "¿Habla del espacio cívico, de quien se organiza, o de las condiciones para hacerlo?"),
    ("territorio",              TERRITORIOS,       True,  "Solo si el trino ancla el hecho en ese lugar. Si es nacional sin anclaje: nacional"),
    ("dimension_afectada",      DIMENSION,         True,  "EJE 1 · Qué capacidad del actor social está en juego"),
    ("tipo_restriccion",        RESTRICCION,       True,  "EJE 2 · La forma concreta que toma la restricción. Si no hay ninguna: ninguna"),
    ("actor_restrictor",        ACTOR_RESTRICTOR,  True,  "EJE 3 · Solo quien el trino señala EXPLÍCITAMENTE"),
    ("comb",                    COMB,              True,  "EJE 4 · capacidad=recursos propios · oportunidad=condiciones externas · motivacion=voluntad, miedo, legitimidad"),
    ("nivel_afectacion",        NIVEL,             False, "EJE 5 · A quién alcanza lo que el trino describe"),
    ("posicion_enunciado",      POSICION,          False, "EJE 6 · QUÉ HACE EL AUTOR. Ejercer un ataque (deslegitimacion) NO es denunciarlo (denuncia)"),
    ("marcador_interseccional", INTERSECCIONAL,    True,  "EJE 7 · Solo si es EXPLÍCITO en el trino. No lo infieras del tema general"),
]


def _cargar_base(min_conf: float) -> pd.DataFrame:
    """La misma base de análisis que va al informe: es sobre esa población que hay que
    reportar concordancia, no sobre el crudo."""
    from pipeline.report import build_dataset
    base, _ = build_dataset(min_conf)
    return base


def muestrear(base: pd.DataFrame, frac: float, seed: int) -> pd.DataFrame:
    """Muestra estratificada por posición del enunciado, con mínimo 2 por estrato.

    Estratificar importa: `deslegitimacion` es una minoría del corpus y es justo donde el
    codificador automático se equivoca. Una muestra simple al 10% podría traer dos o tres
    casos y no permitiría decir nada sobre el eje que más pesa."""
    rng = random.Random(seed)
    objetivo = max(1, round(len(base) * frac))
    partes = []
    for val, g in base.groupby("posicion_enunciado"):
        n = max(2, round(len(g) * frac)) if len(g) >= 2 else len(g)
        partes.append(g.sample(n=min(n, len(g)), random_state=seed))
    m = pd.concat(partes)
    # Si la estratificación se quedó corta frente al 10%, completar al azar con el resto.
    if len(m) < objetivo:
        resto = base[~base["id"].isin(m["id"])]
        if len(resto):
            m = pd.concat([m, resto.sample(n=min(objetivo - len(m), len(resto)),
                                           random_state=seed)])
    return m.sample(frac=1, random_state=seed).reset_index(drop=True)  # desordenar


def exportar(frac: float, seed: int, min_conf: float) -> int:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation

    base = _cargar_base(min_conf)
    if base.empty:
        print("[qa] la base de análisis está vacía; clasificá primero")
        return 1
    m = muestrear(base, frac, seed)

    QA_DIR.mkdir(parents=True, exist_ok=True)
    # 1) Los códigos de la máquina, APARTE. No van al libro del codificador.
    cols_maq = ["id"] + [e[0] for e in EJES]
    maq = m[[c for c in cols_maq if c in m.columns]].copy()
    maq["relevante"] = maq["relevante"].map(lambda v: "si" if v else "no")
    maq.to_csv(MAQUINA_CSV, index=False)

    # 2) El libro para codificar a mano.
    wb = Workbook()
    ws = wb.active
    ws.title = "codificar"
    encabezados = ["id", "fecha", "autor", "url", "texto"] + [e[0] for e in EJES]
    ws.append(encabezados)
    for i, h in enumerate(encabezados, 1):
        c = ws.cell(row=1, column=i)
        c.font = Font(bold=True, size=10)
        c.fill = PatternFill("solid", fgColor="E8E7E3")
        c.alignment = Alignment(vertical="center", wrap_text=True)
    for _, r in m.iterrows():
        fecha = str(r.get("created_at") or "")[:10]
        ws.append([str(r["id"]), fecha, r.get("author"), r.get("url"),
                   " ".join(str(r.get("text") or "").split())])
    anchos = {"A": 20, "B": 11, "C": 16, "D": 30, "E": 90}
    for col, w in anchos.items():
        ws.column_dimensions[col].width = w
    for i in range(len(anchos) + 1, len(encabezados) + 1):
        ws.column_dimensions[ws.cell(row=1, column=i).column_letter].width = 22
    ws.freeze_panes = "F2"
    for row in ws.iter_rows(min_row=2, min_col=5, max_col=5):
        row[0].alignment = Alignment(wrap_text=True, vertical="top")

    # Desplegables solo en los ejes de valor único: en los multi-etiqueta la validación
    # impediría escribir "genero, territorial", que es justo lo que el libro de códigos pide.
    n = ws.max_row
    for j, (campo, valores, multi, _) in enumerate(EJES, start=len(anchos) + 1):
        if multi:
            continue
        letra = ws.cell(row=1, column=j).column_letter
        dv = DataValidation(type="list", formula1='"' + ",".join(valores) + '"',
                            allow_blank=True, showDropDown=False)
        ws.add_data_validation(dv)
        dv.add(f"{letra}2:{letra}{n}")

    # 3) Hoja de instrucciones: el libro de códigos viaja con el archivo.
    ins = wb.create_sheet("cómo codificar")
    ins.column_dimensions["A"].width = 26
    ins.column_dimensions["B"].width = 14
    ins.column_dimensions["C"].width = 100
    ins.append(["Campo", "¿Varios?", "Qué codificar · valores admitidos"])
    for c in ins[1]:
        c.font = Font(bold=True, size=10)
        c.fill = PatternFill("solid", fgColor="E8E7E3")
    for campo, valores, multi, ayuda in EJES:
        ins.append([campo, "sí, separá con coma" if multi else "uno solo",
                    f"{ayuda}\nValores: {', '.join(valores)}"])
    for row in ins.iter_rows(min_row=2):
        row[2].alignment = Alignment(wrap_text=True, vertical="top")
        row[1].alignment = Alignment(wrap_text=True, vertical="top")
    ins.append([])
    ins.append(["REGLA CRÍTICA", "", "EJE 6 · Ejercer un ataque no es denunciarlo. "
                "«Rechazamos los señalamientos contra X» es denuncia, NO deslegitimacion. "
                "El autor que deslegitima es quien ataca, no quien reporta el ataque."])
    ins.append(["", "", "EFECTO INHIBITORIO · Solo si alguien YA dejó de hacer algo. "
                "Denunciar un riesgo o contar un asesinato es denuncia, no repliegue."])
    for row in ins.iter_rows(min_row=ins.max_row - 1):
        row[2].alignment = Alignment(wrap_text=True, vertical="top")
        row[0].font = Font(bold=True)

    out = QA_DIR / f"qa_para_codificar_seed{seed}.xlsx"
    wb.save(out)
    print(f"[qa] muestra de {len(m)} trinos ({100 * len(m) / len(base):.1f}% de {len(base)}) "
          f"· estratificada por posicion_enunciado · seed={seed}")
    print(f"[qa] → {out}")
    print(f"[qa] → {MAQUINA_CSV.name} (códigos de la máquina, NO se entregan al codificador)")
    print("[qa] al recibirlo codificado: python -m pipeline.qa --concordancia <archivo>")
    return 0


# --- concordancia -------------------------------------------------------------
def kappa(a: list, b: list) -> tuple[float, float]:
    """Cohen's kappa y acuerdo observado para dos series de etiquetas únicas."""
    n = len(a)
    if not n:
        return float("nan"), float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    cats = set(a) | set(b)
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    k = (po - pe) / (1 - pe) if pe < 1 else 1.0
    return k, po


def _set(v) -> set[str]:
    return {x.strip().lower() for x in str(v or "").split(",") if x.strip()}


def concordancia(path: Path, seed: int) -> int:
    if not MAQUINA_CSV.exists():
        print(f"[qa] falta {MAQUINA_CSV}; corré primero --export")
        return 1
    hum = pd.read_excel(path, sheet_name="codificar", dtype={"id": str})
    maq = pd.read_csv(MAQUINA_CSV, dtype={"id": str})
    m = hum.merge(maq, on="id", how="inner", suffixes=("_h", "_m"))
    if m.empty:
        print("[qa] ningún id en común entre el archivo humano y los códigos de máquina")
        return 1

    lineas = [f"# Concordancia humano · máquina\n",
              f"Submuestra de **{len(m)} trinos** codificados a doble ciego. "
              f"Semilla `{seed}`. Archivo: `{path.name}`.\n",
              "κ de Cohen sobre los ejes de valor único; en los multi-etiqueta, κ promedio "
              "por categoría y Jaccard medio. Lectura convencional: κ < 0,40 pobre · "
              "0,40–0,60 moderada · 0,60–0,80 sustancial · > 0,80 casi perfecta.\n",
              "| Eje | Tipo | κ | Acuerdo | Lectura |", "|---|---|---|---|---|"]
    print(f"\n[qa] concordancia sobre {len(m)} trinos codificados\n")
    print(f"  {'eje':26} {'κ':>7} {'acuerdo':>9}")
    flojos = []
    for campo, valores, multi, _ in EJES:
        ch, cm = f"{campo}_h", f"{campo}_m"
        if ch not in m.columns or cm not in m.columns:
            continue
        sub = m[m[ch].notna() & (m[ch].astype(str).str.strip() != "")]
        if sub.empty:
            continue
        if multi:
            ks, jac = [], []
            for cat in valores:
                a = [cat in _set(v) for v in sub[ch]]
                b = [cat in _set(v) for v in sub[cm]]
                if any(a) or any(b):
                    ks.append(kappa(a, b)[0])
            for x, y in zip(sub[ch], sub[cm]):
                A, B = _set(x), _set(y)
                jac.append(len(A & B) / len(A | B) if (A | B) else 1.0)
            k = sum(ks) / len(ks) if ks else float("nan")
            ac = sum(jac) / len(jac)
            tipo = "multi"
        else:
            a = [str(v).strip().lower() for v in sub[ch]]
            b = [str(v).strip().lower() for v in sub[cm]]
            k, ac = kappa(a, b)
            tipo = "único"
        lectura = ("casi perfecta" if k > 0.80 else "sustancial" if k > 0.60 else
                   "moderada" if k > 0.40 else "POBRE — revisar el prompt")
        if k <= 0.60:
            flojos.append((campo, k))
        print(f"  {campo:26} {k:7.3f} {ac:8.1%}   {lectura}")
        lineas.append(f"| `{campo}` | {tipo} | {k:.3f} | {ac:.1%} | {lectura} |")

    lineas.append("")
    if flojos:
        lineas.append("## Ejes que no alcanzan concordancia sustancial\n")
        for campo, k in flojos:
            lineas.append(f"- **`{campo}`** (κ = {k:.3f}). Antes de publicar proporciones de "
                          f"este eje: revisar su definición en el `SYSTEM_PROMPT`, o reportarlo "
                          f"con la advertencia de que la codificación no es estable.")
        print(f"\n[qa] ⚠️ {len(flojos)} eje(s) por debajo de κ=0,60. No publiques sus "
              f"proporciones sin advertirlo.")
    else:
        lineas.append("Todos los ejes alcanzan concordancia sustancial o mejor.\n")
        print("\n[qa] ✓ todos los ejes en concordancia sustancial o mejor")

    QA_DIR.mkdir(parents=True, exist_ok=True)
    out = QA_DIR / "concordancia.md"
    out.write_text("\n".join(lineas), encoding="utf-8")
    print(f"[qa] → {out}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Doble codificación y concordancia (brief §5)")
    ap.add_argument("--export", action="store_true", help="Armar el libro para codificar")
    ap.add_argument("--concordancia", type=Path, help="Calcular κ contra el libro codificado")
    ap.add_argument("--frac", type=float, default=0.10, help="Fracción de la base (brief: 10%%)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--min-confianza", type=float, default=0.5)
    args = ap.parse_args()
    if args.concordancia:
        return concordancia(args.concordancia, args.seed)
    if args.export:
        return exportar(args.frac, args.seed, args.min_confianza)
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
