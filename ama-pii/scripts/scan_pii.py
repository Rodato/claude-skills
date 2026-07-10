#!/usr/bin/env python3
"""Escáner de PII para artefactos de datos del programa AMA.

Corazón de la skill `ama-pii`: un guard ejecutable que se corre ANTES de cualquier
`git add`/push/deploy de un CSV que toque datos de AMA (encuestas de menores 14-19).
Revisa cada columna en busca de identificadores directos y sale con código != 0 si
encuentra PII probable, para poder encadenarlo como pre-push gate.

Detecta, por columna:
  - email        celdas que matchean un correo (regex)
  - telefono     secuencias de 7-15 dígitos tolerando '+', espacios, guiones y puntos
  - documento    secuencias largas de dígitos (cédula/DNI/tarjeta de identidad)
  - nombre-col   nombres de columna sospechosos (nombre, documento, cédula, dni,
                 teléfono, celular, whatsapp, correo, email, dirección, fecha_nac…),
                 insensible a mayúsculas y acentos, más los códigos PII conocidos de
                 AMA (DEM_01, ADM_02, Nombre_completo, N_mero_de_celular_WhatsApp…).

Uso:
    python3 scan_pii.py <archivo.csv | directorio> [...]
    python3 scan_pii.py data/encuesta_anon.csv
    python3 scan_pii.py data/            # escanea todos los .csv recursivamente

Exit codes:
    0  sin PII evidente
    1  PII probable encontrada (no commitear/deploy)
    2  error de uso (path inexistente, sin CSVs)

Sólo stdlib (no requiere pandas): así corre como gate en cualquier entorno.
Comentarios en español, código en inglés.
"""
from __future__ import annotations

import csv
import re
import sys
import unicodedata
from pathlib import Path

# ── Regex de detección ────────────────────────────────────────────────────────

# Correo: parte local + '@' + dominio con al menos un punto.
RE_EMAIL = re.compile(r"[\w.+\-]+@[\w\-]+\.[\w.\-]+")

# Candidato a teléfono: empieza con dígito (o '+dígito'), seguido de dígitos y
# separadores (espacio, punto, guion). Luego se cuentan los dígitos reales.
RE_PHONE_CAND = re.compile(r"\+?\d[\d .\-]{5,}\d")

# Corrida pura de dígitos (sin separadores) — candidata a documento.
RE_DIGIT_RUN = re.compile(r"\d{7,}")

