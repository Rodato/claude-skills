---
name: ama-kobo
description: >-
  Convenciones para ingerir y validar datos de encuestas del programa AMA
  (Estudio Plural) desde KoboToolbox, Typeform y las listas de asistencia de
  Google Form. Úsala al bajar, leer, limpiar, cruzar o validar cualquiera de
  esas encuestas — línea base (Leticia/Cobija) o línea de salida
  (Iquitos/Lago Agrio) — para que los gotchas no obvios (separador `;`,
  `_submission_time` vs `start`, columnas de grado duplicadas, respuesta
  múltiple pegada por comas o por espacios, IDs placeholder, NaN truthy,
  matrices de Typeform) no se reinventen ni se rompan en cada sesión.
---

# AMA Kobo — ingesta y validación de encuestas AMA

Receta reutilizable para **leer, validar y cruzar** las encuestas del programa
**AMA: Habilidades para navegar la vida** (Estudio Plural). Las fuentes son tres
—KoboToolbox, Typeform y Google Form de asistencia— y cada una tiene trampas que
cuestan horas si se olvidan. Esta skill las concentra y apunta al código real que
ya las resuelve.

## Cuándo usarla

- Bajar datos de la API de Kobo o Typeform (token + asset/form UID).
- Leer un CSV/export de Kobo en pandas sin corromper IDs ni fechas.
- Validar calidad: IDs placeholder, outliers de duración, timestamps corruptos.
- Cruzar asistencia (Google Form) contra encuestas Kobo (faltantes, conteos).
- Descomponer preguntas de **respuesta múltiple** (comas vs espacios).
- Unificar/mapear preguntas entre ciudades o entre línea base y línea de salida.

## Proyectos de referencia (leé el código real antes de inventar)

Dos proyectos vivos, misma familia de datos con distinta piel. Cada uno tiene su
`CLAUDE.md` extenso — **léelo primero** cuando trabajes sobre uno.

| | Línea base 2026 | Línea de salida 2026 |
|---|---|---|
| Ruta | `~/Documents/Dev/AMA/Lineabase2026/` | `~/Documents/Dev/AMA/Lineasalida2026/lago-agrio/` |
| Ciudades | Leticia (CO), Cobija (BO) | Iquitos (PE), Lago Agrio (EC) |
| Fuentes | Kobo (CSV export) + Google Form asistencia | Kobo (API JSON) + Typeform (API) |
| Consumo | Scripts CLI (validación, Excel, LLM) | Dashboard Streamlit en vivo (cache 30s) |
| Multi-respuesta | comas (Iquitos) · **espacios** (Cobija/Leticia) | vía completitud por etiqueta |

Preprocesamiento original (Iquitos + Lago Agrio) vive en
`~/Documents/Dev/AMA/Preprocesamiento/` — es el esquema madre que replican
`Lineabase2026/src/preprocess.py` y `unify_surveys.py`.

## Qué fuente da qué (mapa mental)

| | **KoboToolbox** | **Typeform** | **Google Form (asistencia)** |
|---|---|---|---|
| Cómo llega | CSV export (`sep=';'`) o API JSON | API JSON paginada | CSV descargado |
| Clave temporal | `_submission_time` (filtrar) · `start`/`end` (duración) | `submitted_at` · `landed_at` (duración) | `Marca temporal` (filtrar) |
| Identificador envío | `_uuid` / `_id` | `token` / `response_id` | fila |
| Forma del registro | dict plano `grupo/pregunta` (API) o columnas (CSV) | answers con `field_ref`/`field_id` | columnas fijas |
| Rol en AMA | encuesta principal = **fuente de verdad** | encuesta (Lago Agrio, canal paralelo) | quién asistió (para cruzar) |
| Multi-respuesta | `multiple_select=both`: 1 col unida + N binarias | matrices = 1 answer por subpregunta | — |

En Lago Agrio, **Typeform y Kobo son complemento, no duplicado** (cubren cursos
distintos del mismo colegio) → no deduplicar entre fuentes. Ver
`Lineasalida2026/lago-agrio/CLAUDE.md`.

## La receta en breve

1. **Bajar** (si aplica): `fetch_kobo.py` (Kobo API → CSV con el formato de la UI)
   o los clientes `lib/kobo.py` / `lib/db.py` (API → DataFrame in-memory).
   → `references/api-clients.md`.
