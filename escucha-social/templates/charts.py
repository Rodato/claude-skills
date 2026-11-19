# TEMPLATE de la skill `escucha-social`. Copiar a pipeline/charts.py.
# Las 6 figuras son las de una escucha de espacio cívico; la paleta y _setup/_bare/_barras_h son reusables
# tal cual. Ajustar CAMBIO_GOBIERNO a la bisagra del proyecto (o quitar la línea).
"""Gráficas del reporte de una escucha de espacio cívico. PNG a 300 dpi para incrustar en el .docx.

Paleta heredada de una escucha anterior, validada con el validador de la skill dataviz (modo light,
superficie clara): azul y rojo como par divergente — CVD ΔE 21.6, visión normal ΔE 32.3.
Una sola serie usa un solo tono; nunca se cicla color por barra.

Reglas que se respetan acá: marcas delgadas, ejes y grilla recesivos, etiquetas directas
selectivas, texto en tinta y nunca en el color de la serie, leyenda siempre que haya dos
series, y ningún eje doble.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# --- tokens ---
BLUE, RED, GRAY = "#2a78d6", "#e34948", "#c9c8c3"
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8985"
GRID, SURFACE = "#e8e7e3", "#ffffff"
FONTS = ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"]
DPI = 300

# Posesión de De la Espriella: la bisagra analítica de toda la escucha.
CAMBIO_GOBIERNO = date(2026, 8, 7)


def _setup():
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": FONTS, "font.size": 8.5,
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "text.color": INK, "axes.labelcolor": INK2,
        "xtick.color": MUTED, "ytick.color": INK2,
        "axes.edgecolor": GRID, "axes.linewidth": 0.8,
        "xtick.major.size": 0, "ytick.major.size": 0,
        "figure.dpi": DPI, "savefig.dpi": DPI, "savefig.bbox": "tight",
        "savefig.facecolor": SURFACE, "savefig.pad_inches": 0.06,
    })


def _bare(ax, xgrid=True, enteros=False):
    for s in ("top", "right", "left", "bottom"):
        ax.spines[s].set_visible(False)
    if xgrid:
        ax.xaxis.grid(True, color=GRID, linewidth=0.7)
        ax.set_axisbelow(True)
    if enteros:
        ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))


def _save(fig, out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    return out


def _title(ax, titulo: str, subtitulo: str | None = None):
    ax.set_title(titulo, loc="left", fontsize=10, fontweight="bold", color=INK,
                 pad=20 if subtitulo else 8)
    if subtitulo:
        ax.text(0, 1.02, subtitulo, transform=ax.transAxes, fontsize=8, color=INK2, va="bottom")


def _barras_h(pares, out: Path, titulo: str, subtitulo: str, color=BLUE, unidad="trinos"):
    """Barras horizontales de una sola serie, ordenadas de mayor a menor."""
    _setup()
    pares = [(k, v) for k, v in pares if v]
    if not pares:
        return None
    pares = sorted(pares, key=lambda kv: kv[1])
    etiquetas = [k for k, _ in pares]
    valores = [v for _, v in pares]
    fig, ax = plt.subplots(figsize=(7.2, max(2.0, 0.34 * len(pares) + 1.1)))
    ax.barh(etiquetas, valores, color=color, height=0.62)
    _bare(ax, enteros=True)
    tope = max(valores)
    for y, v in enumerate(valores):
        ax.text(v + tope * 0.015, y, f"{v:,}".replace(",", "."),
                va="center", fontsize=8, color=INK2)
    ax.set_xlim(0, tope * 1.12)
    ax.set_xlabel(unidad, fontsize=8)
    _title(ax, titulo, subtitulo)
    return _save(fig, out)


# --- 1. volumen mensual, con la bisagra del cambio de gobierno ----------------
def fig_volumen(pares, out: Path) -> Path:
    """pares: [(date_del_mes, n), ...] ya ordenado."""
    _setup()
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    xs = [d for d, _ in pares]
    ys = [n for _, n in pares]
    ax.plot(xs, ys, color=BLUE, linewidth=1.8, marker="o", markersize=3.2)
    _bare(ax, xgrid=False)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True, nbins=5))
    ax.yaxis.grid(True, color=GRID, linewidth=0.7)
    ax.set_axisbelow(True)
    if xs and min(xs) <= CAMBIO_GOBIERNO <= max(xs):
        ax.axvline(CAMBIO_GOBIERNO, color=MUTED, linewidth=0.9, linestyle=(0, (4, 3)))
        ax.text(CAMBIO_GOBIERNO, ax.get_ylim()[1] * 0.98, "  7 ago: cambio de gobierno",
                fontsize=7.5, color=INK2, va="top", ha="left")
    if ys:
        imax = ys.index(max(ys))
        ax.annotate(f"{max(ys):,}".replace(",", "."), (xs[imax], ys[imax]),
                    textcoords="offset points", xytext=(0, 7), ha="center",
                    fontsize=8, color=INK2)
    ax.set_ylabel("trinos", fontsize=8)
    _title(ax, "Volumen mensual de la conversación",
           "Base de análisis: trinos colombianos relevantes")
    fig.autofmt_xdate(rotation=0, ha="center")
    return _save(fig, out)


# --- 2. encuadres, agrupados por si el espacio se usa o se disputa ------------
def fig_encuadre(pares_uso, pares_disputa, out: Path) -> Path:
    """Dos grupos con color distinto: usar el espacio y disputarlo son cosas diferentes."""
    _setup()
    datos = ([(k, v, BLUE) for k, v in pares_uso if v] +
             [(k, v, RED) for k, v in pares_disputa if v])
    if not datos:
        return None
    datos = sorted(datos, key=lambda t: t[1])
    fig, ax = plt.subplots(figsize=(7.2, max(2.2, 0.34 * len(datos) + 1.3)))
    ax.barh([d[0] for d in datos], [d[1] for d in datos],
            color=[d[2] for d in datos], height=0.62)
    _bare(ax, enteros=True)
    tope = max(d[1] for d in datos)
    for y, d in enumerate(datos):
        ax.text(d[1] + tope * 0.015, y, f"{d[1]:,}".replace(",", "."),
                va="center", fontsize=8, color=INK2)
    ax.set_xlim(0, tope * 1.12)
    ax.set_xlabel("trinos", fontsize=8)
    handles = [plt.Rectangle((0, 0), 1, 1, color=BLUE),
               plt.Rectangle((0, 0), 1, 1, color=RED)]
    ax.legend(handles, ["El espacio en uso", "El espacio en disputa"],
              frameon=False, fontsize=8, loc="lower right")
    _title(ax, "De qué se habla cuando se habla de espacio cívico",
           "Encuadre dominante de cada trino")
    return _save(fig, out)


# --- 3. postura por tipo de actor (divergente) --------------------------------
def fig_postura_actor(filas, out: Path) -> Path:
    """filas: [(actor, n_amplia, n_restringe), ...]. Diverge desde el cero."""
    _setup()
    filas = [f for f in filas if (f[1] + f[2])]
    if not filas:
        return None
    filas = sorted(filas, key=lambda f: f[1] + f[2])
    etiquetas = [f[0] for f in filas]
    amplia = [f[1] for f in filas]
    restringe = [-f[2] for f in filas]
    fig, ax = plt.subplots(figsize=(7.2, max(2.2, 0.36 * len(filas) + 1.2)))
    ax.barh(etiquetas, amplia, color=BLUE, height=0.62, label="Amplía el espacio")
    ax.barh(etiquetas, restringe, color=RED, height=0.62, label="Lo restringe")
    _bare(ax)
    ax.axvline(0, color=MUTED, linewidth=0.8)
    for y, (a, r) in enumerate(zip(amplia, restringe)):
        if a:
            ax.text(a, y, f" {a}", va="center", ha="left", fontsize=7.5, color=INK2)
        if r:
            ax.text(r, y, f"{-r} ", va="center", ha="right", fontsize=7.5, color=INK2)
    lim = max(max(amplia, default=0), max((-r for r in restringe), default=0)) * 1.25
    ax.set_xlim(-lim, lim)
    ax.set_xticks([])
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    _title(ax, "Quién amplía y quién restringe el espacio",
           "Trinos por tipo de actor que los publica")
    return _save(fig, out)


# --- 4. quién aparece restringiendo -------------------------------------------
def fig_restrictores(pares, out: Path) -> Path:
    return _barras_h(pares, out, "Quién aparece señalado como restrictor",
                     "Actor que el trino identifica limitando el espacio cívico", color=RED)


# --- 5. libertades en juego ---------------------------------------------------
def fig_libertades(pares, out: Path) -> Path:
    return _barras_h(pares, out, "Qué libertades están en juego",
                     "Un trino puede poner más de una en juego", color=BLUE)


# --- 6. antes y después del cambio de gobierno --------------------------------
def fig_antes_despues(filas, out: Path) -> Path:
    """filas: [(etiqueta, pct_antes, pct_despues), ...]. Dos series → leyenda obligatoria."""
    _setup()
    if not filas:
        return None
    filas = sorted(filas, key=lambda f: f[2])
    etiquetas = [f[0] for f in filas]
    ys = range(len(filas))
    fig, ax = plt.subplots(figsize=(7.2, max(2.2, 0.42 * len(filas) + 1.3)))
    h = 0.34
    ax.barh([y + h / 2 for y in ys], [f[1] for f in filas], height=h,
            color=GRAY, label="Antes del 7 de agosto")
    ax.barh([y - h / 2 for y in ys], [f[2] for f in filas], height=h,
            color=RED, label="Después del 7 de agosto")
    ax.set_yticks(list(ys))
    ax.set_yticklabels(etiquetas)
    _bare(ax)
    tope = max(max(f[1], f[2]) for f in filas)
    for y, f in zip(ys, filas):
        ax.text(f[1] + tope * 0.015, y + h / 2, f"{f[1]:.0f}%", va="center",
                fontsize=7.5, color=INK2)
        ax.text(f[2] + tope * 0.015, y - h / 2, f"{f[2]:.0f}%", va="center",
                fontsize=7.5, color=INK2)
    ax.set_xlim(0, tope * 1.15)
    ax.set_xlabel("% de los trinos del período", fontsize=8)
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    _title(ax, "Cómo cambió el encuadre con el cambio de gobierno",
           "Participación de cada encuadre dentro de su propio período")
    return _save(fig, out)
