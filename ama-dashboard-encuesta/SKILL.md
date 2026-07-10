---
name: ama-dashboard-encuesta
description: >-
  Receta y convenciones para construir o extender dashboards Streamlit que
  monitorean EN VIVO un levantamiento de encuestas leyendo directo las APIs de
  KoboToolbox y Typeform (sin base de datos intermedia): avance, completitud por
  pregunta y cobertura línea base↔salida. Sigue el patrón del endline de AMA
  (Estudio Plural), cuyo ejemplo canónico es Lineasalida2026/lago-agrio. Usá esta
  skill al arrancar un dashboard de monitoreo de encuestas Kobo/Typeform, o al
  agregarle tabs/vistas/clientes/gráficas — para que el patrón source-agnóstico,
  los clientes con cache, el tema Bloomberg y los gotchas no se reinventen cada
  vez. NO es para bots de WhatsApp sobre Postgres (esa es `bot-dashboard`).
---

# AMA Dashboard Encuesta — monitoreo en vivo de un levantamiento

Receta reutilizable para dashboards operativos de **Streamlit + httpx (Kobo/Typeform API) + Plotly**
que monitorean un **levantamiento de encuestas mientras sucede**: cuántas van, qué preguntas se
saltan, y a cuántos de la línea de base se re-alcanzó. Cubre dos casos:

1. **Arrancar uno nuevo** desde cero (scaffolding + clientes API + vistas + estilo).
2. **Editar uno existente** (agregar fuente, tab, KPI o gráfica) sin romper las convenciones.

## Esta skill vs `bot-dashboard` — cuál usar

Son **dos recetas distintas**. La diferencia es de dónde salen los datos y qué se mide.
Si estás monitoreando un **levantamiento de encuestas** (avance de campo), es ésta. Si estás
monitoreando un **bot de WhatsApp/chat** (uso, conversaciones, alertas), es `bot-dashboard`.

| | **`ama-dashboard-encuesta`** (esta) | **`bot-dashboard`** (hermana) |
|---|---|---|
| Qué monitorea | Avance de un levantamiento de encuestas | Un bot de WhatsApp/chat |
| Fuente de datos | **Kobo + Typeform API en vivo** (httpx) | **Supabase Postgres** (psycopg2 / pg8000) |
| Capa de datos | Clientes API con `@st.cache_data(ttl=30)`, sin DB | `db.py` con queries SQL parametrizadas |
| Persistencia | **Ninguna** — se relee la API en cada refresh | La DB es la fuente de verdad |
| Preguntas clave | ¿cuántas van? ¿qué se salta? ¿a quién falta? | ¿cuánta gente usa? ¿qué conversan? ¿alertas? |
| Refresh | `streamlit-autorefresh` global 30s | Manual / al cambiar filtros |
| Ejemplo canónico | `Lineasalida2026/lago-agrio/dashboard/` | `AMA/Bot_monitoring/`, `aly-dashboard` |
| Estilo | Bloomberg dark terminal (comparten `theme.py`) | Claro premium **o** Bloomberg dark |

Comparten piel (ambos pueden usar el tema Bloomberg de `Bot_monitoring`), pero **no** comparten
capa de datos ni pregunta de negocio. No mezcles: un dashboard de encuesta que empieza a leer de
Postgres ya es el otro caso.

## Implementación de referencia (leé el código real antes de inventar)

El dashboard vivo del **endline de AMA** es la receta completa. Cuando dudes de un patrón, mirá
cómo está resuelto ahí:

- **Repo local**: `~/Documents/Dev/AMA/Lineasalida2026/lago-agrio/`
- **`CLAUDE.md` de ese repo**: la mejor fuente única (stack, estructura, datos del form,
  bugs conocidos, cobertura). **Léelo primero** al trabajar sobre él.
- **App live**: dos fuentes (Typeform / Kobo) con un toggle; tabs AVANCE, COMPLETITUD,
  COBERTURA, BOT.

Esta skill captura lo **común y transferible**; el `CLAUDE.md` tiene el detalle específico de
ese levantamiento (IDs de form, colegios, snapshots de cobertura).

## La receta en una imagen

