# Lógica de salto — columna `condicion`

XLSForm no tiene "saltar a la pregunta N": tiene `relevant`, una expresión
XPath evaluada por **cada** pregunta que decide si se muestra o no. No existe
un "goto" — cada pregunta que debería ocultarse lleva su propia condición.

## Lo que acepta el builder

1. **Atajo `nombre_pregunta=valor`** (el caso común, un solo igual):
   - `tiene_pareja=Sí` → `relevant` = `${tiene_pareja} = 'si'` (el valor se
     slugifica igual que las opciones en `choices`, así que "Sí" con tilde y
     mayúscula matchea el `name` real de la opción, no el label visible).
   - Múltiples valores válidos con `|`: `colegio=miscal_sucre|rogelia_menacho`
     → `relevant` = `${colegio} = 'miscal_sucre' or ${colegio} = 'rogelia_menacho'`.
   - Negación con `!=`: `tiene_pareja!=Sí` → `${tiene_pareja} != 'si'`.

2. **XPath crudo**, si empieza con `xpath:` — se copia tal cual a `relevant`
   sin tocar. Usalo para condiciones que no son un simple igual (`selected()`
   para `select_multiple`, comparaciones numéricas, `and`/`or` combinados
   entre preguntas distintas). Ejemplo real (violencia en pareja, solo si
   hubo respuesta positiva):
   `xpath:selected(${situaciones_violencia}, 'gritos') or selected(${situaciones_violencia}, 'golpes')`

3. **Vacío** → sin `relevant`, la pregunta siempre se muestra.

## Lo que el builder rechaza (falla fuerte, no adivina)

Cualquier texto en `condicion` que no matchee los patrones de arriba —
típicamente porque vino copiado tal cual del Word original sin traducir:

- `"Pase a la pregunta 8"` ❌
- `"Solo si el entrevistado tiene pareja"` ❌
- `"Saltar si no está matriculado"` ❌

El script para con un error listando la fila y el texto exacto. **Traducí
esa prosa vos** (o con Claude, mirando qué pregunta y qué valor de respuesta
gatilla el salto) al atajo `nombre=valor` o a `xpath:`, y volvé a correr.
Esto es intencional: en un instrumento con preguntas de salud mental o
violencia, un salto mal inferido puede ocultar o mostrar preguntas sensibles
a la persona equivocada — mejor que pare a que adivine.

## Cómo mapear la prosa del Word a la condición correcta

El patrón típico en los instrumentos AMA es "Pregunta ancla" (única, con
opciones) seguida de una o más preguntas que solo aplican a una de esas
opciones:

```
¿Actualmente tienes pareja?            [pregunta ancla, name=tiene_pareja]
  Sí
  No

¿Actualmente vives con tu pareja actual?   ← "(solo si tiene pareja)"
```

1. Identificá el `name` de la pregunta ancla (ponelo explícito en la columna
   `nombre` si no confiás en el slug automático — ver `esquema_intermedio.md`).
2. Identificá qué opción(es) de la ancla activan la pregunta dependiente.
3. Escribí `condicion = tiene_pareja=Sí` en la fila dependiente (o en **todas**
   las filas dependientes, si son varias seguidas — cada una necesita su
   propio `relevant`, no hay forma de aplicarlo "a un bloque" salvo que estén
   además agrupadas con `begin_group`/`end_group`, en cuyo caso poner el
   `relevant` en el `begin_group` alcanza para todo el grupo).

Para agrupar el `relevant` a nivel de grupo en vez de repetirlo en cada fila:
poné la `condicion` en la fila donde arranca la `seccion`/`matriz` del bloque
dependiente — el builder la traslada al `begin_group` en lugar de a cada
pregunta individual.
