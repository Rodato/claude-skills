# Preguntas de respuesta múltiple

Las preguntas "selecciona todas las que apliquen" llegan de Kobo de formas
distintas según ciudad/canal. Elegir mal el separador rompe el conteo en silencio.

## Los tres casos

| Fuente | Cómo llegan las opciones | Cómo descomponer |
|---|---|---|
| **Kobo `multiple_select=both`** (export UI) | 1 columna unida + N columnas binarias `pregunta/opcion` (0/1) | sumar las binarias |
| **Cobija / Leticia** (tablero, celda unida) | opciones **pegadas con espacios** en una sola celda | greedy longest-match contra XML |
| **Iquitos** (Preprocesamiento) | opciones separadas por **comas** | `split(",")` |

La regla mnemónica: **Iquitos = comas, Cobija/Leticia = espacios.**

## 1. `multiple_select=both`: contar las columnas binarias

Con el export setting `multiple_select=both` (ver `fetch_kobo.py::EXPORT_SETTINGS`),
Kobo da la columna unida **más** una columna binaria por opción, nombrada
`pregunta/opcion`. La unida no tiene `/` después de la pregunta; las binarias sí.
`preprocess.py::validate_multi_response` lo aprovecha para validar "máx 2 respuestas":

```python
related = [c for c in df.columns if c.startswith(question)]
joined_cols = [c for c in related if "/" not in c[len(question):]]   # columna unida
binary_cols = [c for c in related if "/" in c[len(question):]]        # opciones 0/1

counts = sum(pd.to_numeric(df[c], errors="coerce").fillna(0) for c in binary_cols)
mask_over = counts > max_responses            # MAX_RESPONSES = 2
df.loc[mask_over, joined_cols + binary_cols] = pd.NA   # >2 respuestas → NA
```

Las 4 preguntas validadas así (mismas que Iquitos/Lago Agrio):

```python
MULTI_RESPONSE_QUESTIONS = [
    "En tu infancia, ¿cómo te criaron principalmente?",
    "En tu infancia, ¿cuál fue la persona más presente?",
    "¿Qué situaciones recuerdas?",
    "Cuando piensas en tu relación de pareja, ¿qué sientes?",
]
```

## 2. Cobija/Leticia: opciones pegadas por ESPACIOS → greedy longest-match

En el tablero (`tablero/lib.py`) las celdas de respuesta múltiple traen las opciones
**concatenadas con espacios**, sin delimitador. No se puede `split(" ")` porque las
propias etiquetas tienen espacios ("La mitad de los días"). La solución: tener el
catálogo de **todas** las etiquetas de opción (extraídas del XML del form, ordenadas
de más larga a más corta) e ir consumiendo la celda por la coincidencia **más larga**.

Extraer etiquetas del XML (`<value>…</value>`), más largas primero:

```python
# lib.py::_etiquetas_opciones  (cacheado con lru_cache)
for m in re.findall(r"<value>(.*?)</value>", txt, re.S):
    s = _limpiar_label(m)                 # colapsa espacios dobles que trae Kobo
    if s:
        labels.add(s)
return tuple(sorted(labels, key=len, reverse=True))   # greedy: más larga primero
```

Descomponer una celda:

```python
# lib.py::segmentar
def segmentar(celda):
    labs = _etiquetas_opciones()
    s = _limpiar_label(celda)
    out = []
    while s:
        for L in labs:                    # labs ya viene de mayor a menor longitud
            if s.startswith(L):
                out.append(L)
                s = s[len(L):].strip()
                break
        else:                             # ningún label calza: deja el resto y corta
            out.append(s)
            break
    return out
```

**Verificación esperada:** cobertura 100% de las celdas, 0 sobrantes. Si el `else`
del `for` se dispara seguido, falta alguna etiqueta en el XML (o hay una opción
"Otro" de texto libre) — revisar, no ignorar.

`_limpiar_label` (`re.sub(r"\s+", " ", ...).strip()`) es clave: Kobo mete **espacios
dobles** en algunas etiquetas ("La  mitad de los días"), y sin colapsarlos el
`startswith` falla.

## 3. Iquitos: comas

En el Preprocesamiento original las mismas preguntas venían separadas por comas, así
que ahí es un `split(",")` con strip. Si trabajás con datos de Iquitos y el greedy de
espacios devuelve basura, revisá si en realidad son comas.

## 4. XML del form como diccionario de etiquetas

Los `form/*.xml` (Cobija, Leticia) son el XLSForm compilado. Las etiquetas de opción
están en `<value>…</value>` dentro de bloques `<text id=".../opcion:label">`. Sirven
para: (a) el catálogo de `segmentar`, (b) mapear código→etiqueta de colegio/grado.
En la API de Kobo el equivalente es `content.choices` (`list_name → {name: label}`),
que `lib/kobo.py::get_asset` arma en un dict. Ojo: una etiqueta de Kobo puede venir
como **lista** (una por idioma) → tomar la primera (`_first`).