```
dashboard/
├── app.py                  # entry point: page_config, inject_css, autorefresh 30s,
│                           #   selector de fuente, filtros, tabs AVANCE/COMPLETITUD/COBERTURA
├── data/
│   └── baseline_keys.parquet   # llaves HMAC de la base (SIN PII) para la cobertura live
└── lib/
    ├── db.py               # cliente Typeform (httpx, cache 30s, paginación, get_identities)
    ├── kobo.py             # cliente KoboToolbox (httpx, cache 30s, completion_by_label, get_identities)
    ├── normalize.py        # form_response Typeform → (response_row, [answer_rows])
    ├── completion.py       # % completitud por pregunta Typeform (maneja matrices con _all_ids)
    ├── coverage.py         # motor de cruce base↔endline (normalización, match cascada, HMAC)
    └── theme.py            # CSS Bloomberg + base_layout() Plotly + html_table()
scripts/                    # CLIs offline (PII): cruce de cobertura + informes Excel — NO parte del deploy
.streamlit/
├── secrets.toml            # TYPEFORM_TOKEN/FORM_ID/field_refs, KOBO_*, COVERAGE_SALT (gitignored)
└── secrets.toml.example    # plantilla commiteada
requirements.txt            # httpx, streamlit, streamlit-autorefresh, pandas, plotly
runtime.txt                 # python-3.11
```

Deploy: **Streamlit Community Cloud**, auto-redeploy en push a `main`. **Los datos no se
commitean** — el repo es solo código; las respuestas se releen de la API en cada refresh.
(Ver `references/arquitectura.md`.)

## El patrón central: vistas agnósticas de la fuente

Esto es lo que hace que Typeform y Kobo convivan sin duplicar los tabs. **Cada rama de fuente
produce dos estructuras idénticas en forma**, y los tabs consumen esas dos sin saber de dónde
salieron:

- **`responses`** — un DataFrame con columnas comunes: `response_id`, `submitted_at`
  (**tz-aware**, UTC) y `hidden_*` opcionales (`hidden_colegio`, `hidden_ciudad`,
  `hidden_encuestador`).
- **`comp`** — un DataFrame `[pregunta, respondidas, total, pct]` que devuelve la función
  `compute_comp(df)` de la rama.

```python
# app.py — la rama elige la fuente, pero deja SIEMPRE el mismo contrato.
if fuente == "TYPEFORM":
    responses = get_responses(FORM_ID)
    answers = get_answers(FORM_ID)
    def compute_comp(df):
        return completion_by_question(form_def, answers, df["response_id"].tolist())
else:  # KOBO
    responses = kobo.get_responses(KOBO_UID)
    records = kobo.get_submissions(KOBO_UID)
    def compute_comp(df):
        return kobo.completion_by_label(asset, records, df["response_id"].tolist())

# ── Los tabs AVANCE / COMPLETITUD leen `responses` y `compute_comp(df)`, nunca la fuente. ──
```

Las diferencias entre fuentes se resuelven **preguntando por columnas, no por fuente**:

```python
# 3er KPI adaptativo: Typeform trae encuestador; Kobo no → cae a colegios.
has_encuestador = "hidden_encuestador" in df.columns
if has_encuestador:
    kpi3_label, kpi3_val = "ENCUESTADORES", df["hidden_encuestador"].nunique()
else:
    kpi3_label, kpi3_val = "COLEGIOS", df["hidden_colegio"].nunique()
```

Si agregás una tercera fuente (otra API), tu trabajo es escribir un cliente que emita esas dos
estructuras — no tocar los tabs. Detalle en `references/arquitectura.md` y `references/clientes-api.md`.

## Reglas no negociables (el resto está en las references)

- **Sin base de datos, sin webhooks, sin Airtable.** La fuente de verdad es la API; se relee en
  cada refresh. Es una decisión de stack mínimo, no un pendiente. No introduzcas una DB "para
  cachear" — para eso está `@st.cache_data(ttl=30)`.
- **Toda llamada a la API va detrás de `@st.cache_data(ttl=30)`** en `lib/db.py` (Typeform) o
  `lib/kobo.py` (Kobo). Nunca `httpx.get` suelto en `app.py`. El autorefresh global (30s) + el
  ttl del cache es lo que da el "en vivo" sin martillar la API.
- **Las vistas son agnósticas de la fuente**: consumen `responses` + `compute_comp(df)`. Las
  diferencias se ramifican por **columna presente** (`"hidden_ciudad" in df.columns`), no por
  `if fuente == ...` dentro del tab.
- **`submitted_at` siempre tz-aware** (`pd.to_datetime(..., utc=True)`), y para comparar contra
  "hoy"/"últimas 24h" se usa el tz del propio dato (`df["submitted_at"].dt.tz`), no `datetime.now()` naive.