2. **Leer** el CSV: `sep=';'`, `dtype=str` (o al menos la columna ID como str),
   resolver la columna de grado duplicada con `bfill`, formatear grado.
   → `references/lectura-kobo.md`.
3. **Validar**: IDs placeholder/longitud, outliers de duración (media − 3σ por
   salón), timestamps corruptos, cruce asistencia↔Kobo, faltantes.
   → `references/validacion.md`.
4. **Descomponer** respuesta múltiple según la fuente (comas o espacios).
   → `references/multi-respuesta.md`.

## Reglas no negociables (el resto está en las references)

- **Leé el CSV Kobo con `sep=';'` y `dtype=str`** (o `dtype={id_col: str}`). El
  `;` es el separador real; `dtype=str` preserva **ceros a la izquierda** en los
  IDs, que se pierden como número.
- **Filtrá por fecha con `_submission_time`, nunca con `start`.** La encuesta se
  abre en la mañana y se sube en la noche del mismo día → `start` puede caer en un
  día distinto. `start`/`end` **sí** sirven para calcular la duración.
- **La columna de grado viene duplicada** (`¿En qué grado estás?`, `.1`, `.2`…)
  porque distintas escuelas usan distintas versiones del form. Unificá con `bfill`
  (`resolve_grade_col` / `_grade_merged` / `resolve_dup_column`). Nunca asumas una
  sola columna.
- **Multi-respuesta: Iquitos separa por comas, Cobija/Leticia por espacios.** Para
  espacios hay que descomponer por *greedy longest-match* contra las etiquetas del
  XML del form (`<value>…</value>`), no por `split`. → `references/multi-respuesta.md`.
- **NaN de pandas es truthy.** Nunca `r.get(a) or r.get(b)` para coalescer ni
  `if v:` para chequear un string. Usá `isinstance(v, str)` / `pd.notna` /
  `.where(v.notna(), otra)`. Esto ya rompió el dedup de cobertura y el mapeo de
  hidden fields.
- **Google Form asistencia: filtrá por `Marca temporal`, NO por `Fecha de
  aplicación`** (tiene typos con años 2007-2011).
- **IDs placeholder** (todos el mismo dígito, o secuencia `12345678`) = inválidos y
  se descartan del match; longitud esperada por ciudad (Leticia 10, Cobija 7-8).
- **Nombres de escuela**: quitar sufijo `" (Ciudad / País)"` con `normalize_school`;
  sedes parecidas **NO** se unifican (`"Antonio Vaca Diez"` ≠ `"Dr Antonio Vaca
  Diez"`). Kobo es la fuente de verdad; `SCHOOL_CORRECTIONS` corrige el Form.
- **PII de menores**: los datos crudos (nombre, documento, teléfono, correo,
  dirección) **nunca** se versionan ni se despliegan. Anonimizar antes de cualquier
  push/deploy. Esto lo cubre la skill hermana **`ama-pii`** — respetala siempre.

## Convenciones del usuario

- Siempre `python3` (no `python`). Comentarios en español, código/identificadores
  en inglés.
- Al iniciar un repo nuevo, preguntar si va a `Rodato` personal o a la org
  `Estudio-Plural` antes de `gh repo create`/push.

## References

- `references/lectura-kobo.md` — parseo de CSV Kobo: `sep`/`dtype`, filtro por
  `_submission_time`, columna de grado duplicada (`bfill`), `format_grade`.
- `references/validacion.md` — IDs placeholder, outliers de duración (media − 3σ,
  `MAX_DURATION_H=8`, `STD_MULTIPLIER=3`), timestamps corruptos, crosscheck
  asistencia↔Kobo, `find_missing_students`.
- `references/multi-respuesta.md` — comas vs espacios, greedy longest-match contra
  el XML, `multiple_select=both` (col unida + binarias), validación >2 respuestas.
- `references/api-clients.md` — fetch Kobo (token/asset, export async), cliente
  Typeform (paginación, `field_refs` como hidden, matrices), `get_identities`.

## Skills hermanas

- **`ama-pii`** — anonimizar/verificar sin PII de menores antes de push/deploy.
- **`ama-excel`** — Excels de seguimiento/informe (openpyxl) del pipeline AMA.
- **`ama-graficas-informe`** — gráficas estilo informe (barras por género, 300dpi).
- **`ama-dashboard-encuesta`** — tableros Streamlit de encuestas (línea base/salida).
- **`bot-dashboard`** — dashboards de monitoreo del bot AMA sobre Supabase.
