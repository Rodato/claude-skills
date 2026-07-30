---
name: ama-armar-encuesta
description: >-
  Construye un XLSForm (el Excel con hojas survey/choices/settings que Kobo
  necesita para crear una encuesta) a partir de una lista de preguntas y
  respuestas en un .docx o .xlsx suelto — el instrumento tal como lo redacta
  el equipo, no un XLSForm ya formado. Úsala cuando el pedido sea "armar",
  "montar" o "subir a Kobo" una encuesta nueva del programa AMA (línea base,
  línea de salida, seguimiento) o de cualquier programa hermano, para que la
  inferencia de tipo de pregunta, la lógica de salto, las matrices tipo
  PHQ-9/GAD-7 y el naming limpio salgan bien la primera vez en vez de
  reinventarse (o copiarse mal) cada vez. Es la hermana "constructora" de
  `ama-kobo` (que solo lee/ingiere encuestas ya publicadas).
---

# AMA Armar Encuesta — de lista de preguntas a XLSForm

Receta para pasar de un instrumento en prosa (Word con preguntas + opciones +
"pase a la pregunta N", o un Excel suelto con una fila por pregunta) a un
**XLSForm** correcto y limpio, listo para subir a KoboToolbox. No reemplaza el
criterio humano en las partes ambiguas (tipo de pregunta, lógica de salto,
qué preguntas forman una matriz) — los separa en un paso de **normalización**
(vos/Claude deciden) y un paso de **construcción** (el script, determinístico).

## Cuándo usarla

- El equipo pide una encuesta nueva o una versión editada de una existente
  (seguimiento, línea base, línea de salida) a partir de un doc de preguntas.
- Hay que convertir un Word con tablas de matriz (PHQ-9, GAD-7, escalas de
  actitudes) sin que cada fila quede con su propia lista de opciones repetida.
