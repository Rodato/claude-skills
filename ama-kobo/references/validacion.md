# Validación y cruce de encuestas

Reglas de calidad de datos AMA. Fuentes: `Lineabase2026/src/validate_kobo.py`
(IDs, duración, timestamps) y `src/crosscheck.py` (cruce asistencia↔Kobo).

## 1. IDs inválidos (placeholder + longitud)

Un ID es inválido si es **placeholder** (todos el mismo dígito) o tiene **longitud
incorrecta** para la ciudad (Leticia 10, Cobija 7 u 8).

```python
# validate_kobo.py::validate_id
def check(val):
    s = str(val).strip()
    if s.isdigit() and len(set(s)) == 1:              # 11111111, 9999999
        return True, f"placeholder (todos '{s[0]}')"
    if len(s) not in id_length:                        # id_length = 10  o  [7, 8]
        return True, f"longitud incorrecta ({len(s)} dígitos, esperado {lengths_str})"
    return False, ""
```

En la **línea de salida** (`coverage.py`) el placeholder es más amplio: además de
"todos el mismo dígito" descarta **secuencias** tipo `12345678` (`_is_placeholder_doc`).
Los encuestadores tipean rellenos cuando no tienen la cédula (`11111111` = 199 casos,
`12345678`, `99999999999`, `123456`). Tratarlos como "sin documento", **no** como una
persona real — si no, colapsan personas distintas en el dedup y borran respuestas
reales (bug real 2026-06-23, subestimaba la salida ~3.9 pts).

Para **match** de IDs entre fuentes, normalizar quitando no-alfanuméricos y ceros a
la izquierda (`normalize_id_for_match`, crosscheck.py):

```python
s = "".join(c for c in str(val).strip() if c.isalnum())
return s.lstrip("0") or s   # si queda vacío (ej. "000"), preserva s
```

## 2. Outliers de duración (media − 3σ, por salón)

Duración = `end − start` en minutos. Un tiempo **sospechosamente corto** dentro de
su salón (llenó la encuesta a la carrera) se marca como outlier. Constantes:
`STD_MULTIPLIER = 3.0`, `MAX_DURATION_H = 8`.

```python
# validate_kobo.py
df["start_dt"] = pd.to_datetime(df["start"], utc=True)
df["end_dt"]   = pd.to_datetime(df["end"], utc=True)
df["duration_min"] = (df["end_dt"] - df["start_dt"]).dt.total_seconds() / 60
```

El umbral se calcula **por salón** (`groupby(grade_col)`), sobre los registros con
timestamp válido:

```python
# detect_outliers_in_group(durations)
threshold = mean - STD_MULTIPLIER * std        # media − 3σ
mask = durations < threshold                    # sospechoso = por debajo
```

Casos que devuelven "sin outliers" (esperado, no bug):
- `n < 2` → grupo muy pequeño.
- `std == 0` → todos iguales.
- Si hubo un levantamiento con la encuesta abierta horas, la media/σ se **inflan** y
  el umbral cae en **negativo** → nadie flagueado. Comportamiento correcto.

## 3. Timestamps corruptos (excluidos del análisis de tiempo)

Duración negativa (`end < start`) o mayor a `MAX_DURATION_H` horas = timestamp
corrupto. Se **excluye** del cálculo de outliers y se reporta aparte.

```python
max_min = MAX_DURATION_H * 60
df["timestamp_invalido"] = (df["duration_min"] < 0) | (df["duration_min"] > max_min)
# ...
valid = group[~group["timestamp_invalido"]]     # solo válidos entran al outlier
```

## 4. Cruce asistencia (Google Form) ↔ Kobo

`crosscheck.py` compara **conteos por escuela+salón** entre la lista de asistencia
y Kobo. No depende de matching de nombres/IDs para el conteo.

### Filtro de fecha del Form: `Marca temporal`, NUNCA `Fecha de aplicación`

`Fecha de aplicación` tiene typos con años **2007-2011**. Usar siempre `Marca
temporal`, que además hay que limpiar (formato `2026/02/23 7:18:51 a. m. GMT-5`):

```python
# parse_marca_temporal
cleaned = (ts_series
    .str.replace(' ', ' ', regex=False)       # narrow no-break space
    .str.replace('a. m.', 'AM', regex=False)
    .str.replace('p. m.', 'PM', regex=False)
    .str.replace(r'\s*GMT[+-]\d+', '', regex=True)
    .str.strip())
return pd.to_datetime(cleaned, format='%Y/%m/%d %I:%M:%S %p')
```

Deduplicar el Form por `ciudad + ID + fecha`, conservando el más reciente.

### Nombres de escuela

```python
# normalize_school: 'Dr Antonio Vaca Diez (Cobija / BOL)' → 'Dr Antonio Vaca Diez'
paren = s.find(" (")
if paren != -1:
    s = s[:paren]
return SCHOOL_CORRECTIONS.get(s, s)
```

- **Sedes parecidas NO se unifican**: `"Antonio Vaca Diez"` (secundaria) ≠ `"Dr
  Antonio Vaca Diez"` (primaria) son colegios distintos. Sus diferencias de conteo
  se reportan como error de registro, no se fusionan.
- `SCHOOL_CORRECTIONS` corrige nombres del **Form** para que coincidan con Kobo.
  **Kobo es la fuente de verdad.**

### Interpretación del signo de la diferencia (`kobo − asistencia`)

- `⚠` diferencia **< 0**: hay más en asistencia que en Kobo → faltan encuestas.
- `✓` diferencia **= 0**: cuadra.
- `+` diferencia **> 0**: más en Kobo que en asistencia → llenó sin estar en lista.

## 5. Faltantes: match por ID, luego por nombre (`find_missing_students`)

Para grupos donde asistencia > Kobo, por cada estudiante de asistencia:

1. **Match por ID** normalizado contra los IDs Kobo del mismo grupo → si aparece,
   está OK.
2. Si no: clasificar la razón (`ID vacío`, `placeholder`, `ID no encontrado`).
3. **Doble check por nombre** dentro del grupo (`names_match`): token-subset —
   todos los tokens del nombre de asistencia deben estar en el nombre Kobo (mínimo
   2 tokens para evitar falsos positivos):

```python
# names_match: asistencia "Maria Garcia" ⊆ Kobo "Maria Fernanda Garcia Lopez"
att_tokens  = set(normalize_text(att_name).split())
kobo_tokens = set(normalize_text(kobo_name).split())
if len(att_tokens) < 2:
    return False
return att_tokens.issubset(kobo_tokens)
```

Si hay match de nombre pero no de ID → el estudiante **sí** llenó la encuesta con un
**ID mal digitado**: corregir el ID, no re-levantar. (En el Excel se pinta naranja.)

`normalize_text` = minúsculas + sin tildes (NFD, drop `Mn`) + espacios colapsados.

## 6. Record-linkage asistido por LLM (línea de salida)

Para los no-cruzados por el método determinista (`difflib < 0.88`, base sin
documento), la línea de salida hizo un segundo pase con subagentes LLM **uno por
colegio** (bloqueo por colegio, los labels coinciden exactos). Criterio conservador
(son menores), 1-a-1, teléfono ignorado (suele ser el del encuestador). Es
**worklist de verificación humana, no cobertura auto-aplicada**. Detalle en
`Lineasalida2026/lago-agrio/CLAUDE.md`.