- **Gráficas con `plotly.graph_objects` (`go.*`)**, nunca `px.*`, y siempre partiendo de
  `base_layout(**kwargs)` de `theme.py`. Colores desde las constantes de `theme.py`
  (`AMBER`, `CYAN`, `GREEN`, `RED`), nunca hex hardcodeado disperso.
- **NaN es truthy en pandas.** Para coalescer columnas usá `.where(notna())` o
  `isinstance(v, str)`, **nunca** `r.get(a) or r.get(b)`. Este bug ya mordió en `db.py`,
  `kobo.py` y `coverage.py` — está documentado en los tres.
- **Tablas y charts largos van en contenedores scrolleables**, no estiran la página:
  `html_table(..., max_height=360)` y `with st.container(height=520): st.plotly_chart(...)`.
- **PII (datos de menores)**: la lista nominal de faltantes **nunca** toca el dashboard público.
  El dashboard solo lee `baseline_keys.parquet` con llaves **HMAC**. La PII vive en `outputs/`
  (gitignored) y se genera con los `scripts/` offline. Ver `references/cobertura.md`.

## Cómo trabajar

**Para un dashboard nuevo:**
1. Definí las fuentes: ¿Typeform, Kobo, ambas? ¿qué form/asset UID? ¿hay línea de base que cruzar?
2. `references/arquitectura.md` para levantar el esqueleto (stack, estructura, secrets, deploy).
3. `references/clientes-api.md` para montar el/los cliente(s) con cache, paginación y el contrato
   `responses` + `comp`. **No repliques el parseo de Kobo/Typeform de memoria** — cruzá con la
   skill `ama-kobo` para los gotchas de la capa de datos (separador `;`, matrices, IDs placeholder).
4. `references/tema-bloomberg.md` para el estilo (copiá `theme.py` tal cual del repo canónico).
5. Si hay cobertura base↔salida, `references/cobertura.md` (y `ama-pii` para el detalle fino de HMAC/PII).

**Para editar uno existente:** leé el `CLAUDE.md` del repo, luego el archivo que vas a tocar, y
respetá el contrato source-agnóstico. Casi todo bug futuro (NaN truthy, matrices, iconos Material,
cold start, `use_container_width`, shebang del `.venv`) ya está listado — en las references y en
la sección "Bugs conocidos" del `CLAUDE.md`.

## References

- `references/arquitectura.md` — stack mínimo (httpx, sin DB), estructura de archivos, el patrón
  source-agnóstico en detalle, secrets, runtime, deploy en Streamlit Cloud.
- `references/clientes-api.md` — patrón de cliente Typeform (`db.py`) y Kobo (`kobo.py`): cache 30s,
  paginación, `hidden_*` via `field_refs`, `completion_by_label`/`completion_by_question`,
  `get_identities`. Diferencias Typeform vs Kobo (encuestador, ciudad).
- `references/tema-bloomberg.md` — `theme.py`: CSS Bloomberg, `base_layout()`, `html_table()`, y los
  dos gotchas de estilo (iconos Material y contenedores scrolleables).
- `references/cobertura.md` — el tab COBERTURA: cruce base↔salida, HMAC, PII, cota mínima, cómo se
  regenera el parquet de llaves. (El detalle fino de PII vive en `ama-pii`.)

## Skills hermanas

- **`bot-dashboard`** — el otro caso (bot de WhatsApp sobre Supabase Postgres). Distinta capa de
  datos y distinta pregunta de negocio; comparte piel Bloomberg. Ver la tabla de arriba.
- **`ama-kobo`** — convenciones de la capa de datos Kobo/Typeform/Google Form (parseo, `_submission_time`
  vs `start`, matrices, IDs placeholder, respuesta múltiple, NaN truthy). **No repitas ese detalle
  acá; referencialo.**
- **`ama-graficas-informe`** — estilo canónico de las gráficas del informe (distribuciones por género,
  paleta fija). Relevante si te piden **distribuciones P31-P46 en vivo** en el dashboard (hoy fuera
  de alcance del endline; sería reusar `variables_encuesta_informe.py` + `generar_graficas_informe.py`).
- **`ama-pii`** — reglas de anonimización, cobertura y HMAC. El detalle de por qué la lista nominal
  nunca toca el dashboard vive ahí.
- **`ama-excel`** — informes descargables (openpyxl, multi-hoja, semáforo, PII). Los `scripts/` de
  cobertura e informes de este repo siguen esas convenciones.
