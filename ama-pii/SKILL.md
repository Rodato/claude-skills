---
name: ama-pii
description: >-
  Guard de anonimización/PII para los datos del programa AMA (Estudio Plural):
  encuestas de menores 14-19 con identificadores directos (nombre, documento,
  teléfono, correo, dirección, fecha de nacimiento) y categorías especiales
  (salud mental PHQ-9/GAD-7, violencia, sustancias). Úsala SIEMPRE antes de un
  `git add`/commit/push o de un deploy a Streamlit Cloud que toque datos AMA, y
  cuando el usuario diga "commit y push", "subir", "publicar datos", "anonimizar",
  "desplegar el tablero/dashboard" o exportar cualquier CSV/Excel del programa —
  para no filtrar PII de menores a un canal outward-facing e irreversible
  (historial git, caché, indexación).
---

# ama-pii — guard de anonimización/PII de AMA

Skill de **seguridad**, no de features. Los CSV crudos de AMA (encuestas Kobo/Typeform de
**menores de 14-19 años**) contienen PII directa —nombre, documento, teléfono, correo,
dirección, fecha de nacimiento— **y** categorías especiales (salud mental PHQ-9/GAD-7,
violencia, sustancias). Un `push` a GitHub o un `deploy` a Streamlit Cloud es
**outward-facing e irreversible**: queda en el historial de git, en cachés y en índices.
Por eso el crudo **nunca** se versiona ni se despliega — sólo el **artefacto anonimizado**.

El usuario ya lo tiene como práctica y valoró explícitamente que se lo blindara de forma
proactiva cuando dijo "commit y push" sin pensarlo. Cuando esta skill aplica, **frená el
push/deploy y corré el checklist** antes de tocar nada.

## Cuándo dispara (obligatorio)

Antes de **cualquiera** de estas acciones, si el material toca datos AMA:

- `git add` / `git commit` / `git push` en un repo de AMA (tablero, dashboard, Preprocesamiento…).
- Deploy o redeploy a **Streamlit Community Cloud** (cada push a `main` redespliega solo).
- Exportar/compartir un CSV o Excel del programa (Kobo, Typeform, Google Form, informes).
- El usuario dice "commit", "push", "subir", "publicar", "anonimizar", "desplegar", "compartir el dashboard".

Ante la duda, **asumí que aplica** y corré el scanner.

## El scanner (corazón de la skill)

`scripts/scan_pii.py` es un guard ejecutable, sólo stdlib (no requiere pandas — así corre en
cualquier entorno, incluido pre-push). Recibe un CSV **o un directorio** y **sale con código
!= 0 si encuentra PII probable**, para poder encadenarlo como gate.

```bash
python3 ~/.claude/skills/ama-pii/scripts/scan_pii.py data/encuesta_anon.csv
python3 ~/.claude/skills/ama-pii/scripts/scan_pii.py data/            # todos los .csv, recursivo
```

Por cada columna reporta, sobre celdas no vacías:

- **email** — celdas que matchean un correo.
- **tel** — secuencias de 7-15 dígitos tolerando `+`, espacios, guiones y puntos.
- **doc** — corridas largas de dígitos (cédula/DNI/tarjeta de identidad).
- **señal** — nombre de columna sospechoso: `nombre`, `documento`, `cédula`, `dni`,
  `teléfono`, `celular`, `whatsapp`, `correo`, `email`, `dirección`, `fecha_nac`… (insensible
  a mayúsculas y acentos) **más** los códigos PII conocidos de AMA (`DEM_01`, `ADM_02`,
  `Nombre_completo`, `N_mero_de_celular_WhatsApp`…). También avisa **cuasi-identificadores**
  (`edad`, `etnia`, `estrato`, `lengua`…) sin hacer fallar el gate.

Detecta el separador `;` o `,` automáticamente y lee todo como texto. Exit codes: `0` sin PII
evidente, `1` PII probable (no subir), `2` error de uso. Detecta PII **incrustada en texto
libre** (un teléfono/correo dentro de un comentario), no sólo columnas identificadoras.

**El scan es una red, no una garantía**: pasar el scan no autoriza el push por sí solo — hay
que haber hecho también el allowlist y revisar cuasi-identificadores. Un scan con hallazgos,
en cambio, **sí bloquea**.

## Checklist antes de cualquier `git add`/push/deploy

1. **Allowlist de columnas, NO blocklist.** Commiteá/desplegá **solo** las columnas que la app
   usa; regenerá el artefacto anonimizado desde el crudo dejando fuera todo lo demás. Una
   allowlist es segura ante columnas nuevas; una blocklist se olvida de la próxima columna PII.
2. **`.gitignore` defensivo** para los crudos (`outputs/`, `data/kobo/`, `*_unificada.csv`…);
   versioná **solo** el artefacto anonimizado.
3. **Repo privado** + acceso restringido si es app. Si querés algo **público**, primero reducí
   cuasi-identificadores: binear la edad, quitar etnia/nivel socioeconómico/lengua, y mostrar
   solo agregados.
4. **Escaneá el contenido** del anonimizado con `scan_pii.py` (emails `@`, secuencias largas de
   dígitos, nombres de columna PII). Exit != 0 ⇒ **no subir**.
