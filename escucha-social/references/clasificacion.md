# Clasificación: taxonomía cerrada sobre un LLM barato

## La forma general

- **Modelo:** `google/gemini-2.5-flash-lite` vía OpenRouter. Barato y suficiente para
  taxonomías cerradas; para 12.000 trinos el costo es de centavos.
- **Batch de 12 trinos**, 6 workers, `response_format: {"type": "json_object"}`,
  `temperature: 0`.
- **Caché incremental por id** en `data/processed/classified.csv`: en refrescos solo se paga
  por trinos nuevos. `--force` reclasifica todo, `--limit N` es el smoke barato.
- Cada trino entra con un índice `i` que el modelo debe devolver sin cambiar. Así se
  reensambla el batch aunque el modelo reordene.

Al trino se le pasa, además del texto (recortado a 600 caracteres), el **contexto que ayuda
a decidir**: autor, `location`, `co_hits` (qué disparó la señal de país), las keywords que lo
capturaron y —si viene del barrido por cuenta— `contexto_cuenta` con el modo `emite`/`menciones`.

## Diseñar la taxonomía

Un campo por pregunta del encargo. En la escucha de espacio cívico, las preguntas de la reunión se volvieron:

| Pregunta del encargo | Campo |
|---|---|
| ¿De qué se habla? | `encuadre` (12 valores, eje dominante) |
| ¿Qué libertad está en juego? | `libertades` (multi) |
| ¿Quién habla? | `tipo_actor` |
| ¿Amplía o restringe? | `postura_espacio_civico` |
| ¿Quién restringe? | `restrictores` (multi) |
| ¿Con qué argumentos se deslegitima? | `estigmatiza` + `tono_hacia_organizaciones` |
| ¿Hay repliegue? | `efecto_inhibitorio` |

Más tres campos de infraestructura que **toda** escucha necesita:

- `relevante` (bool) — filtro de ruido temático.
- `pais` — filtro geográfico.
- `confianza` (0–1) — permite `--min-confianza` en el reporte sin reclasificar.
- `cita_clave` — fragmento textual breve, alimenta el anexo.

### Reglas que hay que escribir en el prompt, sí o sí

**1. Relevancia y país son independientes.** Un trino sobre el cierre del espacio cívico en
Venezuela es `relevante=true` con `pais="otro"`. Si se mezclan, el embudo del informe deja de
poder reportar la tasa de descarte por país.

