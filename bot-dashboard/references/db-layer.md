# La capa de datos (`db.py`)

`db.py` es la **única** puerta a la base. Toda query vive acá, parametrizada, en timezone
`America/Bogota`, y pasando por el filtro de cuentas de test. Las páginas nunca abren conexión
ni escriben SQL sueltas.

## Conexión + helper de lectura

**Variante psycopg2** (aly-dashboard):
```python
import os, psycopg2, psycopg2.extras, pandas as pd
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
TZ = "America/Bogota"

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def fetch_df(query: str, params=None) -> pd.DataFrame:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params or [])
            return pd.DataFrame(cur.fetchall())

def execute(query: str, params=None) -> int:      # INSERT/UPDATE/DELETE → rowcount
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or [])
            return cur.rowcount
```

**Variante pg8000 + SQLAlchemy** (AMA — preferida para Python 3.12+):
```python
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
_engine = create_engine(make_url(DATABASE_URL).set(drivername="postgresql+pg8000"))

def query_df(sql: str, params: Optional[dict] = None) -> pd.DataFrame:
    with _engine.connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params or {})
```
Con SQLAlchemy 2.0: params **named** (`:param`) en un dict. `SELECT DISTINCT … ORDER BY expr::int`
falla → usar `GROUP BY`.

## Timezone — regla dura

La DB guarda `timestamptz` en **UTC**; la UI opera en **GMT-5**. Toda query que extraiga
hora/día o filtre por fecha convierte primero:
```sql
WHERE DATE(created_at AT TIME ZONE 'America/Bogota') >= :start
```
El "hoy" del sidebar también se calcula con `ZoneInfo("America/Bogota")`, no con `date.today()`.
(pg8000 devuelve `DATE` como `datetime` 00:00 — castear `::text` en SQL si Plotly muestra la hora en el eje.)

## Filtro central de fecha + cuentas de test

Otros repos (evals, benchmarks, smoke tests) escriben a las **mismas tablas** y contaminan los KPIs.
Un único `_date_filter()` construye el `WHERE` y **siempre** excluye esas cuentas, para que cada
query nueva herede el filtro sin pensarlo:

```python
_TEST_CLIENT_NUMBERS = ("eval", "verify", "smoke", "debug-rank", …)   # exactos
_TEST_CLIENT_LIKE    = ("debug-%", "test-%", "smoke%")                 # patrones client_number
_TEST_CONV_LIKE      = ("eval-%", "verify-%", "trace-%", …)            # patrones conversation_id

def _date_filter(date_col, date_from=None, date_to=None, *, bot_id=None,
                 client_col="client_number", conv_col="conversation_id"):
    clauses, params = [], []
    if date_from: clauses.append(f"DATE({date_col} AT TIME ZONE '{TZ}') >= %s"); params.append(date_from)
    if date_to:   clauses.append(f"DATE({date_col} AT TIME ZONE '{TZ}') <  %s"); params.append(date_to)
    if bot_id:    clauses.append("bot_id = %s"); params.append(bot_id)
    if client_col:
        clauses.append(f"{client_col} NOT IN ({','.join(['%s']*len(_TEST_CLIENT_NUMBERS))})")
        params += list(_TEST_CLIENT_NUMBERS)
        for pat in _TEST_CLIENT_LIKE: clauses.append(f"{client_col} NOT LIKE %s"); params.append(pat)
    if conv_col:
        for pat in _TEST_CONV_LIKE: clauses.append(f"{conv_col} NOT LIKE %s"); params.append(pat)
    where = "WHERE " + " AND ".join(clauses) if clauses else ""
    return where, params
```
- `date_to` es **exclusivo** (fecha elegida + 1 día) para incluir el día completo.
- Queries con alias pasan columnas calificadas (`client_col="ui.client_number"`).
- Drill-downs por usuario explícito apagan el filtro (`client_col=None, conv_col=None`).
- Si el repo hermano agrega un prefijo sentinel nuevo, sumarlo a la tupla correspondiente.

**Filtro por país** (variante sin bot_id, AMA): `client_number ~ '^(57|59)'` (Colombia/Bolivia) vía
un helper `_country_clause(alias)`.

## Descubrimiento multi-bot (si la DB es compartida)

Si varias instancias del bot comparten tablas con una columna `bot_id`, el dashboard **detecta**
los bots disponibles y muestra un selector:
```python
def get_available_bot_ids() -> list[str]:
    # SELECT DISTINCT bot_id … WHERE bot_id <> '' AND <mismos filtros de test>
    # fallback a un bot conocido si la query falla
```
El bot seleccionado vive en `st.session_state["selected_bot"]` y todas las queries filtran por él.
Con auth por roles, el selector se limita a los `bot_id` permitidos del rol.

## Convenciones de query

- **Siempre parametrizado.** Nunca f-strings con datos externos. Las partes dinámicas del SQL
  (columnas, cláusulas) sí se interpolan, pero **los valores** van por params.
- `session`/`day` guardados como `text` → castear `::int` para ordenar.
- `responses` JSON con claves `q1, q2…` → extraer con `->>'q1'`.
- Valores sucios conocidos (ej. literal `'false'` en `school`) → filtrar explícito en rankings.
- Firma típica: `get_algo(date_from=None, date_to=None, bot_id=None) -> pd.DataFrame|dict`.
