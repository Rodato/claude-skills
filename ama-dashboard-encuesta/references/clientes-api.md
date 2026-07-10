# Clientes API — Typeform (`db.py`) y Kobo (`kobo.py`)

Cada fuente tiene su cliente en `lib/`. Ambos siguen el mismo esqueleto: **una llamada paginada
cacheada 30s** trae todo, y las funciones derivan DataFrames in-memory dentro de esa ventana.
El objetivo de los dos es emitir el mismo contrato: `responses` + una función de completitud +
`get_identities` (para cobertura).

> **No repliques el parseo de memoria.** Los gotchas finos de Kobo/Typeform (separador `;`,
> `_submission_time` vs `start`, matrices, IDs placeholder, respuesta múltiple) viven en la skill
> **`ama-kobo`** — cruzá con ella. Acá está el patrón del **cliente de dashboard** (cache,
> paginación, contrato), no el diccionario de campos.

## Regla de oro: todo detrás de `@st.cache_data(ttl=30)`

Nunca `httpx.get` suelto en `app.py`. El token sale de `st.secrets`, no de un parámetro:

```python
TYPEFORM_API = "https://api.typeform.com"
def _token() -> str:
    return st.secrets["TYPEFORM_TOKEN"]
```

Cache en dos niveles distintos:
- **definición del form** (`get_form_definition` / `get_asset`) → `ttl=60` (cambia poco).
- **respuestas/envíos** (`_fetch_all` / `_fetch`) → `ttl=30` (es el dato vivo).

## Cliente Typeform (`db.py`)

### Paginación

Typeform pagina con cursor `before` = token del último item. Se para cuando la página trae menos
de `page_size`:

```python
@st.cache_data(ttl=30, show_spinner="Trayendo respuestas de Typeform…")
def _fetch_all(form_id: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    response_rows, answer_rows, before = [], [], None
    with httpx.Client(headers={"Authorization": f"Bearer {_token()}"}, timeout=60) as client:
        while True:
            params = {"page_size": 1000, "sort": "submitted_at,desc"}
            if before:
                params["before"] = before
            r = client.get(f"{TYPEFORM_API}/forms/{form_id}/responses", params=params)
            r.raise_for_status()
            items = r.json().get("items") or []
            if not items:
                break
            for item in items:
                item.setdefault("form_id", form_id)
                resp_row, ans_rows = normalize_response(item)   # normalize.py
                response_rows.append(resp_row)
                answer_rows.extend(ans_rows)
            before = items[-1].get("token")
            if len(items) < 1000:
                break
    ...
```

Devuelve **dos** DataFrames: `responses` (una fila por envío) y `answers` (una fila por respuesta,
plana). `normalize.py::normalize_response` convierte cada `form_response` en `(response_row, [answer_rows])`;
`normalize_answer` mapea cada tipo Typeform a columnas `value_text/value_number/value_choice/...`.

### Hidden fields via `field_refs` (Typeform no tiene encuestador nativo)

El form de AMA **no tiene hidden fields nativos**: "encuestador", "colegio", "barrio" son
preguntas regulares. Se mapean a columnas `hidden_*` con la config `[field_refs]` de secrets, así
las vistas que esperan `hidden_colegio` funcionan sin cambios:

```python
def _attach_field_refs_as_hidden(responses, answers):
    mapping = _field_ref_map()          # lee secrets [field_refs] → {nombre: ref}
    for name, ref in mapping.items():
        sub = answers[answers["field_ref"] == ref]
        # Primer valor no-nulo por preferencia de columna.
        # NO usar `or`: NaN es truthy en pandas.
        v = sub["value_choice"]
        for col in ("value_text", "value_number", "value_date", "value_file_url"):
            v = v.where(v.notna(), sub[col])
        m = pd.Series(v.values, index=sub["response_id"].values)
        responses[f"hidden_{name}"] = responses["response_id"].map(m)
    return responses
```

### `get_identities` — identidad por respuesta (para cobertura)

Localiza las preguntas de identidad **por título** (`_classify_identity`: "apellido"→apellido1/2,
"documento/dni/cédula"→documento, etc.), arma `nombre` juntando nombre1+nombre2+apellido1+apellido2,
y devuelve el esquema común que espera `coverage.py`:

```
response_id, submitted_at, ciudad, colegio, grado, nombre, documento, telefono, correo, fuente
```

La ciudad es fija `"lago_agrio"` (el form Typeform es solo de ahí); `fuente="typeform"`.

## Cliente Kobo (`kobo.py`)

Espejo de `db.py`. Diferencia estructural: los envíos de Kobo son **dicts planos con claves
`grupo/pregunta`** (`datos_colegio/colegio_final`, `phq9/phq_1`) — el último segmento es el `name`
del XLSForm.

### `get_asset` — parsea el survey a preguntas reales + mapas de etiquetas

Recorre el `content.survey` manteniendo una **pila de grupos** para reconstruir `grupo/pregunta`,
saltando los tipos que no son preguntas contestables:

