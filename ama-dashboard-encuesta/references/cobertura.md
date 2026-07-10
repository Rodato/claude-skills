# Cobertura — tab COBERTURA vs línea de base

El tab COBERTURA responde lo esencial del endline: de los que medimos en la **línea de base**
(grupo **Tratamiento**), ¿a cuántos re-alcanzamos en la salida y quiénes faltan. Motor:
`lib/coverage.py`. Los CLIs offline están en `scripts/`.

> El detalle fino de por qué la PII nunca sale al dashboard, y las reglas de anonimización, viven
> en la skill **`ama-pii`**. Los informes Excel derivados siguen **`ama-excel`**. Acá está solo lo
> que el dashboard necesita.

## La regla de oro: PII nunca toca el dashboard público

La lista nominal de faltantes (nombre, documento, teléfono) **jamás** llega al dashboard. El
reparto es:

- **Dashboard público** ← lee `dashboard/data/baseline_keys.parquet`: solo **llaves HMAC** de la
  base (código AMA, ciudad, colegio, grado, grupo, `hash_doc`, `hash_namecol`). Sin texto plano —
  seguro de commitear.
- **Reporte de campo (PII)** ← vive en `outputs/` (**gitignored**): `faltantes.csv`,
  informes Excel. Lo genera `scripts/cruce_cobertura.py` offline.

## Cómo funciona la cobertura live (en `app.py`)

`load_coverage()` (cacheada `ttl=30`) lee el parquet de llaves, arma la identidad live del endline
(Kobo + Typeform) y cruza por HMAC:

```python
keys = pd.read_parquet(BASELINE_KEYS_PATH)         # llaves HMAC de la base
frames = []
if uid and st.secrets.get("KOBO_TOKEN"):    frames.append(kobo.get_identities(uid))
if fid and st.secrets.get("TYPEFORM_TOKEN"): frames.append(get_identities(fid))
endline = build_endline_identities(*frames)        # une + normaliza + dedup
cov_df = coverage_from_keys(keys, endline, salt)   # marca alcanzado por match exacto de HMAC
```

Devuelve por colegio/ciudad; el tab pinta KPIs (meta, alcanzados, %, faltan), barra global,
métricas por ciudad, barras h por colegio (color `RED<30 / AMBER 30-70 / GREEN≥70`) y tabla detalle.

## Es una COTA MÍNIMA

`coverage_from_keys` solo hace **match exacto de HMAC** (documento o nombre+colegio), porque un
hash no se puede comparar fuzzy. El reporte offline (`scripts/cruce_cobertura.py`) hace el cruce
completo con más métodos y es la cifra buena. El dashboard lo dice explícito en el caption:
"COTA MÍNIMA".

## El motor de match (`coverage.py`) — para el reporte offline

`match()` marca cada persona de la base como alcanzada, con una **cascada** de métodos (el
documento solo está en ~70% de la base, por eso el fuzzy de nombre es imprescindible):

1. **documento** normalizado (`norm_doc`).
2. **nombre+colegio exacto** (`norm_name` order-independiente + `norm_colegio` canónico).
3. **nombre+colegio fuzzy** (`difflib.SequenceMatcher ≥ 0.88`).
4. **teléfono** como desempate (`norm_phone`, últimos 9 dígitos).

### Normalización — los gotchas que importan

- **IDs placeholder** (`norm_doc` → `_is_placeholder_doc`): los encuestadores tipean rellenos
  cuando no tienen la cédula (`11111111`, `12345678`, `99999999999`, `123456`). Si se trataran como
  documento, el dedup colapsaría personas distintas. `norm_doc` los descarta (todo-mismo-dígito o
  secuencia) → cuentan como "sin documento". (Este gotcha también está en `ama-kobo`.)
- **NaN truthy** (mordió dos veces acá): en `build_endline_identities::_pkey` el chequeo es
  `isinstance(r["ndoc"], str)`, **no** `if r["ndoc"]` — un `NaN` de pandas es truthy y colapsaría
  todo a una sola llave. Misma convención (`ok = isinstance(v, str) and bool(v)`) en `match()`.

```python
def _pkey(r):
    # isinstance, no `if v`: NaN de pandas es truthy y colapsaría todo a una llave.
    if isinstance(r["ndoc"], str) and r["ndoc"]:
        return r["ndoc"]
    if isinstance(r["nname"], str) and r["nname"] and isinstance(r["ncolegio"], str) and r["ncolegio"]:
        return f"{r['nname']}|{r['ncolegio']}"
    return f"rid:{r['response_id']}"   # sin llaves → no colapsar con otros
```

## HMAC — cómo se generan y consumen las llaves

`build_baseline_keys(baseline, salt)` produce la tabla commiteable: por persona, `hash_doc` y
`hash_namecol` son HMAC-SHA256 de las llaves normalizadas. `coverage_from_keys` hashea el endline
live con **el mismo salt** y cuenta coincidencias:

```python
def _hmac(salt, value):
    if not isinstance(value, str) or not value:
        return None
    return hmac.new(salt.encode(), value.encode(), hashlib.sha256).hexdigest()
```

El **salt** (`COVERAGE_SALT`) vive en secrets (local + Streamlit Cloud), **no se commitea**. Debe
ser el **mismo** con que se generó el parquet. Si lo rotás, **regenerá el parquet**.

## Regenerar el cruce

```bash
COVERAGE_SALT=... .venv/bin/python scripts/cruce_cobertura.py
```

Produce en `outputs/` (gitignored, PII): `faltantes.csv` (nominal, para campo),
`cobertura_resumen.csv` (agregado anónimo), `endline_no_en_base.csv` (QA: endline en colegios
Tratamiento sin match). Y reescribe `dashboard/data/baseline_keys.parquet`.

## Dos lecturas que no hay que confundir

- **Cobertura** (uno-a-uno): enlaza persona a persona; **subestima por diseño** (documento falta en
  ~30% de la base, los nuevos no suman). Es lo que mide impacto/seguimiento.
- **Volumen / agregado** (`informe_salida_excel.py`, `informe_base_vs_salida_excel.py`): cuenta
  cuántos respondieron por colegio, sin enlazar. Es la lectura honesta del avance. Un colegio puede
  pasar 100% al incluir estudiantes nuevos.

Que un registro caiga en "de más" **no** implica que sea ajeno a la base — casi siempre es alguien
que sí estaba pero cuyo registro no cruzó (documento distinto, nombre escrito de otra forma). Es
material de **revisión manual**, no un conteo de "nuevos".

**Camilo Gallegos — Typeform+Kobo = COMPLEMENTO, no duplicado** (confirmado por campo): ese colegio
se encuestó por los dos canales cubriendo cursos distintos. **NO deduplicar entre fuentes** ni
tratar su footprint alto como inflado.
