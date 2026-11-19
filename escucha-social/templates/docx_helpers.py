# TEMPLATE de la skill `escucha-social`. Copiar a pipeline/docx_helpers.py (o pegar
# dentro de report.py, que es como viven hoy en los proyectos de referencia).
"""Helpers de python-docx para informes de escucha social.

Nada de esto es específico de un tema: es la capa de composición del .docx —estilo,
párrafos, viñetas, tablas, cifras, figuras— que se repite igual en cada escucha.

Lo que SÍ se escribe por proyecto son las secciones (`sec_portada`, `sec_metodo`,
`sec_medido`, `sec_lectura`, `sec_anexo`): ahí vive el encargo.
"""
from __future__ import annotations

from collections import Counter

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

BODY_FONT = "Calibri"


def style_doc(doc: Document) -> None:
    """Cuerpo 10,5 pt con interlineado 1,15 y encabezados en tinta casi negra."""
    n = doc.styles["Normal"]
    n.font.name = BODY_FONT
    n.font.size = Pt(10.5)
    n.paragraph_format.space_after = Pt(6)
    n.paragraph_format.line_spacing = 1.15
    for lvl, size in ((1, 15), (2, 12.5), (3, 11)):
        st = doc.styles[f"Heading {lvl}"]
        st.font.name = BODY_FONT
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = RGBColor(0x11, 0x11, 0x11)
        st.paragraph_format.space_before = Pt(14 if lvl == 1 else 10)
        st.paragraph_format.space_after = Pt(4)


def p(doc, text="", *, bold=False, italic=False, size=None, align=None, space_after=None):
    par = doc.add_paragraph()
    run = par.add_run(text)
    run.bold, run.italic = bold, italic
    if size:
        run.font.size = Pt(size)
    if align:
        par.alignment = align
    if space_after is not None:
        par.paragraph_format.space_after = Pt(space_after)
    return par


def bullet(doc, text, level=0):
    par = doc.add_paragraph(text, style="List Bullet")
    par.paragraph_format.left_indent = Inches(0.25 + 0.25 * level)
    par.paragraph_format.space_after = Pt(3)
    return par


def table(doc, headers, rows, widths=None):
    """Tabla con encabezado en negrita y columnas numéricas alineadas a la derecha."""
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.LEFT
    for i, h in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        run = cell.paragraphs[0].add_run(str(h))
        run.bold = True
        run.font.size = Pt(9.5)
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(str(v))
            run.font.size = Pt(9.5)
            if i > 0:
                cells[i].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def num(v) -> str:
    """Miles con punto, como se escribe en Colombia. Aislado en su propio helper porque
    aplicar .replace(",", ".") sobre una frase entera se come las comas de la prosa."""
    return format(int(v), ",d").replace(",", ".")


def pct(n, d):
    return f"{100.0 * n / d:.1f}%" if d else "—"


def figura(doc, path, pie: str, ancho=6.3):
    """Inserta un PNG con su pie. Las gráficas acompañan a la tabla, no la reemplazan."""
    if not path:
        return
    doc.add_picture(str(path), width=Inches(ancho))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    par = doc.add_paragraph()
    par.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = par.add_run(pie)
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    par.paragraph_format.space_after = Pt(10)


def cita(doc, texto: str, meta_texto: str, ancho_max=280):
    """Trino del anexo: cita sangrada + línea de autor/engagement en gris."""
    par = doc.add_paragraph()
    par.paragraph_format.left_indent = Inches(0.3)
    par.paragraph_format.space_after = Pt(2)
    run = par.add_run(f"«{' '.join(str(texto).split())[:ancho_max]}»")
    run.font.size = Pt(9.5)
    meta = doc.add_paragraph()
    meta.paragraph_format.left_indent = Inches(0.3)
    meta.paragraph_format.space_after = Pt(8)
    mrun = meta.add_run(meta_texto)
    mrun.font.size = Pt(8)
    mrun.font.color.rgb = RGBColor(0x66, 0x66, 0x66)


def multi_counter(series) -> Counter:
    """Cuenta valores de una columna multi-etiqueta ('a, b, c').

    Ojo: la suma supera el total de la base. Decilo en el pie de la gráfica."""
    c = Counter()
    for v in series.dropna():
        for x in str(v).split(","):
            x = x.strip()
            if x and x.lower() not in ("nan", ""):
                c[x] += 1
    return c


def bools(m, cols):
    """pandas relee los booleanos del CSV como 'True'/'true'/1.0 — y el string 'False'
    es truthy. Normalizar SIEMPRE antes de sumar."""
    for col in cols:
        if col in m.columns:
            m[col] = m[col].astype(str).str.lower().isin(["true", "1", "1.0"])
    return m