```python
_SKIP_TYPES = {"note", "calculate", "start", "end", "today",
               "begin_group", "end_group", "begin_repeat", "end_repeat", "audit", "deviceid"}

stack = []
for row in survey:
    rtype, name = row.get("type"), row.get("name")
    if rtype in ("begin_group", "begin_repeat"):
        if name: stack.append(name)
        continue
    if rtype in ("end_group", "end_repeat"):
        if stack: stack.pop()
        continue
    if rtype in _SKIP_TYPES or not name:
        continue
    full_key = "/".join([*stack, name]) if stack else name
    questions.append({"name": name, "full_key": full_key, "label": ...})
```

Construye mapas `value→label` para colegio, ciudad y grado (leyendo las listas `choices` del
XLSForm). `colegio_final`/`grado_final` son `calculate` (coalesce por ciudad/branching), así que
sus valores se etiquetan uniendo las listas de las variantes.

### `_fetch` — paginación por `next`

Kobo pagina siguiendo la URL `next` de la respuesta:

```python
@st.cache_data(ttl=30, show_spinner="Trayendo envíos de KoboToolbox…")
def _fetch(uid):
    url = f"{_base()}/api/v2/assets/{uid}/data/?format=json&limit=30000"
    with httpx.Client(headers=_headers(), timeout=120) as client:
        while url:
            r = client.get(url); r.raise_for_status()
            page = r.json()
            records.extend(page.get("results") or [])
            url = page.get("next")
```

Deja `responses` con `response_id` (`_uuid` o `_id`), `submitted_at` (`_submission_time`, UTC),
`hidden_colegio` (código → etiqueta) y `hidden_ciudad`. **Kobo no tiene encuestador**
(`_submitted_by=None`, envíos web) → por eso el dashboard añade el filtro CIUDAD y el KPI cae a
"COLEGIOS" en vez de "ENCUESTADORES".

### `_suffix` — leer un campo tolerando el prefijo de grupo

El anidamiento de las claves puede variar; se busca exacto y si no, cualquier clave que termine en
`/<name>`. **Sin `or`** (NaN truthy):

```python
def _suffix(rec, name):
    if name in rec and _nonempty(rec[name]):
        return rec[name]
    tail = "/" + name
    for k, v in rec.items():
        if k.endswith(tail) and _nonempty(v):
            return v
    return None
```

### `completion_by_label` — completitud agrupada por etiqueta

Este es el corazón de la completitud en Kobo. Agrupa preguntas **por etiqueta exacta**, así el
branching condicional colapsa a una fila: las ~15 variantes de "¿En qué grado estás?"
(`grado_<ciudad>_<colegio>`) y las 2 de colegio quedan como **una** pregunta. Una pregunta cuenta
como respondida si **cualquiera** de sus claves tiene valor no vacío:

```python
def completion_by_label(asset, records, response_ids):
    label_keys = defaultdict(list)      # etiqueta → [full_key, ...]
    for q in asset["questions"]:
        label_keys[q["label"]].append(q["full_key"])
    total = len(set(response_ids))
    recs = [r for r in records if _rid(r) in set(response_ids)]
    rows = []
    for label in label_order:           # conserva orden del form
        keys = label_keys[label]
        n = sum(1 for r in recs if any(_nonempty(r.get(k)) for k in keys))
        rows.append({"pregunta": label, "respondidas": n, "total": total,
                     "pct": round(n / total * 100, 1)})
    return pd.DataFrame(rows)
```

Devuelve `[pregunta, respondidas, total, pct]` — **idéntico** a la versión Typeform.

## El equivalente Typeform: `completion.py::completion_by_question`

Misma forma de salida, pero agrupa por **título exacto** y maneja matrices. En una `matrix` de
Typeform, las answers llegan con el `field_id` de cada **subpregunta** (fila), no del contenedor,
así que `_all_ids` incluye los subfields:

```python
def _all_ids(field):
    ids = {field["id"]}
    for sf in (field.get("properties") or {}).get("fields") or []:
        if "id" in sf:
            ids.add(sf["id"])       # subpreguntas de matrix/group
    return ids
```

Una matriz cuenta como respondida si la persona contestó **al menos una fila**. Si Typeform agrega
otros tipos de container (group, etc.), revisar esta función.

## `get_identities` (Kobo) — mismo esquema que Typeform

Devuelve las mismas columnas (`response_id, submitted_at, ciudad, colegio, grado, nombre,
documento, telefono, correo, fuente`) con `fuente="kobo"`, leyendo los datos personales crudos de
los `records` con `_suffix`. La normalización y el match viven en `coverage.py`, no acá.

## Diferencias Typeform vs Kobo — resumen

| | Typeform (`db.py`) | Kobo (`kobo.py`) |
|---|---|---|
| Estructura del envío | anidado (answers por field) | dict plano `grupo/pregunta` |
| Paginación | cursor `before` (token) | URL `next` |
| Encuestador | sí (pregunta → `hidden_encuestador`) | **no** (`_submitted_by=None`) |
| Ciudad | fija (Lago Agrio) | `hidden_ciudad` (Iquitos + Lago Agrio) |
| Hidden fields | via `[field_refs]` de secrets | derivados de `grupo/pregunta` |
| Completitud | `completion_by_question` (por título, `_all_ids` para matrices) | `completion_by_label` (por etiqueta) |
| KPI adaptativo | "ENCUESTADORES" | "COLEGIOS" + filtro CIUDAD |
