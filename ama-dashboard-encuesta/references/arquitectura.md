# Arquitectura — stack mínimo y vistas agnósticas

Detalle del esqueleto: qué stack, por qué sin DB, cómo se organiza el código, y el patrón
source-agnóstico que sostiene todo. Fuente: `Lineasalida2026/lago-agrio/` y su `CLAUDE.md`.

## Stack

- **Streamlit** + **`streamlit-autorefresh`** — refresh global cada 30s (`st_autorefresh`).
- **httpx** — llama las APIs de **Typeform** y **Kobo** directo, sin DB intermedia.
- **plotly.graph_objects** — todas las gráficas, con tema oscuro custom (`theme.py`).
- **pandas** — toda la transformación de datos in-memory.
- **Python 3.11** (Homebrew). Fijado en `runtime.txt` (`python-3.11`).

`requirements.txt` completo del repo canónico:

```
httpx>=0.27
streamlit>=1.36
streamlit-autorefresh>=1.0.1
pandas>=2.2
plotly>=5.22
```

**Sin Supabase, sin webhooks, sin Airtable.** Es una decisión intencional de stack mínimo: la
API de la encuesta ya es la fuente de verdad, así que meter una DB en el medio solo agrega una
copia que se desincroniza. El "en vivo" sale de **autorefresh (30s) + `@st.cache_data(ttl=30)`**,
no de una capa de persistencia. Si aparece la tentación de "cachear en una tabla", la respuesta
es el ttl del cache.

`openpyxl` **no** está en `requirements.txt` a propósito: los `scripts/` de informes Excel son
herramienta de análisis offline, no parte del deploy del dashboard.

## Entry point (`app.py`) — orden de arranque

```python
st.set_page_config(page_title="AMA · ENCUESTA DE SALIDA", page_icon="▣", layout="wide")
inject_css()                                  # tema Bloomberg, una vez, arriba de todo
st_autorefresh(interval=30 * 1000, key="global_refresh")   # el "en vivo"
tz = ZoneInfo("America/Bogota")
```

Luego: selector de fuente en el sidebar → carga de datos según la fuente → filtros → header → tabs.

## El patrón source-agnóstico (regla central)

Cada rama de fuente deja **el mismo contrato** para que los tabs no sepan de dónde vienen los datos:

- `responses` — DataFrame con `response_id`, `submitted_at` (tz-aware UTC) y `hidden_*` opcionales.
- `source_title`, `goal_total` — metadatos de la fuente.
- `compute_comp(df)` — función que devuelve el DataFrame `comp` `[pregunta, respondidas, total, pct]`.

```python
if fuente == "TYPEFORM":
    form_def = get_form_definition(FORM_ID)
    responses = get_responses(FORM_ID)
    answers = get_answers(FORM_ID)
    source_title = form_def.get("title") or "Encuesta de salida (Typeform)"
    goal_total = (st.secrets.get("goals") or {}).get("total")
    def compute_comp(df):
        return completion_by_question(form_def, answers, df["response_id"].tolist())
else:  # KOBO
    asset = kobo.get_asset(KOBO_UID)
    responses = kobo.get_responses(KOBO_UID)
    records = kobo.get_submissions(KOBO_UID)
    source_title = asset.get("title") or "Encuesta de salida (Kobo)"
    goal_total = (st.secrets.get("kobo_goals") or {}).get("total")
    def compute_comp(df):
        return kobo.completion_by_label(asset, records, df["response_id"].tolist())
```

A partir de ahí, **todo** se ramifica por columna presente, no por fuente:

```python
# Filtro CIUDAD solo si la fuente lo trae (Kobo sí, Typeform no).
if "hidden_ciudad" in responses.columns:
    ciudad_sel = st.selectbox("CIUDAD", ["TODAS LAS CIUDADES"] + sorted(...))

# Filtro COLEGIO en cascada (opciones según la ciudad ya elegida).
pre = responses
if ciudad_filter and "hidden_ciudad" in pre.columns:
    pre = pre[pre["hidden_ciudad"] == ciudad_filter]
```

