---
name: bot-dashboard
description: >-
  Recipe and conventions for building or extending Streamlit dashboards that
  monitor a WhatsApp/chatbot from a Supabase Postgres DB, following Daniel's
  established pattern (aly-dashboard, AMA/Bot_monitoring). Use when starting a
  new bot-monitoring dashboard, or when adding pages/queries/charts/KPIs to an
  existing one — so the data layer, chart factory, styling and hard-won gotchas
  stay consistent instead of being reinvented each time.
---

# Bot Dashboard — dashboards de seguimiento de bots

Receta reutilizable para dashboards operativos de **Streamlit + Supabase (Postgres) + Plotly**
que monitorean un bot de WhatsApp/chat. Cubre dos casos:

1. **Arrancar uno nuevo** desde cero (scaffolding + motor de datos + estilo).
2. **Editar uno existente** (agregar página, query, gráfica o KPI) sin romper las convenciones.

## Implementaciones de referencia (leé el código real antes de inventar)

Dos dashboards vivos que son la misma receta con distinta piel. Cuando dudes de un patrón,
mirá cómo está resuelto ahí:

| | `aly-dashboard` | `AMA/Bot_monitoring` |
|---|---|---|
| Ruta local | `~/Documents/Dev/` (clonar de `github.com/Rodato/aly-dashboard`) | `~/Documents/Dev/AMA/Bot_monitoring/` |
| Driver DB | `psycopg2` + `RealDictCursor` | `pg8000` + SQLAlchemy (Python 3.12+) |
| Estilo | Claro premium (Oswald / Open Sans) | Bloomberg dark terminal (IBM Plex Mono) |
| Multi-tenant | Sí (`bot_id`, auth con roles) | No (filtro por país/ciudad) |
| Reportes | Excel de alertas | Excel semanal + narrativa LLM por cron |

Ambos tienen un `CLAUDE.md` extenso con el detalle específico de ese repo — **léelo primero**
cuando trabajes sobre uno de ellos. Esta skill captura lo que es **común y transferible**.

## La receta en una imagen

```
app.py                 # entry point: set_page_config, inject CSS, (auth), nav, render páginas
pages/  o  tabs        # una vista por archivo/tab (overview, usuarios, alertas, leaderboard…)
components/
  charts.py            # FÁBRICA Plotly centralizada — todas las gráficas salen de acá
  kpi_row.py           # KPI cards HTML custom (accent bar + icono + sparkline + delta)
  filters.py           # sidebar: logo, nav, selector de bot/ciudad, date pickers, presets
utils/  (o raíz)
  db.py                # ÚNICA capa de datos: conexión + TODAS las queries, parametrizadas
  styles.py            # CSS inyectado + dict COLORS + helpers de layout
  i18n.py              # (opcional) t("key") ES/EN
data/                  # geojson, assets bundled
requirements.txt
.streamlit/config.toml # tema base de Streamlit
.env                   # DATABASE_URL (+ START_DATE, OPENROUTER_API_KEY si aplica)
```

Deploy: **Streamlit Cloud**, auto-redeploy en push a `main`. Único secret imprescindible:
`DATABASE_URL`. (Ver `references/arquitectura.md`.)

## Cómo trabajar

**Para un dashboard nuevo (camino rápido):** copiá `templates/` a la raíz del repo nuevo — es un
dashboard mínimo pero funcional (pg8000 + piel clara) que ya implementa la receta. Seguí su
`templates/README.md`: editá `.env`, ajustá tabla/columnas en `utils/db.py` a tu esquema, y corré
`python3 -m streamlit run app.py`. Después extendé con las references.

**Para un dashboard nuevo (entendiendo cada pieza):**
1. Preguntá/definí: ¿qué tablas escribe el bot y con qué esquema? ¿multi-bot o single? ¿qué país/zona?
2. Andá a `references/arquitectura.md` para levantar el esqueleto y elegir el driver (psycopg2 vs pg8000).
3. Montá la capa de datos con `references/db-layer.md` (conexión, `fetch_df`, filtro de fecha+test, timezone).
4. Montá charts/KPIs/estilo con `references/charts-kpis-estilo.md` (elegí piel: claro premium o dark terminal).
5. Repasá `references/convenciones-gotchas.md` **antes de dar por hecho** cualquier cosa.

**Para editar uno existente:** leé el `CLAUDE.md` del repo, luego el archivo que vas a tocar,
y aplicá las convenciones de `references/convenciones-gotchas.md`. Casi todo bug futuro
está listado ahí (timezone, `key=`/`value=`, `px.*` bajo cache, Python 3.9, PII).

## Reglas no negociables (el resto está en las references)

- **Toda** query va en `db.py`, **parametrizada** (`%s` psycopg2 / `:param` SQLAlchemy). Nunca f-strings con datos externos.
- **Timezone siempre `America/Bogota`**: `DATE(created_at AT TIME ZONE 'America/Bogota')`. La DB guarda UTC.
- **Filtrá las cuentas de test/eval** que escriben a las mismas tablas (o contaminan los KPIs).
- **Gráficas con `go.*` + `.tolist()`, nunca `px.*`** cuando hay `@st.cache_data` (px lee el índice, no los valores).
- **Colores desde el dict `COLORS`**, nunca hex hardcodeado. CSS inyectado, no inline por página.
- **Series temporales**: rellenar días sin datos con 0 y fijar el eje X al rango, o un filtro con datos escasos parece roto.
- **PII (teléfonos, datos de menores)**: enmascarar en la UI; exports con datos sensibles solo local/gitignored y por canal privado.

## Templates y references

- `templates/` — dashboard de arranque **listo para copiar y correr** (app.py, db.py, styles.py,
  charts, kpi_row, filters, una página de ejemplo, requirements, config). Ver `templates/README.md`.
- `references/arquitectura.md` — esqueleto de archivos, stack, elección de driver, deployment.
- `references/db-layer.md` — patrón de `db.py` con snippets (conexión, `fetch_df`/`execute`, `_date_filter`, timezone, filtro de test, multi-bot).
- `references/charts-kpis-estilo.md` — fábrica de gráficas, KPI cards, dict COLORS, inyección de CSS, las dos pieles visuales.
- `references/convenciones-gotchas.md` — todas las reglas obligatorias y las trampas conocidas.
- `references/reportes.md` — patrón complementario: reporte Excel + narrativa LLM, envío por cron (repo gemelo).
