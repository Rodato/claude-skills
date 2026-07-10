# Anonimización de datos AMA — referencia

Detalle de los patrones que codifica la skill `ama-pii`. Ejemplos vivos en el repo (leelos
antes de inventar): `Lineabase2026/tablero/scripts/anonimizar.py`,
`Lineabase2026/tablero/scripts/exportar_bot.py`,
`Lineasalida2026/lago-agrio/dashboard/lib/coverage.py`.

## Allowlist vs blocklist

**Siempre allowlist.** El artefacto seguro se **regenera** desde el crudo dejando pasar solo las
columnas que la app necesita; todo lo demás se descarta por defecto.

| | Blocklist (❌ frágil) | Allowlist (✅ segura) |
|---|---|---|
| Regla | "quitar estas columnas PII" | "dejar solo estas columnas útiles" |
| Columna nueva en el crudo | **se cuela** (no está en la lista de quitar) | queda fuera por defecto |
| Falla | silenciosa (leak) | segura (a lo sumo falta un dato útil) |

Patrón de `anonimizar.py`: arma `columnas` = variables graficables + `ciudad/grupo/sexo`, y antes
de escribir hace un **assert de seguridad** que aborta si una PII conocida se coló en la salida:

```python
PII = {"ADM_01", "ADM_02", "DEM_01", "DEM_02", "DEM_03", "DEM_04", ...}   # códigos identificadores
columnas = [c for c in columnas if c in df.columns]         # allowlist real
fuga = set(columnas) & PII
if fuga:
    raise SystemExit(f"ABORTADO — columnas PII en la salida: {sorted(fuga)}")
df[columnas].to_csv(OUT_CSV, sep=";", index=False)          # solo lo permitido sale
```

`exportar_bot.py` hace lo mismo bajando de Kobo: proyecta `SAFE_COLS + FREE_TEXT_COLS` y
`assert not (PII & set(df.columns))` (con `PII = {"Nombre_completo", "N_mero_de_celular_WhatsApp"}`).

## `_redactar_pii` — red de seguridad en texto libre

Las columnas abiertas (comentarios, "¿por qué?") no se pueden allowlistear por nombre: **el
contenido** puede traer un teléfono o correo que el encuestado escribió. Antes de escribirlas, se
pasan por un filtro regex que redacta y avisa (así una re-corrida con datos nuevos no filtra):

```python
_RE_TEL   = re.compile(r"(?:\+?\d[\d .\-]{6,}\d)")     # teléfono con o sin separadores
_RE_EMAIL = re.compile(r"[\w.\-]+@[\w.\-]+\.\w+")      # correo

def _redactar_pii(texto):
    if not isinstance(texto, str) or not texto.strip():
        return texto, False
    nuevo = _RE_EMAIL.sub("[correo removido]", texto)
    nuevo = _RE_TEL.sub("[número removido]", nuevo)
    return nuevo, (nuevo != texto)   # (texto_limpio, hubo_pii)
```

`scan_pii.py` usa las mismas familias de regex para **verificar** (no redactar) el artefacto
final: si el scan marca `tel`/`email`/`doc` en una columna abierta, quedó PII sin redactar.

## Patrón HMAC — cruzar identidades sin exponerlas

Problema: hay que saber si una persona de la **línea base** volvió a responder en el **endline**,
pero el dashboard es público. Solución: no exportar el nombre/documento, exportar su **HMAC-SHA256
salteado**. Reversible solo con el salt, que vive en secrets y nunca en el repo.

```python
import hmac, hashlib, secrets

salt = secrets.token_hex(32)   # generar UNA vez; a secrets (local .toml + Streamlit Cloud)

def hmac_key(salt: str, value: str | None) -> str | None:
    if not isinstance(value, str) or not value:   # NaN de pandas es truthy → isinstance, no `if v`
        return None
    return hmac.new(salt.encode(), value.encode(), hashlib.sha256).hexdigest()
```

Diseño (de `coverage.py`):

- Se exporta `dashboard/data/baseline_keys.parquet` con **solo**: `codigo` (pseudónimo AMA),
  `ciudad`, `colegio`, `grado`, `grupo`, `hash_doc`, `hash_namecol`. Cero texto plano.
- El dashboard hashea el endline live con el **mismo salt** y cuenta coincidencias exactas ⇒
  **cota mínima** de cobertura (sin fuzzy ni teléfono, que no se pueden hashear exacto).
- El cruce completo con PII (fuzzy `difflib`, teléfono, nominal de faltantes con nombre/documento)
  se genera aparte y vive **solo** en `outputs/` (gitignored). Nunca toca el dashboard.
- Rotar el salt ⇒ regenerar el parquet. Mismo salt en el script generador y en el deploy.

Antes de commitear el parquet, correr `scan_pii.py` sobre él exportado a CSV (o inspeccionar las
columnas): solo debe haber `codigo` + hashes, ningún nombre/documento en claro.

## Reducción de cuasi-identificadores (destino público)

Sin nombre, un menor todavía se re-identifica por la combinación de atributos. Si el destino es
público, antes de publicar:

- **Binear** variables continuas: edad → rangos (`14-15`, `16-17`…), no el valor exacto.
- **Quitar** cuasi-identificadores finos: etnia, nivel socioeconómico/estrato, lengua materna,
  religión, orientación.
- **Solo agregados**: contar por género/ciudad/colegio, nunca exponer la fila individual.
- Preferir umbral de celda mínima (p. ej. no mostrar celdas con < 5 personas) para no aislar casos.

`scan_pii.py` **avisa** estos cuasi-identificadores (`edad`, `etnia`, `estrato`, `lengua`…) pero
**no** hace fallar el gate — la decisión de reducirlos depende de si el destino es público. La PII
directa sí falla el gate siempre.

## Después del push: verificar el remoto

```bash
git ls-files | grep -Ei 'crudo|unificad|raw|kobo/|outputs/|_pii'   # nada sensible debería salir
git log --oneline --stat -1                                        # qué archivos entraron
```

Si un crudo se coló, **no** alcanza con borrarlo en un commit nuevo (queda en el historial):
reescribir con `git filter-repo` y rotar cualquier identificador/secreto expuesto. Un push a un
repo público, además, puede haber quedado en cachés/índices de terceros.
