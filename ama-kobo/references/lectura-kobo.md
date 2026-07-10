# Lectura y parseo de datos Kobo

Cómo leer un export/CSV de KoboToolbox en pandas sin corromper datos. Fuentes:
`Lineabase2026/src/validate_kobo.py`, `src/crosscheck.py`, `src/preprocess.py`.

## 1. Separador `;` y `dtype=str`

Los CSV de Kobo (export UI y `fetch_kobo.py`) usan **punto y coma**. Y hay que
forzar la columna ID (o todo) a string, o pandas la lee como número y **pierde
los ceros a la izquierda** (`0123456` → `123456`).

```python
# validate_kobo.py: solo la columna ID como str
df = pd.read_csv(csv_path, sep=";", dtype={cfg["id_col"]: str})

# crosscheck.py / preprocess.py / tablero: todo como str (más seguro)
df = pd.read_csv(matches[0], sep=";", dtype=str)
```

Buscar el CSV más reciente por patrón de ciudad (glob + mtime):

```python
matches = glob.glob(pattern)                       # p.ej. "data/kobo/*Leticia*.csv"
matches.sort(key=os.path.getmtime, reverse=True)
df = pd.read_csv(matches[0], sep=";", dtype=str)   # el más reciente
```

`CITY_CONFIG` (validate_kobo.py) mapea ciudad → patrón, columna ID, longitud
esperada, columnas de nombre/escuela/grado. La columna ID **difiere por ciudad**:
Leticia `¿Cuál es tu tarjeta de identidad?`, Cobija `¿Cuál es tu número de
documento de identidad?`.

## 2. Filtro por fecha: `_submission_time`, no `start`

La encuesta se **abre en la mañana** y se **sube en la noche** del mismo día. Por
eso el único campo temporal confiable para "de qué día es esta respuesta" es
`_submission_time`. `start`/`end` sirven para **duración**, no para filtrar el día.

```python
# Filtrar por día de aplicación (validate_kobo.py, crosscheck.py):
df = df[df["_submission_time"].str[:10] == args.date].copy()

# En fetch_kobo.py el filtro usa comparación de datetime:
submission_dt = pd.to_datetime(df["_submission_time"], errors="coerce")
mask_keep = submission_dt >= pd.to_datetime(start_date)
```

`_submission_time` está en **UTC**. En los dashboards (`lib/kobo.py`) se parsea con
`pd.to_datetime(..., utc=True, errors="coerce")`.

## 3. Columna de grado DUPLICADA → unificar con `bfill`

Kobo exporta la misma pregunta varias veces cuando el form tuvo varias versiones;
pandas las renombra `col`, `col.1`, `col.2`… **Distintas escuelas usan distintas
versiones**, así que la respuesta real puede estar en cualquiera de ellas. Hay que
combinarlas fila a fila.

`resolve_grade_col` (validate_kobo.py) devuelve la columna con datos:

```python
def resolve_grade_col(df, base_name):
    candidates = [c for c in df.columns
                  if c == base_name or c.startswith(base_name + ".")]
    for col in reversed(candidates):   # la última suele ser la real
        if df[col].notna().any():
            return col
    return base_name  # fallback
```

`_grade_merged` (crosscheck.py) es más robusto: combina TODAS las versiones con
`bfill` (primera no-nula por fila):

```python
grade_cols = [c for c in df.columns
              if c == grade_base or c.startswith(grade_base + ".")]
df["_grade_merged"] = df[grade_cols].bfill(axis=1).iloc[:, 0]
```

`resolve_dup_column` (preprocess.py) es la versión canónica y agrega el caso de la
**versión del form con espacio extra** (`base_name + ' '`):

```python
candidates = [
    c for c in df.columns
    if c == base_name
    or c.startswith(base_name + ".")
    or c.rstrip() == base_name          # versión con trailing space
]
merged = df[candidates].bfill(axis=1).iloc[:, 0]
```

`unify_surveys.py::find_variant_columns` lo lleva más lejos: además normaliza
comillas tipográficas (`“” ‘’`) y solo acepta el sufijo tras el punto si son
**dígitos** (`re.fullmatch(r"\.\d+", tail)`), para no fusionar columnas parecidas
por accidente. Usalo cuando mapees preguntas entre datasets.

## 4. Formato de grado por ciudad (`format_grade`)

```python
def format_grade(code):
    # Leticia: '10:03' → 'Grado 10 – Salón 03'
    # Cobija:  '6A'    → 'Grado 6A'   (se deja tal cual)
    if pd.isna(code):
        return "Sin grado"
    s = str(code).strip()
    parts = s.split(":")
    if len(parts) == 2:
        return f"Grado {parts[0]} – Salón {parts[1]}"
    return f"Grado {s}"
```

Para **matching** (no display) de salón, usar `normalize_grade` (crosscheck.py),
que uniforma variantes sucias del Form: `'5a'→'5A'`, `'11-01'/'11_01'→'11:01'`,
`'10;02'→'10:02'`, `'10:1'→'10:01'`, `'B6'→'6B'`.

En la línea de salida (Kobo API) el grado es un `calculate` (`grado_final`) que
coalesce ~15 variantes `grado_<ciudad>_<colegio>`; su código (p.ej. `4_A`) se
etiqueta uniendo todas las listas `grados_*`. Ver `lib/kobo.py::get_asset`.

## 5. Placeholders de valor → NA

En `preprocess.py`, tras leer, se reemplazan los rellenos de "no sé" por NA:

```python
PLACEHOLDER_VALUES = ["Sin información", "No válida", "No disponible"]
df = df.replace(PLACEHOLDER_VALUES, pd.NA)
```