**Por qué importa:** agregar una fuente = escribir un cliente que emita `responses` +
`compute_comp`. Los tabs AVANCE y COMPLETITUD no se tocan.

## Manejo de tiempo (tz-aware, siempre)

`submitted_at` llega en UTC y se mantiene tz-aware. Para "hoy" y "últimas 24h" se usa el tz del
propio dato, no un `datetime.now()` naive:

```python
tz = ZoneInfo("America/Bogota")
now = datetime.now(tz)
today_d = now.date()
last_24h = datetime.now(df["submitted_at"].dt.tz) - timedelta(hours=24)   # tz del dato
ult_24h = (df["submitted_at"] >= last_24h).sum()
```

## Tabs

`AVANCE` · `COMPLETITUD POR PREGUNTA` · `COBERTURA vs LÍNEA BASE` · `ENCUESTA BOT`.

- **AVANCE**: KPIs (total, hoy, encuestadores/colegios, ritmo resp/h 24h), barra de meta opcional
  (`goal_total`), distribución por colegio (barras h), ritmo diario (barras + acumulado en `y2`),
  ranking por colegio (`html_table`). El ranking es **por colegio en ambas fuentes** — el de
  encuestadores se quitó por datos sucios en Typeform (5 variantes de "Katherine Gómez").
- **COMPLETITUD**: KPIs (preguntas total, 100% completas, completitud media), barras h con color
  por umbral (`RED <50`, `AMBER <90`, `GREEN ≥90`) dentro de `st.container(height=520)`, tabla detalle.
- **COBERTURA**: cruce base↔salida por HMAC — ver `references/cobertura.md`.
- **BOT** (específico de AMA): lee un asset Kobo aparte (`BOT_ASSET_UID`) con la encuesta de
  satisfacción del chatbot. No es parte del patrón general; es un tab extra de ese levantamiento.

## Secrets (`.streamlit/secrets.toml`)

Gitignored. Plantilla commiteada en `secrets.toml.example`. Estructura:

```toml
# ── Typeform ──
TYPEFORM_TOKEN = "tfp_..."
FORM_ID = "xxxxxxxx"
[field_refs]                 # preguntas del form tratadas como hidden fields
# encuestador = "<field-ref>"
# colegio     = "<field-ref>"

# ── KoboToolbox ──
KOBO_BASE = "https://kf.kobotoolbox.org"   # global; eu.kobotoolbox.org para EU
KOBO_TOKEN = "..."
KOBO_ASSET_UID = "aXxxxxxxxxxxxxxxxxxxxx"

# ── Cobertura ──
COVERAGE_SALT = "cadena-larga-y-secreta"   # MISMO salt que generó el parquet

# ── Metas opcionales (barra de progreso en AVANCE) ──
[goals]
total = 1500
[kobo_goals]
# total = 1500
```

Los secrets **viven en Streamlit Cloud** (app settings), no en el repo. Al agregar una fuente,
pegá sus secrets ahí también. **Si rotás un token, actualizalo en Streamlit Cloud.**

## Deploy

- **Streamlit Community Cloud** conectado al repo. Cada push a `main` **redespliega**.
- **Los datos no se commitean** — el repo es solo código. Las respuestas se releen de la API.
- **Si tocás el form en Typeform** (agregar/quitar pregunta), **no hay que cambiar código**: el
  dashboard se adapta en el siguiente refresh (la definición del form tiene su propio cache de 60s).
- **Cold start**: si nadie abre el link por horas, la app duerme; la primera carga después tarda
  ~15-20s. Es de Streamlit Cloud, no del código.

## Correr local

```bash
cd ~/Documents/Dev/AMA/Lineasalida2026/lago-agrio
source .venv/bin/activate     # python3.11 -m venv .venv si no existe
pip install -r requirements.txt
streamlit run dashboard/app.py
```

**Gotcha del `.venv` con shebang roto**: si el repo se movió de carpeta, el shebang de los
scripts del venv apunta a la ruta vieja y `streamlit run ...` directo falla. Workaround local:
`.venv/bin/python -m streamlit run dashboard/app.py`. Prod (Streamlit Cloud) no se afecta.
