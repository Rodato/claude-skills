#!/usr/bin/env python3
"""Saca un BORRADOR del CSV intermedio desde un .docx de preguntas.

Uso:
    python3 extraer_docx.py instrumento.docx > borrador.csv

Best-effort, no automágico: separa párrafos de tablas y arma filas candidatas
(preguntas, opciones, bloques de matriz), pero **no** infiere lógica de salto
en prosa ni decide con certeza qué es una opción vs. una instrucción. Revisá
y completá el CSV a mano antes de correr build_xlsform.py — ver
references/esquema_intermedio.md para las columnas esperadas.

No depende de python-docx: un .docx es un .zip con word/document.xml adentro,
y con stdlib (zipfile + xml.etree) alcanza para sacar texto y tablas.
"""
from __future__ import annotations

import csv
import sys
import zipfile
from xml.etree import ElementTree as ET

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

HEADER = ["seccion", "matriz", "pregunta", "tipo", "opciones", "lista",
          "ayuda", "requerido", "condicion", "nombre", "validacion"]


def para_text(p) -> str:
    return "".join(node.text or "" for node in p.iter(f"{W}t")).strip()


def table_rows(tbl) -> list[list[str]]:
    rows = []
    for tr in tbl.findall(f"{W}tr"):
        cells = []
        for tc in tr.findall(f"{W}tc"):
            text = " ".join(para_text(p) for p in tc.findall(f"{W}p")).strip()
            cells.append(text)
        rows.append(cells)
    return rows


def looks_like_blank(text: str) -> bool:
    stripped = text.replace("_", "").replace(" ", "")
    return text.count("_") >= 4 and len(stripped) < len(text) * 0.5


def main():
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)

    docx_path = sys.argv[1]
    with zipfile.ZipFile(docx_path) as z:
        xml = z.read("word/document.xml")
    root = ET.fromstring(xml)
    body = root.find(f"{W}body")

    out_rows = []
    pending_question = None  # dict acumulando pregunta + candidatas a opciones
    table_counter = 0

    def flush_pending():
        nonlocal pending_question
        if pending_question is None:
            return
        opciones = pending_question["opciones"]
        row = {k: "" for k in HEADER}
        row["pregunta"] = pending_question["pregunta"]
        if opciones:
            row["tipo"] = "unica"  # revisar a mano si en realidad es 'multiple'
            row["opciones"] = "|".join(opciones)
        # sin opciones: tipo queda vacío a propósito -> build_xlsform.py lo
        # infiere, o lo completás vos si la heurística no alcanza.
        out_rows.append(row)
        pending_question = None

    def emit_texto(pregunta_text: str):
        row = {k: "" for k in HEADER}
        row["pregunta"] = pregunta_text
        row["tipo"] = "texto"
        out_rows.append(row)

    for child in body:
        tag = child.tag
        if tag == f"{W}p":
            text = para_text(child)
            if not text:
                continue
            if "?" in text:
                # Puede venir "¿Pregunta? ___blank___" en un solo párrafo:
                # partimos en el último '?' y tratamos el resto como posible
                # blank de relleno, no como texto de la pregunta.
                idx = text.rfind("?")
                flush_pending()
                q_part, rest = text[:idx + 1].strip(), text[idx + 1:].strip()
                if rest and looks_like_blank(rest):
                    emit_texto(q_part)
                else:
                    pending_question = {"pregunta": q_part, "opciones": []}
                    if rest:
                        pending_question["opciones"].append(rest)
            elif pending_question is not None:
                if looks_like_blank(text):
                    # línea de "rellenar" -> probablemente texto libre, no opción
                    pregunta = pending_question["pregunta"]
                    pending_question = None
                    emit_texto(pregunta)
                else:
                    pending_question["opciones"].append(text)
            else:
                # texto suelto sin pregunta activa (instrucciones, títulos) -> nota candidata
                row = {k: "" for k in HEADER}
                row["pregunta"] = text
                row["tipo"] = "nota"
                row["requerido"] = "no"
                out_rows.append(row)
        elif tag == f"{W}tbl":
            flush_pending()
            table_counter += 1
            rows = table_rows(child)
            if len(rows) < 2:
                continue
            header_cells = rows[0]
            opciones = "|".join(c for c in header_cells[1:] if c)
            matriz_id = f"tabla_{table_counter}"
            for r in rows[1:]:
                if not r or not r[0]:
                    continue
                row = {k: "" for k in HEADER}
                row["matriz"] = matriz_id
                row["pregunta"] = r[0]
                row["tipo"] = "unica"
                row["opciones"] = opciones
                out_rows.append(row)
    flush_pending()

    writer = csv.DictWriter(sys.stdout, fieldnames=HEADER)
    writer.writeheader()
    for row in out_rows:
        writer.writerow(row)

    print(
        f"# {len(out_rows)} filas candidatas extraídas de {docx_path}. "
        f"Revisar a mano: secciones, tipos, matrices, lógica de salto en prosa.",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
