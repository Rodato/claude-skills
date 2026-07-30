# Esquema del CSV intermedio

Una fila = una pregunta (o una fila de matriz, o una nota). Encabezados en
español, minúsculas, sin acentos. Todas las columnas son opcionales salvo
`pregunta` (obligatoria salvo `tipo=nota`, donde `pregunta` hace de texto de
la nota).

| columna | obligatoria | descripción |
|---|---|---|
| `seccion` | no | Nombre del bloque temático. Filas consecutivas con el mismo valor quedan envueltas en `begin_group`/`end_group` (grupo "visual", sin `field-list`). Vacío = sin grupo. |
| `matriz` | no | ID compartido por las filas de una misma grilla (ej. `phq9`, `gad7`). Filas consecutivas con el mismo `matriz` se agrupan como `field-list` — ver `matrices_y_grupos.md`. Debe ir acompañado de opciones idénticas en todas las filas del bloque. |
| `pregunta` | **sí** | Texto de la pregunta (o de la nota si `tipo=nota`). |
| `tipo` | no | `texto` \| `numero` \| `fecha` \| `unica` \| `multiple` \| `nota`. Si falta, se infiere — ver `tipos_y_heuristicas.md`. |
| `opciones` | solo si `unica`/`multiple` | Opciones separadas por `\|`. Ej: `Nunca\|Algunos días\|La mitad de los días\|Casi todos los días\|No sabría decir`. |
| `lista` | no | Nombre explícito de `list_name` a reusar. Si se omite, se autogenera por hash del contenido de `opciones` — dos preguntas con las mismas opciones (texto idéntico) terminan compartiendo lista sin que lo pidas. |
| `ayuda` | no | Texto de `hint` (instrucción secundaria, ej. "Selecciona máximo 2 opciones"). |
| `requerido` | no | `si`/`no`. Default `si` (las notas siempre son `no`, se fuerza). |
| `condicion` | no | Lógica de salto. Atajo `nombre_pregunta=valor` o XPath crudo `${nombre_pregunta} = 'valor'`. Prosa libre → error. Ver `logica_de_salto.md`. |
| `nombre` | no | `name` explícito de la pregunta (variable en el XForm). Si se omite, se autogenera desde `pregunta` (slug limpio, ver abajo). Necesario cuando otra fila referencia esta pregunta en `condicion` y el slug automático sería impredecible — mejor ponerlo a mano en preguntas "ancla" (las que gatillan saltos). |
| `validacion` | no | Atajo a una validación conocida del programa: `telefono:CO`, `telefono:BO`, `documento:CO`, `documento:BO`, `edad:14-20` (rango libre), o `xpath:<constraint crudo>` para algo custom. Ver `tipos_y_heuristicas.md`. |

## Slug de `nombre` (cuando no se especifica)

1. Normalizar Unicode (NFKD), quitar acentos/diacríticos.
2. Minúsculas, reemplazar todo lo que no sea `[a-z0-9]` por `_`.
3. Colapsar `_` repetidos, quitar `_` al inicio/final.
3. Truncar a ~40 caracteres tomando palabras completas.
4. Si colisiona con un `name` ya usado en el formulario, sufijo numérico
   (`_2`, `_3`...).

Esto es deliberadamente **distinto** al `_Cu_l_es_tu_nombre_y_apellido` que
deja el conversor nativo de Word de Kobo (reemplaza cada carácter no-ASCII
por `_`, ilegible). Preferí siempre el slug limpio salvo que estés
reemplazando una versión existente de un form ya publicado y necesites
mantener los mismos `name` para no romper el historial de respuestas — en
ese caso, poné el `nombre` viejo explícito en la columna.

## Ejemplo real: bloque PHQ-9 completo

Así se ve el bloque de salud mental (PHQ-9) del instrumento de salida en el
esquema intermedio — nota + 9 filas de matriz compartiendo una sola lista:

```csv
seccion,matriz,pregunta,tipo,opciones,lista,ayuda,requerido,condicion,nombre,validacion
Salud mental,,"En los últimos 14 días (las últimas dos semanas), ¿con qué frecuencia te han molestado las siguientes situaciones?",nota,,,Marca con una X la respuesta que más se acerque a lo que te ha pasado.,no,,,
Salud mental,phq9,Tener poco interés o placer en hacer las cosas,unica,Nunca|Algunos días|La mitad de los días|Casi todos los días|No sabría decir,freq5,,si,,phq_1,
Salud mental,phq9,"Sentirse decaído/a, deprimido/a o sin esperanza",unica,Nunca|Algunos días|La mitad de los días|Casi todos los días|No sabría decir,freq5,,si,,phq_2,
Salud mental,phq9,Tener problemas para dormir o dormir demasiado,unica,Nunca|Algunos días|La mitad de los días|Casi todos los días|No sabría decir,freq5,,si,,phq_3,
Salud mental,phq9,Sentirse cansado/a o con poca energía,unica,Nunca|Algunos días|La mitad de los días|Casi todos los días|No sabría decir,freq5,,si,,phq_4,
Salud mental,phq9,Tener poco apetito o comer en exceso,unica,Nunca|Algunos días|La mitad de los días|Casi todos los días|No sabría decir,freq5,,si,,phq_5,
Salud mental,phq9,"Sentirse mal contigo mismo/a, o que eres un fracaso o has quedado mal con tu familia",unica,Nunca|Algunos días|La mitad de los días|Casi todos los días|No sabría decir,freq5,,si,,phq_6,
Salud mental,phq9,"Tener dificultad para concentrarte, por ejemplo al leer o ver televisión",unica,Nunca|Algunos días|La mitad de los días|Casi todos los días|No sabría decir,freq5,,si,,phq_7,
Salud mental,phq9,Moverte o hablar tan lento que otras personas podrían notarlo; o al contrario estar muy inquieto/a,unica,Nunca|Algunos días|La mitad de los días|Casi todos los días|No sabría decir,freq5,,si,,phq_8,
Salud mental,phq9,Pensar que estarías mejor muerto/a o hacerte daño de alguna manera,unica,Nunca|Algunos días|La mitad de los días|Casi todos los días|No sabría decir,freq5,,si,,phq_9,
```

Notar: mismo `lista=freq5` en las 9 filas (una sola lista de opciones en
`choices`, no nueve copias), mismo `matriz=phq9` (un solo `field-list`), y
`nombre` explícito (`phq_1`..`phq_9`) porque son el patrón de nombre que ya
usan tus dashboards/scripts existentes (`phq9/phq_1` en Kobo API, ver
`ama-kobo`).

## Ejemplo real: pregunta con salto

```csv
seccion,matriz,pregunta,tipo,opciones,lista,ayuda,requerido,condicion,nombre,validacion
Relaciones,,¿Actualmente tienes pareja?,unica,Sí|No,si_no,,si,,tiene_pareja,
Relaciones,,¿Actualmente vives con tu pareja actual?,unica,Sí|No,si_no,,si,tiene_pareja=Sí,,
```

La segunda fila solo aparece si la primera se respondió "Sí" — ver
`logica_de_salto.md` para cómo se traduce el atajo `tiene_pareja=Sí` a
`relevant`.