# Fecha ISO (2026-06-15, 2026/6/1): un candidato a teléfono que en realidad es una
# fecha. Evita el falso positivo típico de columnas de timestamp (_submission_time).
RE_DATEISH = re.compile(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$")

# ── Vocabulario de nombres de columna ─────────────────────────────────────────

# Tokens fuertes: si aparecen como palabra dentro del nombre de la columna,
# es PII directa. (Ya normalizados: sin acentos, minúsculas.)
NAME_TOKENS = {
    "nombre", "nombres", "apellido", "apellidos",
    "documento", "cedula", "dni", "identidad", "tarjeta", "pasaporte",
    "carnet",  # nota: NO se incluye "ci" (2 letras) — matchea partes de palabras
               # mangleadas por Kobo (exper_ci_n) y da falsos positivos.
    "telefono", "celular", "whatsapp", "movil", "phone",
    "correo", "email", "mail",
    "direccion", "domicilio", "residencia",
    "nacimiento", "cumpleanos", "birthdate",
}

# Subcadenas para nombres compuestos sin separadores ("nombrecompleto").
NAME_SUBSTRINGS = (
    "nombrecompleto", "numerodecelular", "numerodedocumento", "numerodocumento",
    "celularwhatsapp", "fechanacimiento", "fechanac", "fechadenacimiento",
)

# Códigos PII conocidos del dataset AMA (ver anonimizar.py / coverage.py).
AMA_PII_CODES = {
    "adm_01", "adm_02", "adm_03", "adm_04",
    "dem_01", "dem_02", "dem_03", "dem_04",
    "dem_05", "dem_06", "dem_07", "dem_08", "dem_09", "dem_15",
    "meta_01", "meta_02",
    "nombre_completo", "n_mero_de_celular_whatsapp",
}

# Cuasi-identificadores: no son PII directa, pero re-identifican si el destino es
# público. No hacen fallar el gate; sólo se avisan (ver checklist paso 3).
QUASI_TOKENS = {
    "edad", "etnia", "estrato", "socioeconomico", "nivelsocioeconomico",
    "lengua", "idioma", "religion", "orientacion",
}


# ── Utilidades ────────────────────────────────────────────────────────────────

def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def normalize_header(name: str) -> tuple[str, list[str], str]:
    """Devuelve (normalizado_con_espacios, tokens, normalizado_sin_separadores)."""
    base = strip_accents(name).lower().strip()
    spaced = re.sub(r"[^a-z0-9]+", " ", base).strip()
    tokens = spaced.split()
    joined = re.sub(r"[^a-z0-9]+", "", base)
    return spaced, tokens, joined


def classify_header(name: str) -> str | None:
    """Etiqueta el nombre de columna: 'PII', 'QUASI' o None."""
    spaced, tokens, joined = normalize_header(name)
    tokenset = set(tokens)
    # Código AMA exacto (dem_03, adm_02, nombre_completo…).
    if joined in AMA_PII_CODES or spaced.replace(" ", "_") in AMA_PII_CODES:
        return "PII"
    if tokenset & NAME_TOKENS:
        return "PII"
    if any(sub in joined for sub in NAME_SUBSTRINGS):
        return "PII"
    if tokenset & QUASI_TOKENS:
        return "QUASI"
    return None


def count_phone(cell: str) -> bool:
    """True si la celda contiene una secuencia de 7-15 dígitos con forma de teléfono."""
    for m in RE_PHONE_CAND.finditer(cell):
        tok = m.group().strip()
        if RE_DATEISH.match(tok):   # es una fecha ISO, no un teléfono
            continue
        digits = re.sub(r"\D", "", tok)
        if 7 <= len(digits) <= 15:
            return True
    return False


def count_document(cell: str) -> bool:
    """True si la celda contiene una corrida pura de >=7 dígitos (documento/DNI)."""
    for m in RE_DIGIT_RUN.finditer(cell):
        if 7 <= len(m.group()) <= 20:
            return True
    return False


def sniff_delimiter(sample: str) -> str:
    """Detecta ';' o ',' mirando la primera línea (Kobo usa ';', otros ',')."""
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,\t")
        if dialect.delimiter in ";,\t":
            return dialect.delimiter
    except csv.Error:
        pass
    first = sample.splitlines()[0] if sample else ""
    return ";" if first.count(";") >= first.count(",") and ";" in first else ","


# ── Escaneo de un archivo ─────────────────────────────────────────────────────

class ColumnStat:
    __slots__ = ("name", "label", "nonempty", "email", "phone", "doc")

    def __init__(self, name: str, label: str | None) -> None:
        self.name = name
        self.label = label            # 'PII' | 'QUASI' | None
        self.nonempty = 0
        self.email = 0
        self.phone = 0
        self.doc = 0

    @property
    def has_content_pii(self) -> bool:
        return self.email > 0 or self.phone > 0 or self.doc > 0


def scan_file(path: Path) -> tuple[list[ColumnStat], int, str]:
    """Escanea un CSV. Devuelve (stats por columna, n_filas, delimitador)."""
    with path.open("r", encoding="utf-8", errors="replace", newline="") as fh:
        sample = fh.read(65536)
        fh.seek(0)
        delim = sniff_delimiter(sample)
        reader = csv.reader(fh, delimiter=delim)
        try:
            header = next(reader)
        except StopIteration:
            return [], 0, delim
        stats = [ColumnStat(h, classify_header(h)) for h in header]
        n_rows = 0
        for row in reader:
            n_rows += 1
            for i, cell in enumerate(row):
                if i >= len(stats):
                    continue  # fila con más campos que el header
                if not cell or not cell.strip():
                    continue
                st = stats[i]
                st.nonempty += 1
                if RE_EMAIL.search(cell):
                    st.email += 1
                if count_phone(cell):
                    st.phone += 1
                if count_document(cell):
                    st.doc += 1
    return stats, n_rows, delim


# ── Reporte ───────────────────────────────────────────────────────────────────

def report_file(path: Path, stats: list[ColumnStat], n_rows: int, delim: str) -> bool:
    """Imprime el reporte de un archivo. Devuelve True si encontró PII probable."""
    sep_show = {";": "';'", ",": "','", "\t": "TAB"}.get(delim, repr(delim))
    print(f"\n■ {path}")
    print(f"  sep={sep_show} · {n_rows} filas · {len(stats)} columnas")

    if not stats:
        print("  (archivo vacío)")
        return False

    header = f"  {'columna':<38} {'no-vac':>7} {'email':>6} {'tel':>6} {'doc':>6}  señal"
    print(header)
    print("  " + "-" * (len(header) - 2))

    pii_cols: list[str] = []
    quasi_cols: list[str] = []
    for st in stats:
        flag = ""
        if st.label == "PII":
            flag = "⚠ NOMBRE-PII"
        elif st.label == "QUASI":
            flag = "· cuasi-id"
        name = st.name if len(st.name) <= 38 else st.name[:35] + "..."
        row = (f"  {name:<38} {st.nonempty:>7} {st.email:>6} "
               f"{st.phone:>6} {st.doc:>6}  {flag}")
        # Sólo imprimir filas con alguna señal para no ahogar el reporte.
        if st.label or st.has_content_pii:
            print(row)
        if st.label == "PII" or st.has_content_pii:
            pii_cols.append(st.name)
        if st.label == "QUASI":
            quasi_cols.append(st.name)

    found = bool(pii_cols)
    if not found:
        print("  → sin señales de PII directa en este archivo")
    else:
        emails = [f"{s.name}({s.email})" for s in stats if s.email]
        phones = [f"{s.name}({s.phone})" for s in stats if s.phone]
        docs = [f"{s.name}({s.doc})" for s in stats if s.doc]
        names = [s.name for s in stats if s.label == "PII"]
        if names:
            print(f"  ⛔ nombres de columna PII: {', '.join(names)}")
        if emails:
            print(f"  ⛔ celdas con email:       {', '.join(emails)}")
        if phones:
            print(f"  ⛔ celdas con teléfono:    {', '.join(phones)}")
        if docs:
            print(f"  ⛔ celdas con documento:   {', '.join(docs)}")
    if quasi_cols:
        print(f"  ℹ cuasi-identificadores (revisar si el destino es público): "
              f"{', '.join(quasi_cols)}")
    return found


# ── Recolección de archivos ───────────────────────────────────────────────────

def collect_csvs(paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"AVISO: no existe: {path}", file=sys.stderr)
            continue
        if path.is_dir():
            files.extend(sorted(path.rglob("*.csv")))
        elif path.suffix.lower() == ".csv":
            files.append(path)
        else:
            # Se permite escanear cualquier archivo de texto tabular igualmente.
            files.append(path)
    return files


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2

    files = collect_csvs(argv[1:])
    if not files:
        print("ERROR: no se encontraron CSVs para escanear.", file=sys.stderr)
        return 2

    print("=" * 72)
    print("  scan_pii.py — guard de PII para datos AMA (menores 14-19)")
    print("=" * 72)

    any_pii = False
    dirty_files: list[str] = []
    for f in files:
        try:
            stats, n_rows, delim = scan_file(f)
        except Exception as exc:  # noqa: BLE001 — reportar y seguir con los demás
            print(f"\n■ {f}\n  ERROR al leer: {exc}", file=sys.stderr)
            any_pii = True  # ante la duda, fallar el gate
            dirty_files.append(str(f))
            continue
        if report_file(f, stats, n_rows, delim):
            any_pii = True
            dirty_files.append(str(f))

    print("\n" + "=" * 72)
    if any_pii:
        print("  ⛔ RESULTADO: PII PROBABLE — NO commitear / NO push / NO deploy.")
        print(f"     Archivos con señales ({len(dirty_files)}):")
        for d in dirty_files:
            print(f"       - {d}")
        print("     Regenerá el artefacto con allowlist de columnas (anonimizar.py /")
        print("     exportar_bot.py) y volvé a correr este scan antes de subir nada.")
    else:
        print("  ✅ RESULTADO: sin PII directa evidente.")
        print("     Igual verificá: cuasi-identificadores si el destino es público,")
        print("     y el árbol remoto tras el push (que no se haya colado el crudo).")
    print("=" * 72)
    return 1 if any_pii else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
