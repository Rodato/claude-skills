# Clientes de API: Kobo y Typeform

Cómo bajar datos directo de las APIs. Fuentes: `Lineabase2026/src/fetch_kobo.py`
(export async a CSV), `Lineabase2026/tablero/scripts/exportar_bot.py` (data JSON
plano), y los clientes del dashboard `Lineasalida2026/lago-agrio/dashboard/lib/`
(`kobo.py`, `db.py`).

## KoboToolbox

### Autenticación

- **Header**: `Authorization: Token <KOBO_API_TOKEN>` (¡`Token`, no `Bearer`!).
- **Base**: servidor global `https://kf.kobotoolbox.org` (`KOBO_BASE_URL`).
- **Asset UID**: uno por formulario/ciudad (`KOBO_ASSET_LETICIA`,
  `KOBO_ASSET_COBIJA`, `KOBO_ASSET_BOT`, etc.). El token está en `.env` /
  `st.secrets`.

```python
def auth_headers(token):
    return {"Authorization": f"Token {token}"}
```

### Dos endpoints, dos formas de bajar

**A. Export async → CSV** (`fetch_kobo.py`, replica el export manual de la UI). Es
un flujo POST + polling:

```python
# 1. POST crea el export → devuelve URL del task
url = f"{base}/api/v2/assets/{uid}/exports/"
r = requests.post(url, headers=auth_headers(token), data=EXPORT_SETTINGS)
task_url = r.json()["url"]

# 2. GET al task hasta status == "complete" → da result URL
# 3. GET al result → CSV (sep=';')
```

`EXPORT_SETTINGS` importa —reproduce el CSV que espera el pipeline—:

```python
EXPORT_SETTINGS = {
    "fields_from_all_versions": "true",   # trae TODAS las versiones → columnas .1 .2
    "group_sep": "/",
    "hierarchy_in_labels": "false",
    "lang": "Spanish (es)",
    "multiple_select": "both",            # col unida + binarias (ver multi-respuesta.md)
    "type": "csv",
}
```

`fields_from_all_versions=true` es justo lo que **crea las columnas de grado
duplicadas** — es intencional (no perder respuestas de versiones viejas). Se unifican
al leer (ver `lectura-kobo.md`).

**B. Data JSON paginado** (`lib/kobo.py`, `exportar_bot.py`). Cada envío es un **dict
plano** con claves `grupo/pregunta` (`datos_colegio/colegio_final`, `phq9/phq_1`); el
**último segmento** de la clave es el `name` del XLSForm. Paginar siguiendo `next`:

```python
url = f"{base}/api/v2/assets/{uid}/data/?format=json&limit=30000"
while url:
    r = client.get(url)                 # httpx.Client con headers de auth
    page = r.json()
    records.extend(page.get("results") or [])
    url = page.get("next")              # None cuando se acaba
```

### Leer un campo por su `name` tolerando el prefijo de grupo

El anidamiento de grupos puede variar entre versiones del form. Buscar por exacto y,
si no, por sufijo `/<name>`. **No** coalescer con `a or b` (NaN es truthy):

```python
# lib/kobo.py::_suffix
if name in rec and _nonempty(rec[name]):
    return rec[name]
tail = "/" + name
for k, v in rec.items():
    if k.endswith(tail) and _nonempty(v):
        return v
return None
```

### Definición del form (etiquetas)

`get_asset(uid)` (`/api/v2/assets/{uid}/?format=json`) trae `content.survey`
(preguntas ordenadas) y `content.choices` (`list_name → {value: label}`). Al recorrer
el survey, mantener una **pila de grupos** para reconstruir `grupo/pregunta`, y saltar
tipos que no son preguntas reales:

```python
_SKIP_TYPES = {"note","calculate","start","end","today",
               "begin_group","end_group","begin_repeat","end_repeat","audit","deviceid"}
```

Las etiquetas pueden venir como **lista** (una por idioma) → `_first` toma la primera.
`colegio_final` y `grado_final` son `calculate` que coalescen variantes por ciudad;
su etiqueta se resuelve uniendo las listas `escuelas_*` / `grados_*`.

### Completitud por etiqueta (colapsa variantes con branching)

`completion_by_label` agrupa preguntas por **etiqueta exacta**, así las ~15 variantes
de "¿En qué grado estás?" y las 2 de colegio cuentan como **una** pregunta. Una
pregunta cuenta como respondida si **cualquiera** de sus claves tiene valor no vacío.

## Typeform

### Autenticación y paginación

- **Header**: `Authorization: Bearer <TYPEFORM_TOKEN>` (acá sí `Bearer`).
- **Base**: `https://api.typeform.com`. Form def: `/forms/{id}`; respuestas:
  `/forms/{id}/responses`.
- Paginar con cursor `before = items[-1].token` (orden `submitted_at,desc`),
  `page_size=1000`, hasta que la página venga con menos de 1000 items.

### Hidden fields que en realidad son preguntas

El form de Lago Agrio **no tiene hidden fields nativos**. Encuestador/colegio/barrio
son preguntas normales; se mapean a columnas `hidden_<nombre>` vía
`secrets.toml::field_refs` (`{nombre: ref}`). Al pegarlos hay que coalescer varias
columnas de valor **sin usar `or`** (NaN es truthy):

```python
# db.py::_attach_field_refs_as_hidden
v = sub["value_choice"]
for col in ("value_text", "value_number", "value_date", "value_file_url"):
    v = v.where(v.notna(), sub[col])       # NO: sub["value_choice"] or sub["value_text"]
m = pd.Series(v.values, index=sub["response_id"].values)
responses[f"hidden_{name}"] = responses["response_id"].map(m)
```

### Matrices: un answer por SUBpregunta

Las preguntas tipo `matrix` mandan answers con el `field_id` de cada **subpregunta**
(fila), no del contenedor. Para completitud/lectura hay que aplanar los fields
(Typeform anida preguntas dentro de `group`/matrix) e incluir los subfields:

```python
# db.py::_flatten_fields (recursivo)
sub = (f.get("properties") or {}).get("fields")
if sub:
    out.extend(_flatten_fields(sub))
```

### Duración

`duration_seconds = submitted_at − landed_at`. Ambos se parsean
`pd.to_datetime(..., utc=True, errors="coerce")`.

## Vista agnóstica de la fuente

Los dashboards normalizan Kobo y Typeform a un mismo esquema para que las vistas no
sepan de dónde viene el dato:

- `responses`: `response_id`, `submitted_at` (tz-aware), `hidden_*` opcionales.
- `get_identities()` (en ambos clientes): `response_id, submitted_at, ciudad,
  colegio, grado, nombre, documento, telefono, correo, fuente`. Devuelve strings
  **crudos** (la normalización y el match viven en `coverage.py`).
- Kobo `_submitted_by = None` (envíos web, sin encuestador) → el dashboard usa
  filtro por **ciudad**; Typeform sí tiene `hidden_encuestador` (datos sucios,
  no normalizados aún).

## PII

Todos estos clientes tocan PII de menores (nombre, documento, teléfono, correo). Al
exportar a un CSV que se va a versionar, proyectar **solo** columnas agregables y
correr el filtro anti-PII (`exportar_bot.py::_redactar_pii` redacta teléfonos/correos
del texto libre y un `assert` bloquea si se cuela `Nombre_completo` /
`N_mero_de_celular_WhatsApp`). Ver skill hermana **`ama-pii`**.
