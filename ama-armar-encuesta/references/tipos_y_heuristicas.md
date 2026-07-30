# Inferencia de tipo y validaciones conocidas

## Cuándo se infiere `tipo` (si la columna viene vacía)

Orden de evaluación (la primera que matchea gana):

1. `opciones` no vacía + (`pregunta` o `ayuda` contiene alguna de "selecciona
   todas", "marca todas", "seleccionar todas", "(selecciona máximo") →
   **`multiple`**.
2. `opciones` no vacía (y no matcheó lo anterior) → **`unica`**.
3. `pregunta` contiene "fecha de nacimiento" → **`fecha`**.
4. `pregunta` contiene "edad" y no tiene `opciones` → **`numero`**.
5. `pregunta` está vacía y solo hay texto informativo → **`nota`** (si el CSV
   no marcó `tipo=nota` explícito para una fila sin `pregunta`, es un error de
   normalización, no se infiere solo).
6. Nada de lo anterior → **`texto`**.

Estas heurísticas son deliberadamente conservadoras. Si el instrumento tiene
preguntas raras (ej. "¿Cuál es tu número de documento?" sin opciones — ¿es
`numero` o `texto`? depende de si querés permitir ceros a la izquierda), **no
asumas**: poné el `tipo` explícito en el CSV para esas filas. El script no va
a intentar adivinar mejor que estas cinco reglas.

## Validaciones conocidas del programa (columna `validacion`)

Estos son los mismos patrones que ya están en producción en
`AMA/EncuestaSalida/koboreferenceforms/entradaCobija.xlsx` /
`entradaLeticia.xlsx` — no los reinventes con una regex distinta.

| atajo | `type` resultante | `constraint` | `constraint_message` |
|---|---|---|---|
| `telefono:CO` | `integer` | `. >= 3000000000 and . <= 3599999999` (10 dígitos, prefijo móvil CO) | "Tu número de teléfono debe tener 10 dígitos." |
| `telefono:BO` | `integer` | `regex(., '^[0-9]{8}$')` | "Tú número de telefono debe tener solo 8 dígitos." |
| `documento:CO` | `integer` | `regex(., '^[0-9]{6,10}$')` | "Tu número de identificación debe tener entre 6 y 10 dígitos." |
| `documento:BO` | `integer` | `regex(., '^[0-9]{7,8}$')` | "Tu número de identificación debe tener 7 u 8 digitos." |
| `edad:MIN-MAX` (ej. `edad:14-20`) | `integer` | `. >= MIN and . <= MAX` | "La edad debe estar entre MIN y MAX años." |
| `xpath:<expresión>` | (no cambia el `type`) | la expresión tal cual, sin escapar | — (poné vos el `constraint_message` en la columna `ayuda` si hace falta, o editá el XLSForm después) |

Si la pregunta es `fecha` y hay una fila `edad:MIN-MAX` en el CSV (misma
sección), el builder **no** cruza automáticamente el rango de edad al
`constraint` de la fecha de nacimiento — replicá el patrón real a mano si
hace falta (ver `entradaCobija.xlsx`, fila `fecha_nacimiento`: `. >=
date('2006-01-01') and . < date('2013-01-01')`) usando `validacion:xpath:...`
con la fecha calculada para el ciclo de la encuesta.

## Preguntas de identificación (PII) — lista de reconocimiento

El validador (`validate_xlsform.py`) avisa (no bloquea) cuando el `pregunta`
de una fila contiene alguna de estas señales — misma lista que usa la skill
`ama-pii` para CSVs de respuestas ya recolectadas:

`nombre`, `apellido`, `documento`, `cédula`/`cedula`, `dni`, `teléfono`/
`telefono`, `celular`, `whatsapp`, `correo`, `email`, `dirección`/`direccion`,
`fecha de nacimiento`.

Es solo un aviso porque el **instrumento en blanco** no tiene PII real — pero
documenta qué columnas van a tenerla apenas lleguen respuestas, para que la
ingesta (`ama-kobo`) y el guard de anonimización (`ama-pii`) no tengan que
re-descubrirlo mirando el form.
