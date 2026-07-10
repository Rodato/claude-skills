#!/usr/bin/env python3
"""
Paleta y helper mínimo para replicar el estilo de gráficas del informe AMA.

Es una condensación fiel de `crear_grafica()` de
`Lineabase2026/tablero/lib.py` (la versión más general: 1-4 géneros, % dentro de
cada género, barras horizontales, 300 dpi). Copialo tal cual para arrancar un
frente nuevo (p. ej. el endline) y adaptá la fuente de datos.

Comentarios en español, código en inglés. Requiere: pandas, numpy, matplotlib.
"""

from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")  # backend sin GUI (apto Streamlit/servidor)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Paleta fija por género — NUNCA hardcodear otro hex fuera de este dict.
# El azul de "Hombre" (#6cd2ff) es además el acento AMA.
# --------------------------------------------------------------------------- #
COLORES = {
    "Hombre": "#6cd2ff",              # azul claro
    "Mujer": "#fc684f",               # coral
    "Persona no binaria": "#9b59b6",  # púrpura
    "Prefiero no decir": "#95a5a6",   # gris
}
ORDEN_SEXOS = ["Hombre", "Mujer", "Persona no binaria", "Prefiero no decir"]


def truncar(texto: str, n: int = 45) -> str:
    """Colapsa espacios dobles (los trae Kobo) y trunca a n chars con '...'."""
    import re

    texto = re.sub(r"\s+", " ", str(texto)).strip()
    return texto if len(texto) <= n else texto[: n - 3] + "..."


def barh_por_genero(dist: pd.DataFrame, titulo: str,
                    subtitulo: str | None = None):
    """Barras horizontales agrupadas por respuesta, una barra por género.

    `dist` es una tabla larga con columnas: sexo, respuesta, porcentaje
    (el % ya calculado DENTRO de cada género — suma 100% por género). Solo se
    dibujan los géneros con datos. Devuelve la figura matplotlib.
    """
    respuestas = sorted(dist["respuesta"].unique())
    sexos_con_datos = [s for s in ORDEN_SEXOS if s in dist["sexo"].values]
    n_sexos = len(sexos_con_datos)

    n_resp = len(respuestas)
    altura = max(4, n_resp * 0.5 + 1.8)  # altura dinámica
    fig, ax = plt.subplots(figsize=(10, altura))

    y_pos = np.arange(n_resp)
    if n_sexos == 1:
        bar_h, offsets = 0.5, [0]
    elif n_sexos == 2:
        bar_h, offsets = 0.38, [-0.19, 0.19]
    elif n_sexos == 3:
        bar_h, offsets = 0.26, [-0.26, 0, 0.26]
    else:
        bar_h, offsets = 0.20, [-0.30, -0.10, 0.10, 0.30]

    all_bars, all_datos = [], []
    for i, sexo in enumerate(sexos_con_datos):
        datos = []
        for resp in respuestas:
            val = dist[(dist["sexo"] == sexo) & (dist["respuesta"] == resp)]["porcentaje"]
            datos.append(float(val.values[0]) if len(val) else 0.0)
        bars = ax.barh(y_pos + offsets[i], datos, bar_h, label=sexo,
                       color=COLORES.get(sexo, "#888888"), edgecolor="white")
        all_bars.append(bars)
        all_datos.append(datos)

    # Etiqueta de % al lado de cada barra (OJO: > 0, no `if val` — NaN es truthy)
    fontsize_val = 8 if n_sexos <= 2 else 7
    for bars, datos in zip(all_bars, all_datos):
        for bar, val in zip(bars, datos):
            if val > 0:
                ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                        f"{val:.1f}%", va="center", fontsize=fontsize_val, color="#333333")

    ax.set_yticks(y_pos)
    ax.set_yticklabels([truncar(r) for r in respuestas], fontsize=9)
    ax.set_xlabel("Porcentaje dentro de cada género (%)", fontsize=10)
    ax.set_title(titulo, fontsize=12, fontweight="bold", pad=12)

    max_val = max((max(d) for d in all_datos if d), default=0)
    ax.set_xlim(0, max_val * 1.25 if max_val > 0 else 10)
    if n_sexos > 1:
        ax.legend(loc="lower right", fontsize=8)
    ax.xaxis.grid(True, linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)
    ax.invert_yaxis()  # primera respuesta arriba
    fig.tight_layout()

    # Nota de contexto al pie (filtros aplicados), sin colisionar con el título
    if subtitulo:
        fig.subplots_adjust(bottom=0.02 + 0.6 / fig.get_figheight())
        fig.text(0.5, 0.012, subtitulo, ha="center", va="bottom",
                 fontsize=8.5, color="#666666", style="italic")
    return fig


def figura_a_png(fig, dpi: int = 300) -> bytes:
    """Serializa la figura a PNG en memoria. 300 dpi = informe; 130 = display web."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    return buf.getvalue()


def distribucion_por_sexo(df: pd.DataFrame, variable: str,
                          col_sexo: str = "DEM_11",
                          sexos: list[str] | None = None) -> pd.DataFrame:
    """Tabla larga [sexo, respuesta, n, porcentaje] con % DENTRO de cada género.

    Réplica de `variables_encuesta_informe.calcular_distribucion` para variables
    de opción única. Para multi-respuesta (comas o espacios) hay que descomponer
    antes — ver skill hermana `ama-kobo`.
    """
    sexos = sexos or ORDEN_SEXOS
    sub = df[df[col_sexo].isin(sexos) & df[variable].notna()]
    tabla = sub.groupby([col_sexo, variable]).size().reset_index(name="n")
    totales = sub.groupby([col_sexo]).size().reset_index(name="total")
    tabla = tabla.merge(totales, on=col_sexo)
    tabla["porcentaje"] = (tabla["n"] / tabla["total"] * 100).round(1)
    return tabla.rename(columns={col_sexo: "sexo", variable: "respuesta"}).drop(columns="total")


if __name__ == "__main__":
    # Demo mínima con datos sintéticos.
    demo = pd.DataFrame({
        "sexo": ["Hombre", "Hombre", "Mujer", "Mujer", "Persona no binaria"],
        "respuesta": ["De acuerdo", "En desacuerdo", "De acuerdo", "En desacuerdo", "De acuerdo"],
        "porcentaje": [40.0, 60.0, 33.0, 67.0, 100.0],
    })
    fig = barh_por_genero(demo, "Demo · afirmación de ejemplo",
                          subtitulo="Grupo Control · ambas ciudades")
    with open("demo_barh_por_genero.png", "wb") as f:
        f.write(figura_a_png(fig, dpi=300))
    print("Escrito: demo_barh_por_genero.png")