5. **Verificá el árbol remoto** tras el push — que no se haya colado el crudo:
   ```bash
   git ls-files | grep -Ei 'crudo|unificad|raw|kobo/|outputs/|_pii'   # no debería devolver nada sensible
   git log --oneline --stat -1                                        # qué entró en el último commit
   ```
   Si se coló, no alcanza con borrarlo en un commit nuevo: hay que **reescribir el historial**
   (`git filter-repo`) y rotar cualquier secreto/identificador expuesto.
6. **Cruces/llaves con HMAC salteado**, nunca el identificador en claro. Salt con
   `secrets.token_hex(32)`, guardado en secrets (local + Cloud), **no** en el repo. Ver abajo.
7. **Solo agregados** (por género/ciudad/colegio), nunca filas individuales de menores en una
   vista pública.

## Patrón allowlist (regenerar el anonimizado)

No editar el crudo a mano: se **regenera** un artefacto seguro desde el crudo, proyectando solo
las columnas permitidas y **abortando** si alguna PII se cuela. Dos ejemplos vivos en el repo:

- **`Lineabase2026/tablero/scripts/anonimizar.py`** — lee el crudo `AMA_encuesta_unificada.csv`
  (vive **fuera** del repo, no versionado), arma `columnas` = variables graficables +
  ciudad/grupo/sexo, y hace `fuga = set(columnas) & PII; if fuga: raise SystemExit(...)` antes
  de escribir `data/encuesta_anon.csv`. Es el patrón allowlist + assert de seguridad.
- **`Lineabase2026/tablero/scripts/exportar_bot.py`** — baja de Kobo, proyecta solo
  `SAFE_COLS` (agregables) + `FREE_TEXT_COLS` (abiertas), `assert not (PII & set(df.columns))`
  garantiza que `Nombre_completo`/`N_mero_de_celular_WhatsApp` **nunca** salen, y `_redactar_pii()`
  (regex de teléfono/correo) redacta PII que un encuestado haya escrito en el texto libre —
  red de seguridad para futuras respuestas. Avisa cuántas redactó.

Regla: el crudo entra al script, **solo** el artefacto anonimizado sale del script. Después del
export, correr `scan_pii.py` sobre la salida como doble verificación.

## Patrón HMAC para cruces (identidad sin texto plano)

Cuando hay que **cruzar identidades** (p. ej. base ↔ endline) pero exponer el resultado en un
dashboard público, no se exporta el nombre/documento: se exportan **hashes HMAC salteados**.
Referencia viva: **`Lineasalida2026/lago-agrio/dashboard/lib/coverage.py`**.

```python
import hmac, hashlib, secrets
salt = secrets.token_hex(32)   # UNA vez; guardar en secrets (local + Streamlit Cloud), NO en el repo

def hmac_key(salt: str, value: str | None) -> str | None:
    if not isinstance(value, str) or not value:   # NaN de pandas es truthy → usar isinstance
        return None
    return hmac.new(salt.encode(), value.encode(), hashlib.sha256).hexdigest()
```

- El dashboard público lee `data/baseline_keys.parquet`: **solo** `codigo` (pseudónimo) +
  `hash_doc` / `hash_namecol`. Sin nombres ni documentos en claro.
- El mismo salt hashea el endline live y se cuentan matches ⇒ es una **cota mínima** (solo match
  exacto). El cruce completo con PII (fuzzy, teléfono, nominal de faltantes) vive **solo** en
  `outputs/` (gitignored), nunca en el dashboard.
- **El salt debe ser el mismo** en el script que genera el parquet y en los secrets del deploy.
  Si lo rotás, regenerá el parquet. Nunca lo commitees.

## Reducción de cuasi-identificadores (si el destino es público)

Género + ciudad + colegio + grado + edad + etnia pueden re-identificar a un menor aunque no haya
nombre. Para algo público: binear la edad (rangos, no valor exacto), quitar etnia/nivel
socioeconómico/lengua, y mostrar **solo agregados** por categoría — nunca la fila individual.

## Skills hermanas (todas producen artefactos que pueden llevar PII)

Estas skills generan salidas que **deben pasar por este guard** antes de subirse:

- **`ama-kobo`** — ingesta/validación de Kobo/Typeform/Google Form; produce los CSV crudos con PII.
- **`ama-graficas-informe`** — gráficas del informe (agregados por género; seguras si son solo agregados).
- **`ama-excel`** — informes `.xlsx` (datos técnicos por colegio, cobertura); muchos llevan PII → local/gitignored.
- **`ama-dashboard-encuesta`** — tableros Streamlit que se despliegan a Cloud (outward-facing).

Cuando cualquiera de ellas vaya a **commitear, exportar o desplegar**, esta skill se activa.

## Archivos de la skill

- `scripts/scan_pii.py` — el scanner/gate (stdlib, exit != 0 si hay PII).
- `references/anonimizacion.md` — allowlist vs blocklist, `_redactar_pii`, reducción de
  cuasi-identificadores y el patrón HMAC en detalle, con punteros a los scripts reales del repo.