**2. Enumerar las exclusiones de ruido, concretas.** No alcanza "descartá lo irrelevante".
Lo que de verdad aparece: publicidad, ofertas de empleo, horóscopos, deportes (un "club
social" no es espacio cívico), **usos técnicos ajenos de las palabras capturadas** ("sociedad
civil" en sentido del derecho civil, "organización" de un evento), y política partidista pura
sin organización ni libertad en juego. Y: "ante la duda entre ruido y conversación real,
marcá false".

**3. EJERCER ≠ DENUNCIAR. Es el error más costoso.**

La primera versión del clasificador contaba como estigmatización los comunicados que
*rechazan* señalamientos. El dato salía **invertido**: las organizaciones defendiéndose
aparecían como atacantes.

```
estigmatiza = true            → EL AUTOR DEL TRINO ataca la legitimidad de quien se organiza
denuncia_estigmatizacion=true → el autor REPORTA, RECHAZA o ANALIZA un ataque ajeno
```

"Rechazamos los señalamientos contra la Fundación X" es `denuncia_estigmatizacion=true` y
`estigmatiza=FALSE`. Los dos pueden ser false; rarísimamente los dos true.

La misma trampa en `efecto_inhibitorio`: es `true` **solo si el texto dice que alguien YA
dejó de hacer algo** —se calló, no marchó, cerró la oficina, borró la publicación—. Denunciar
un riesgo, contar un asesinato o advertir que defender derechos "cuesta la vida" **no** es
efecto inhibitorio: es denuncia.

Y una tercera: una crítica sustantiva y verificable al trabajo de una organización es
`critica_legitima` en el tono, con `estigmatiza=false`.

> **Al tocar el prompt, verificá que la distinción ejercer/denunciar siga en pie.** Es lo
> primero que se rompe al reescribir.

**4. Dar el contexto político con fechas.** "En Colombia gobierna X desde el 7 de agosto de
2026; antes gobernaba Y. Ambos períodos están en la muestra." Sin eso, el modelo interpreta
mal quién es gobierno en cada trino. Y acto seguido: "No tomes partido: tu trabajo es
describir cómo se habla, no quién tiene razón."

**5. Dar pistas de país concretas.** Entidades, jerga y figuras políticas que indican el país
objetivo; jerga de otros países que lo descarta. Y: "si de verdad no hay señal,
`indeterminado`" — no forzar.

**6. Cerrar los enums en el prompt Y en el código.** "Cada campo acepta ÚNICAMENTE valores de
su propia lista. No inventes categorías ni uses el nombre de otro campo como valor."

**7. Colapsar cuando `relevante=false`.** Si no es relevante: `pais="indeterminado"`,
listas vacías, `tono="na"`. Evita que el ruido contamine los conteos secundarios.

**8. Encuadre = eje dominante, uno solo.** Y hay que decir explícitamente cuándo usar cada
uno de los que se confunden. En la escucha de espacio cívico: si la organización está haciendo su trabajo
(acompaña, publica un informe, va a una audiencia) el encuadre es `ejercicio_incidencia`; si
es su tema de fondo sin que el espacio cívico sea el asunto, es `agenda_tematica`. `otro`
solo para lo que de verdad no encaje.

## Normalización: el modelo se sale del enum

Pasa siempre, incluso con `temperature: 0`. Se ataja **en la normalización, no en el
reporte** — si llega sucio al `.docx` ya contaminó los conteos.

```python
def _pick(v, allowed, fallback):
    """Fuerza el valor dentro del enum. El modelo a veces devuelve el nombre de otro campo."""
    v = str(v or "").strip().lower()
    return v if v in allowed else fallback

def _clean_multi(v, allowed):
    """Normaliza a un orden canónico (el de `allowed`). Sin esto, el modelo devuelve
    'expresion, incidencia' e 'incidencia, expresion' y el reporte los cuenta aparte."""
    seen = {str(x).strip().lower() for x in (v if isinstance(v, list) else str(v or "").split(","))}
    return ", ".join(a for a in allowed if a in seen)
```

El **orden canónico** en multi-etiqueta es el detalle que más silenciosamente rompe un
informe: dos variantes del mismo par se cuentan como categorías distintas y las dos quedan
a media altura en la gráfica.

También hay que tolerar el JSON envuelto en ```` ```json ````: `_extract_json()` lo pela y,
si falla, recorta entre el primer `{` y el último `}`.

## Booleanos que vuelven como string

Al releer el CSV, pandas trae `"True"`/`"true"`/`1.0`. En el reporte:

```python
BOOL_COLS = ("relevante", "estigmatiza", "denuncia_estigmatizacion", "efecto_inhibitorio")
m[col] = m[col].astype(str).str.lower().isin(["true", "1", "1.0"])
```

Un `if row["estigmatiza"]` sobre el string `"False"` es **truthy** y no avisa.

## Smoke de la clasificación

`classify` imprime al final los conteos que importan para detectar una taxonomía invertida:

```
[classify] estigmatiza=210 · denuncia_estigmatizacion=640
[classify] → classified.csv · 10000 clasificados · 7100 relevantes · 4400 Colombia · 4200 núcleo
```

Si `estigmatiza` y `denuncia_estigmatizacion` salen en proporciones raras respecto a lo que
se espera del corpus, revisá el prompt antes de gastar en el barrido completo.

---

## Cuando el libro de códigos viene de un brief

Un cliente puede traer su propio libro de códigos —siete ejes, en la escucha de espacio cívico—. Tres
decisiones al implementarlo:

**1. Respetá los nombres del brief, aunque tengas los tuyos.** El informe se lee contra el
brief; renombrar «Dimensión afectada» a «libertades» obliga al cliente a traducir. Los
valores internos van en snake_case, las etiquetas del informe en las palabras del brief.

**2. Mirá qué NO cubre el libro de códigos y conservalo.** El de la escucha de espacio cívico codificaba
exclusivamente *restricción*: aplicado solo, deja fuera los trinos en que una organización
simplemente ejerce su rol, y con ellos el eje narrativo «espacio en uso vs. espacio en
disputa». Se conservó `encuadre` de la versión anterior por eso, documentando la razón en el
código.

**3. Los ejes conceptuales necesitan operacionalización explícita.** «COM-B: Capacidad /
Oportunidad / Motivación del actor social frente a la restricción» no es codificable tal
cual. En el prompt se convirtió en:

> `capacidad` = saberes, destrezas y recursos PROPIOS de la organización · `oportunidad` =
> condiciones EXTERNAS que habilitan o impiden (permisos, plata, seguridad, acceso a
> decisores) · `motivacion` = voluntad, creencias, miedo, sentido de legitimidad

Escribí esa operacionalización **una sola vez** y reusala literal en el prompt, en la hoja de
instrucciones del libro de doble codificación y en la nota al pie del informe. Si las tres
difieren, la concordancia mide desacuerdo de definiciones, no de criterio.

## Cruzar dos campos que codifican lo mismo

Cuando dos campos codifican el mismo fenómeno por caminos distintos —un booleano
`estigmatiza` y un eje `posicion_enunciado = "deslegitimacion"`— **no elijas uno: quedate
con los dos y medí su incoherencia**. Es un chequeo gratis de si el modelo está confundiendo
ejercer con denunciar:

```python
incoh = sum(1 for c in merged.values()
            if _t(c.get("estigmatiza"))
            != (str(c.get("posicion_enunciado")).lower() == "deslegitimacion"))
print(f"incoherencias={incoh} ({100*incoh/len(merged):.1f}%)"
      + ("  ⚠️ revisar el prompt" if incoh > 0.10 * len(merged) else ""))
```

Se mira **antes** de reportar, no después de que el cliente pregunte.

## Doble codificación humana y concordancia

Si el cliente exige validación humana de la preclasificación automática —hay briefs que
lo llaman «no negociable»— es trabajo de código, no solo de coordinación. Ver
`templates/qa.py`. Cuatro decisiones que importan:

**El libro que recibe la persona NO lleva los códigos de la máquina.** Si los lleva, el
ejercicio mide obediencia, no concordancia. Los códigos automáticos se guardan aparte y
solo se cruzan al calcular.

**Muestra estratificada, no simple.** El 10% al azar de un corpus donde `deslegitimacion` es
minoría trae tres o cuatro casos del eje que más importa. Estratificá por el campo más
propenso al error (la posición del enunciado), con un mínimo por estrato, y fijá la semilla
para que el ejercicio sea reproducible y auditable.

**El libro de códigos viaja dentro del archivo.** Una hoja «cómo codificar» con cada campo,
sus valores admitidos y las dos reglas críticas (ejercer ≠ denunciar; efecto inhibitorio solo
si ya ocurrió). Desplegables en los campos de valor único — pero **no** en los
multi-etiqueta, donde impedirían escribir `genero, territorial`.

**κ de Cohen por campo; en multi-etiqueta, κ por categoría más Jaccard medio.** Lectura
convencional: <0,40 pobre · 0,40–0,60 moderada · 0,60–0,80 sustancial · >0,80 casi perfecta.
Los ejes bajo 0,60 no tienen codificación estable: o se arregla su definición en el prompt,
o el informe publica sus proporciones **con la advertencia**.

Mientras no exista el reporte de concordancia, el informe debe decir en su sección de método
que la codificación es automática y no validada, y que sus cifras son provisionales. El
`report.py` de la escucha de espacio cívico lo hace solo: busca `qa/concordancia.md` y, si no está, escribe el
párrafo de pendiente en negrita.

## El JSON cortado no se arregla reintentando

Con lotes grandes y taxonomías anchas —12 trinos × 19 campos— la respuesta desborda el tope
de salida del modelo y llega truncada. `json.JSONDecodeError` con «Expecting ',' delimiter»
en un offset alto es la firma.

Reintentar **no sirve**: el lote sigue teniendo el mismo tamaño, así que vuelve a desbordar.
En una corrida del 2026-09-15, 102 lotes agotaron sus 4 reintentos y se perdieron
1.228 trinos (2,2% del corpus) en silencio.

La corrección es partir el lote y recurrir:

```python
if isinstance(last_err, json.JSONDecodeError) and len(batch) > 1:
    mitad = len(batch) // 2
    izq, uso_i = classify_batch(batch[:mitad], model, temperature, max_retries)
    der, uso_d = classify_batch(batch[mitad:], model, temperature, max_retries)
    return izq + der, {k: (uso_i.get(k, 0) or 0) + (uso_d.get(k, 0) or 0)
                       for k in set(uso_i) | set(uso_d)}
```

Regla general, la misma del tope de cuota en la captura: **antes de reintentar, preguntate si
el reintento cambia algo.** Si la causa es estructural —el lote es muy grande, la cuota está
agotada— reintentar solo gasta tiempo y esconde la pérdida. Y como el caché es por id, una
segunda pasada sin `--force` recupera lo que se perdió sin volver a pagar por el resto.