- Hay que traducir lógica de salto en prosa ("Pase a la pregunta 8", "Solo si
  tiene pareja") a expresiones `relevant` de XLSForm.
- Hay que decidir si la encuesta se sube a Kobo en modo matriz (grilla) o
  "aplanada" (cada ítem como pregunta independiente, para bot/WhatsApp/Typeform
  donde no hay grilla) — ver `references/matrices_y_grupos.md`.

## La receta en tres pasos

### 1. Normalizar (con criterio humano) → CSV intermedio

Convertí el doc/xlsx crudo a una tabla intermedia — una fila por pregunta,
columnas fijas (`references/esquema_intermedio.md`). Si el origen es un
`.docx`, `scripts/extraer_docx.py archivo.docx > borrador.csv` saca un
**borrador** (párrafos + tablas → filas candidatas) — **no confíes en él a
ciegas**, siempre revisalo a mano: agrupa mal las opciones, no separa
matrices de preguntas sueltas, y no traduce lógica de salto en prosa. Si el
origen ya es un `.xlsx`/`.csv` con una fila por pregunta, mapealo directo al
esquema intermedio.

Este es el paso donde entra el criterio: qué tipo es cada pregunta, qué filas
forman una matriz, y qué dice exactamente la condición de salto. El script de
construcción **falla fuerte** (no adivina) cuando algo de esto queda ambiguo
— ver `references/tipos_y_heuristicas.md` y `references/logica_de_salto.md`.

### 2. Construir → XLSForm real

```bash
python3 ~/.claude/skills/ama-armar-encuesta/scripts/build_xlsform.py \
    borrador.csv --out encuesta.xlsx --titulo "Encuesta de Seguimiento AMA"
```

Emite un `.xlsx` con las tres hojas que Kobo espera (`survey`, `choices`,
`settings`), replicando las convenciones que ya usás en los instrumentos AMA
reales (`Lineabase2026`, `EncuestaSalida`):

- **Nombres limpios**, no el `_Cu_l_es_tu_nombre_y_apellido` que deja el
  importador nativo de Word de Kobo — slugs cortos, legibles, sin acentos.
- **Listas de opciones compartidas**: si dos preguntas tienen las mismas
  opciones (ej. la escala Likert de todo un bloque PHQ-9), se genera **una
  sola** `list_name` para todas, no una por pregunta.
- **Matrices como `begin_group`/`field-list`** con encabezado (`appearance:
  label`) + filas `list-nolabel`, igual que `encuesta_salida_AMA_v1_con_matriz.xlsx`
  — no como select_ones sueltos con la pregunta repetida en cada fila.
  → `references/matrices_y_grupos.md`.
- **Lógica de salto** (`condicion`) traducida a `relevant` con la sintaxis
  `${nombre_pregunta} = 'valor'`, nunca queries a medias.
  → `references/logica_de_salto.md`.
- **Validaciones conocidas del programa** (regex teléfono/documento por
  ciudad, rango de edad, rango de fecha de nacimiento) si las pedís por
  columna `validacion` — mismos patrones que ya están en producción
  (`entradaCobija.xlsx`, `entradaLeticia.xlsx`).
  → `references/tipos_y_heuristicas.md`.

### 3. Validar antes de subir

```bash
python3 ~/.claude/skills/ama-armar-encuesta/scripts/validate_xlsform.py encuesta.xlsx
```

Gate stdlib-only (exit != 0 si algo está roto): toda `select_one`/`select_multiple`
referencia una lista que existe en `choices` y tiene al menos una opción, todo
`name` es único, todo `begin_group` cierra con su `end_group`, y toda
`${referencia}` en `relevant`/`constraint`/`calculation` apunta a una pregunta
que existe y aparece **antes** en el formulario. Si tenés `pyxform` instalado
(`pip install pyxform`), el script también intenta compilarlo a XForm de
verdad — es el validador oficial de Kobo/ODK y atrapa errores que el chequeo
estructural no ve. Sin `pyxform` corre igual, solo con menos cobertura.

Después de validar: **subilo a Kobo como proyecto nuevo o reemplazo de
versión**, nunca edites las hojas a mano en el UI de Kobo después — si hace
falta un cambio, volvé al CSV intermedio y regenerá.

## Reglas no negociables

- **El script no adivina lógica de salto ni tipo de pregunta ambiguos.** Si el
  CSV intermedio tiene una `condicion` en prosa libre o un tipo que no matchea
  ninguna heurística, `build_xlsform.py` **aborta** señalando la fila exacta.
  Es preferible parar y preguntar a vos/Claude que subir una encuesta con un
  salto mal armado en un cuestionario de salud mental/violencia.
- **Reusá listas de opciones idénticas.** Nunca generes una `list_name` nueva
  por pregunta si el set de opciones ya existe — infla el `choices` sheet y
  divergen con el tiempo (typos en una copia y no en la otra).
- **Las preguntas de identificación (nombre, documento, teléfono, correo,
  dirección, fecha de nacimiento) son las mismas que luego hay que anonimizar
  en la ingesta.** Marcalas igual que las conoce `ama-pii` para que el
  pipeline de anonimización no tenga que re-descubrirlas. El script de
  validación las lista al final a modo de aviso (no bloquea: el instrumento
  en blanco no tiene PII real, pero **las respuestas sí la van a tener**).
- **Un XLSForm nuevo no se commitea a un repo público sin pensar el nombre de
  las columnas de PII** — no es dato real, pero documenta exactamente qué
  campos identifican a un menor. Mismo criterio que `ama-pii` para
  documentación (ver el caso real de `Bot_monitoring`: nombres de ejemplo en
  un `CLAUDE.md` de un repo público).
- **Siempre `python3`, no `python`.** Comentarios en español, identificadores
  de código en inglés/snake_case (convención general del usuario).

## References

- `references/esquema_intermedio.md` — columnas del CSV intermedio, con
  ejemplos fila por fila (incluye el bloque PHQ-9 completo como caso real).
- `references/tipos_y_heuristicas.md` — cómo se infiere `tipo` cuando falta,
  validaciones conocidas del programa (regex teléfono CO/BO, rango edad,
  rango fecha nacimiento) y sus atajos en la columna `validacion`.
- `references/matrices_y_grupos.md` — el patrón `begin_group(field-list)` +
  header + `list-nolabel` + `end_group`, cuándo usar la versión "aplanada"
  (`sin_matriz`) en vez de la matriz real, y por qué.
- `references/logica_de_salto.md` — sintaxis aceptada en la columna
  `condicion` (atajo `nombre=valor` y XPath crudo `${x} = 'y'`), y qué hacer
  cuando el doc original solo trae la lógica en prosa.

## Skills hermanas

- **`ama-kobo`** — la dirección inversa: ingerir y validar datos ya
  recolectados desde un XLSForm publicado. Cuando termines de armar la
  encuesta y empiecen a llegar respuestas, esa es la skill que sigue.
- **`ama-pii`** — guard de anonimización antes de cualquier commit/push/deploy
  que toque datos reales de la encuesta (no del instrumento en blanco).
- **`ama-excel`** / **`ama-graficas-informe`** — una vez hay respuestas,
  informes y gráficas siguen esas convenciones.
