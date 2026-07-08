# Arquitectura, stack y deployment

## Stack base

```
streamlit>=1.32       # UI (multipágina con st.navigation, o tabs con st.tabs)
plotly>=5.20          # gráficas
pandas>=2.0
python-dotenv>=1.0    # .env con DATABASE_URL
openpyxl>=3.1         # exports Excel (si hay reportes)
# + driver Postgres — elegir UNO (ver abajo)
```

## Elección de driver Postgres (decisión importante)

| | `psycopg2` (aly-dashboard) | `pg8000` + SQLAlchemy (AMA) |
|---|---|---|
| Cuándo | Python ≤ 3.11, entorno con wheels | **Python 3.12+** o Streamlit Cloud con runtime nuevo |
| Por qué | Maduro, `RealDictCursor` cómodo | `psycopg2` **no tiene wheels para 3.12+** y rompe el build en cloud; `pg8000` es pure-Python |
| requirements | `psycopg2-binary` | `pg8000>=1.30` + `sqlalchemy>=2.0` |
| Parámetros | `%s` posicional | `:param` named (dict) |

**Regla:** para un dashboard nuevo que va a Streamlit Cloud, **default a `pg8000` + SQLAlchemy**
(evita el clásico build roto). Solo usar psycopg2 si ya hay una base con él.

Forzar el driver pg8000 sin string-manipulation frágil:
```python
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
_engine = create_engine(make_url(DATABASE_URL).set(drivername="postgresql+pg8000"))
# NO hacer DATABASE_URL.replace("postgresql://", "postgresql+pg8000://") — produce bugs sutiles
```

## Esqueleto de archivos

Dos layouts válidos, según tamaño:

**Multipágina (aly-dashboard)** — cuando hay varias vistas ricas:
```
app.py                 # st.navigation(pages, position="hidden") + nav custom en sidebar
pages/overview.py …
components/charts.py · kpi_row.py · filters.py
utils/db.py · styles.py · i18n.py · auth.py
data/
```

**Single-file con tabs (AMA)** — cuando es más chico y operativo:
```
src/app.py             # todo el dashboard en tabs: st.tabs(["▣ INDICADORES", "▣ POR COLEGIO", …])
src/db.py              # capa de datos
src/*_report.py        # reportes (Excel / narrativa)
```

Empezá con tabs si son ≤4 vistas simples; pasá a `pages/` cuando cada vista crece.

## Entry point (patrón app.py)

```python
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="…", page_icon="🤖", layout="wide",
                   initial_sidebar_state="expanded")

inject_styles()                      # CSS global una sola vez, antes de renderizar nada
require_login()                      # (opcional) auth gate: st.stop() si no hay sesión
# ... nav / tabs / render de páginas
```

`inject_styles()` va **antes** de cualquier render. Si hay auth, el gate va **antes** de la nav.

## Deployment

- **Streamlit Cloud** (`share.streamlit.io`), auto-redeploy en push a `main`.
- Secrets en el panel de Streamlit Cloud: como mínimo `DATABASE_URL`; sumar `BOT_START_DATE`,
  `OPENROUTER_API_KEY`, y las credenciales de auth (`.streamlit/secrets.toml`) según el caso.
- `runtime.txt` fija la versión de Python en cloud (ej. `python-3.12`).
- **Gotcha de hot-reload:** al agregar un símbolo nuevo a un módulo ya importado, el reload
  puede fallar con `ImportError` por caché de `sys.modules`. Solución: **Reboot app** desde
  "Manage app" (no requiere cambio de código).
- El schema custom de Supabase (ej. `ama`) suele **no estar expuesto por la REST API** —
  se accede solo por conexión Postgres directa (pooler, puerto 6543).
