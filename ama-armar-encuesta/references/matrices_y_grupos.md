# Matrices y grupos — el patrón real de Kobo

Referencia viva: `AMA/EncuestaSalida/encuesta_salida_AMA_v1_con_matriz.xlsx`
vs `encuesta_salida_AMA_v1_sin_matriz.xlsx` (mismo instrumento, dos formas de
publicarlo). Leelos con `openpyxl` antes de tocar esto si tenés dudas —
son el ejemplo canónico.

## Versión matriz (grilla) — la que se sube a Kobo/Enketo web o app

Cuando varias preguntas comparten exactamente las mismas opciones de
respuesta (una escala Likert, PHQ-9, GAD-7, escalas de actitud), Kobo puede
renderizarlas como una sola grilla: la pregunta a la izquierda, las opciones
como columnas, una sola vez arriba. Esto se logra con:

```
begin_group | phq9        |                                                  | | | field-list | | | | |
note        | phq9_intro  | (texto de instrucción)                          | | | | | | | |
select_one freq5 | phq9_header | " " (un espacio, no vacío)                 | | | label | | | | |
select_one freq5 | phq_1       | Tener poco interés o placer en hacer las cosas | | yes | list-nolabel | | | | |
select_one freq5 | phq_2       | ...                                          | | yes | list-nolabel | | | | |
...
end_group    | phq9        |
```

Piezas obligatorias:

- `begin_group`/`end_group` con el mismo `name` (ej. `phq9`), y
  `appearance = field-list` en la fila `begin_group`.
- Una fila `note` **antes** del grupo (o como primera fila del grupo) con el
  texto introductorio compartido — no lo repitas en cada pregunta.
- Una fila `select_one <lista>` con `appearance = label` y `name` terminado
  en `_header`, `label` = un espacio simple (`" "`, no vacío — un label
  vacío rompe el render). Esta fila **solo** pinta el encabezado de columnas
  (las opciones), no es una pregunta real: no se cuenta como respondida.
- Cada ítem real: `select_one <misma lista>` con `appearance = list-nolabel`
  (oculta repetir las opciones en cada fila, porque ya están en el header) y
  `required = yes`.
- **Todas las filas del bloque referencian la misma `list_name`** en
  `choices` (ej. `freq5` con 5 opciones). Nunca una lista nueva por pregunta.

`build_xlsform.py` arma esto automáticamente cuando varias filas consecutivas
del CSV intermedio comparten el mismo valor de `matriz` (columna dedicada,
ver `esquema_intermedio.md`) — genera el `begin_group(field-list)`, la fila
header y el `end_group` sin que tengas que escribirlos a mano.

## Versión aplanada (`sin_matriz`) — cuándo usarla

Se usa cuando el canal de entrega **no puede renderizar una grilla**: un bot
de WhatsApp, Typeform (que no tiene matrices tipo Kobo), o cualquier
integración pregunta-por-pregunta. En ese caso cada ítem se convierte en una
pregunta autocontenida, repitiendo el marco de la pregunta original dentro de
cada label:

- "Tener poco interés o placer en hacer las cosas" (matriz)
  → "En los últimos 14 días, ¿con qué frecuencia has tenido poco interés o
  placer en hacer las cosas?" (aplanada)

No hay `begin_group(field-list)`, no hay fila `_header`, ni `appearance:
list-nolabel` — son `select_one` sueltos, pero **siguen compartiendo la
misma `list_name`** entre sí (eso no cambia).

`build_xlsform.py` soporta ambos modos con la flag `--aplanado`: sin la
flag arma la versión matriz (default, para Kobo); con `--aplanado` arma la
versión de preguntas sueltas y reescribe el `label` de cada ítem incrustando
el marco de la nota introductoria — si el CSV intermedio no trae ya el label
completo por ítem, tenés que escribirlo vos en la columna `pregunta` (el
script no compone frases automáticamente, solo evita el error de subir una
matriz a un canal que no la soporta).

## Grupos "visuales" (columna `seccion`, sin `field-list`)

Además de las matrices hay grupos puramente organizativos — capítulos del
formulario ("Datos personales", "Relaciones de pareja") sin intención de
grilla. Estos usan `begin_group`/`end_group` **sin** `appearance`, uno por
cada valor distinto y consecutivo de la columna `seccion`. No comparten
lista de opciones entre sí (cada pregunta adentro tiene la suya, salvo que
también esté en una `matriz`).
