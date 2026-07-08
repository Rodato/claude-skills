# Templates — arranque de un dashboard nuevo

Archivos de arranque **listos para copiar**, coherentes entre sí, que implementan la receta de la
skill. Por defecto usan **pg8000 + SQLAlchemy** (seguro para Python 3.12+ / Streamlit Cloud) y la
**piel clara premium**.

## Cómo usarlos

1. Copiá este árbol a la raíz del repo nuevo (sin este README):
   ```
   app.py  requirements.txt  runtime.txt  .env.example  .streamlit/config.toml
   utils/db.py  utils/styles.py
   components/charts.py  components/kpi_row.py  components/filters.py
   pages/overview.py
   ```
2. `cp .env.example .env` y poné tu `DATABASE_URL` de Supabase (pooler, puerto 6543).
3. **Ajustá `utils/db.py` al esquema de tu bot**: cambiá el nombre de tabla (`interactions`) y de
   columnas (`client_number`, `conversation_id`, `created_at`) por los reales. Actualizá los
   sentinels de cuentas de test (`_TEST_*`).
4. (Opcional) Elegí piel en `utils/styles.py` — viene la clara premium; para la dark terminal,
   ver `references/charts-kpis-estilo.md`.
5. Correr:
   ```bash
   pip3 install -r requirements.txt
   python3 -m streamlit run app.py
   ```

## Qué trae cada archivo

- `app.py` — entry point: config, inyecta CSS, nav multipágina, sidebar.
- `utils/db.py` — capa de datos: engine pg8000, `query_df`, `date_filter()` (timezone + filtro de test), KPIs y actividad diaria de ejemplo.
- `utils/styles.py` — dict `COLORS` + `inject()` (CSS global) + `page_header()`.
- `components/charts.py` — fábrica Plotly (`go.*`): `bar_h`, `donut`, `line_timeseries` (rellena días en 0).
- `components/kpi_row.py` — KPI cards HTML con accent bar + sparkline + delta.
- `components/filters.py` — sidebar con date pickers + presets 7d/30d; `get_filters()`.
- `pages/overview.py` — página de ejemplo cableando KPIs + actividad diaria con cache.

Todo lo demás (convenciones, gotchas, multi-bot, auth, reportes) está en las `references/` de la skill.
