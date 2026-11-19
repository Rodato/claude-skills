# Captura: keywords, ventanas, Apify y cobertura

## Diseño de keywords

Cada keyword lleva cuatro campos, y los cuatro se usan después:

```yaml
- { q: espacio cívico, bloque: concepto, detecta: el concepto explícito, phrase: true, nivel: core }
```

| Campo | Para qué sirve después |
|---|---|
| `q` | La query. Con `phrase: true` se envuelve en comillas → frase exacta |
| `bloque` | Agrupa el reporte de cobertura y la tabla de rendimiento por keyword |
| `detecta` | Documenta la intención; queda en el JSON crudo para auditar el diseño |
| `nivel` | `core` \| `probe`. Permite `--nivel core` y decidir qué se poda en la 2ª iteración |

**El primer barrido es una red amplia, a propósito.** Se tira para ver qué se pesca; las
keywords que no rindan se podan después. Por eso el informe incluye una tabla de
**rendimiento por keyword** (capturados en bruto vs. cuántos llegaron a la base) y un
párrafo explícito: un volumen bajo no es un fallo de captura, es un hallazgo sobre qué
lenguaje circula.

### Anclaje por país: correr las dos versiones

`lang:es` no acota por país. Medición real (escucha de espacio cívico, 2026-09-11, 60 trinos por término):

| Término | Colombianos |
|---|---|
| `"espacio cívico"` | 2 / 60 — es jerga de foros internacionales de cooperación |
| `"organizaciones sociales"` | 10 / 60 |
| `ONG Colombia` (AND, sin comillas) | 56 / 60 |

Pero anclar con `Colombia` **sesga hacia el registro noticioso**: los colombianos rara vez
escriben "Colombia" al hablar de lo suyo. Por eso cada término genérico corre en **dos
versiones**: la amplia aporta lenguaje vernáculo, la anclada aporta volumen relevante. El
dedup por id en `normalize` hace que el solapamiento no cuente doble.

### Señal léxica de país (`co_score`)

En `normalize.py`, tres tiers positivos y una contraseñal:

| Tier | Peso | Qué es |
|---|---|---|
| `CO_PLACES` | +3 (+4 si está en `location`) | Topónimos y gentilicios inequívocos |
| `CO_ENTITIES` | +3 | Instituciones y ONG del ecosistema (Defensoría, JEP, Indepaz, FLIP, Dejusticia…) más figuras políticas |
| `CO_VOCAB` | +2 | Vocabulario casi exclusivo: "líderes sociales", "firmantes de paz", "paro nacional", "chuzadas" |
| `NOT_CO` | −3 (−4 en `location`) | Marcadores fuertes de otros países hispanohablantes |

Dos decisiones que no son obvias:

- **`CO_ENTITIES` es el tier que más trabaja** en una escucha cívica: la conversación nombra
  una entidad antes que un lugar. Si el tema es otro (movilidad, consumo), el tier fuerte
  es otro — revisá cuál antes de copiar las regex.
- **Venezuela y "venezolano" NO están en `NOT_CO`**, a propósito: la conversación colombiana
  los nombra todo el tiempo (migración, frontera, deportaciones) y penalizarlos borra
  trinos colombianos legítimos. Al adaptar la contraseñal a otro país, buscá su equivalente.

`co_score` **no decide solo**: se pasa como pista (`co_hits`) al clasificador, que juzga con
el texto completo. La decisión queda registrada aparte para poder reportar la tasa de
filtrado en el embudo del informe.

## Ventanas

`since:`/`until:` de X es `[since, until)` — **until exclusivo** — así que cada ventana usa
`hi = inicio de la siguiente`, sin solaparse. `chunk_windows()` lo resuelve para `week` y
`month`.

El actor solo pagina histórico de forma fiable con `since:/until:`, por eso el backfill se
hace por ventanas y no en una sola corrida.

**Estrategia recomendada:** arrancar con `--windows 6` (los últimos ~6 meses) y extender
hacia atrás después, ya con las keywords depuradas. El scraper es reanudable —salta lo ya
capturado mirando si existe el archivo `*__{slug}__{fecha}.json`— así que extender no vuelve
a pagar lo hecho.

## Apify: los dos modos de perder plata y datos

**Actor:** `kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest`, pay-per-result
(~$0.25/1K resultados), corre en plan Free.

### Concurrencia
El plan Free tope **5 corridas concurrentes** y rechaza la sobrante **al instante**. Como el
rechazo es inmediato, sin reintento se pierde la corrida entera. `run_actor` reintenta con
backoff cuando el error es de concurrencia o rate limit; el default es `--workers 4`. Con 6
workers se pierden corridas en silencio. A 4 workers, 270 corridas tardan ~3 horas.

### Cuota — el error que hay que no repetir
El 2026-09-11 la cuenta free tocó su tope mensual de USD 5 a mitad del barrido. El error se
trataba como un fallo transitorio cualquiera, así que **128 corridas seguidas se perdieron
imprimiendo un warning por línea** y el proceso terminó diciendo "listo · 270 corridas".

Y el hueco **no fue aleatorio**: las corridas se lanzan en orden de keyword, así que se perdió
todo el final de la lista — los bloques `riesgo` y `temas_org` quedaron en cero, justo las
dimensiones centrales del encargo.

La corrección, en `templates/_common.py`:

```python
class QuotaExceeded(RuntimeError):
    """Un tope de cuota no se reintenta: se aborta y se avisa."""

# en run_actor:
if "usage hard limit" in msg or "monthly usage" in msg:
    raise QuotaExceeded(str(e)) from e
```

y en el scraper, `ex.shutdown(wait=False, cancel_futures=True)` más un mensaje que dice
cuánto falta, que el hueco no es aleatorio y que el barrido es reanudable.

**Regla general:** cualquier error que no se vaya a arreglar reintentando debe cortar el
barrido, no acumularse como warning. Un pipeline que "termina bien" con datos parciales es
peor que uno que falla.

### Otros detalles del actor
- Devuelve placeholders que hay que filtrar: `noResults`, `type == "mock_tweet"`, `id == "-1"`.
- Pagina de a ~20, así que devuelve **algo más** que `max_items`.
- El actor redirige sus logs al cliente; con cientos de corridas es ilegible → se bajan a
  `WARNING` los loggers `apify_client`, `apify` y el del actor.

### Costo antes de gastar
`scrape_x` imprime el techo teórico antes de correr, y `--dry-run` muestra las queries sin
gastar un peso:

```
[x] 45 keywords × 6 ventanas = 270 corridas · queryType=Latest · maxItems=150 · workers=4
[x] techo teórico 40,500 tweets (~$10.13 a $0.25/1K)
```

Usalo siempre antes de un barrido grande. `--smoke` (2 keywords × última ventana) es la
prueba de humo barata.

## Barrido por cuenta (opcional pero muy rentable)

Dos modos por cada cuenta objetivo:

| Modo | Query | Qué mide |
|---|---|---|
| `emite` | `from:handle` | Qué publica la organización |
| `menciones` | `@handle -from:handle` | Qué dice el resto sobre ella |

El segundo es el que alimenta el mapa de apoyo vs. detractores. **Son poblaciones con sesgos
propios** —la organización habla de sí misma; quien la menciona se autoselecciona— así que
`load_cuentas_df()` está deliberadamente separado de `load_df()` y sus porcentajes **no son
comparables** con los del corpus de keywords. La tabla del informe lo advierte.

Si una organización objetivo no tiene cuenta en la plataforma, **decilo en el informe**: en
una escucha, una organización objetivo solo tenía Facebook, plataforma descartada, y su
ecosistema quedó sin medir.
Un objetivo del encargo que no se pudo medir es información, no un hueco que tapar.

## Cobertura: `cobertura.py`

Recorre los JSON crudos, reconstruye qué (keyword × ventana) se capturó de verdad y lo
compara contra lo pedido. Salida por bloque, con lista de las keywords que quedaron en cero.

Detalle no obvio: **las ventanas esperadas son las que de hecho se intentaron**, no las del
`config.yaml`. Si el primer barrido se corrió con `--windows 6`, comparar contra las 12 del
config reportaría un 50% de cobertura falso.

```
python -m pipeline.cobertura
```

Si imprime `⛔ Bloques enteros sin datos`, el `.docx` **tiene que** incluir la sección de
cobertura antes de cualquier proporción. `report.py` la genera solo cuando
`cob["vacias"] or cob["parciales"]`.

---

## Traducir los booleanos de un brief a queries de X

Un brief de cliente suele traer booleanos escritos en abstracto. Se adaptan, no se copian:

- **OR en mayúscula**, grupos entre paréntesis, AND implícito entre grupos.
  `(ONG OR "organizaciones sociales") ("financiadas por" OR mermelada OR chavistas)`
- **Un OR puro de términos genéricos trae cualquier cosa.** El núcleo de censura digital de
  un brief era `("cuenta suspendida" OR … OR hackearon OR montaje)`: «hackearon» y
  «montaje» solos devuelven ruido masivo. Se ancló con un grupo de sujeto
  (`(activista OR lideresa OR defensora OR periodista OR ONG)`).
- **Un AND de tres grupos muy genéricos tampoco sirve.** `(recursos OR cooperación) AND
  (investigación OR auditoría)` matchea medio Twitter. Se parte en dos queries: una anclada
  al trámite concreto (`"personería jurídica" (negaron OR suspendieron OR …)`) y otra que
  exige el sujeto organizativo.
- **Junto a cada booleano, poné términos autosuficientes.** Un booleano es un balde
  indiferenciado: rinde o no rinde, pero no se sabe cuál de sus seis términos lo sostiene.
  Los términos que se identifican solos —«feminazi», «aborteras», «UNDMO»— van además como
  keyword propia, y así el informe reporta rendimiento término por término.

Dejá anotado en el config **qué cambiaste respecto del brief y por qué**. Un buen brief lo
prevé explícitamente: «los booleanos son indicativos y se ajustan según la herramienta y el
piloto».

## La economía del pay-per-result cambia el diseño

El actor cobra por resultado, no por corrida. Consecuencia directa: **un término que no
rinde es casi gratis**. Eso invierte la intuición de un scraper normal —

- Sondear con muchos términos improbables **no tiene costo real**. Las 13 organizaciones
  territoriales de la escucha de espacio cívico devolvieron 0 items en el piloto: costaron ~nada y su cero es un
  hallazgo (son invisibles en la conversación nacional de X).
- El presupuesto lo marcan **los pocos términos de alto volumen**. Ahí es donde hay que
  mirar antes de lanzar, no en la longitud de la lista.
- Por eso el `--dry-run` que imprime el techo teórico sirve para acotar el peor caso, pero
  **el número que importa es el del piloto**, no el techo.

Medición real (la escucha de espacio cívico): 270 corridas → 24.963 items → **$6,24**, contra un techo teórico
de $10,12. Promedio 92,5 items por corrida, ~$0,023 cada una.

## El piloto de una ventana

```bash
python -m pipeline.scrape_x --registro vernaculo --windows 1
```

Después, rendimiento término por término. Lo que hay que mirar:

| Señal | Qué significa | Qué hacer |
|---|---|---|
| Término en el tope (`>= max_items`) | No mide volumen: mide "al menos esto" | Subirle el tope con `max_items:` propio, y declararlo en el informe |
| Un bloque concentra casi todo | La proporción entre bloques va a estar dominada por él | Verificar que no sea saturación; decidir si se reporta el bloque aparte |
| Término en 0 | Puede ser un hallazgo (ese lenguaje no circula) o un error de sintaxis | Revisar la query a mano en X antes de concluir |
| Dos entradas con el mismo `q` | La segunda se salta en silencio (mismo slug de archivo) | Borrar la duplicada; cuenta doble en cobertura |

Extrapolá el costo del piloto × número de ventanas y compará contra el saldo real de la
cuenta antes de lanzar. Consultarlo por API es una línea:

```python
requests.get("https://api.apify.com/v2/users/me/limits", headers=h).json()["data"]
# → limits.maxMonthlyUsageUsd, current.monthlyUsageUsd, limits.maxConcurrentActorJobs
```

**Verificá `maxConcurrentActorJobs` antes de fijar `--workers`.** Un default heredado del
plan Free (4) sobre un plan Starter (32 permitidas) hace el barrido cuatro veces más lento
sin ninguna razón.

## Saturación: el sesgo que no se ve

Si un término toca su tope en todas las ventanas, su volumen es un piso. Y como las
proporciones del informe se calculan sobre la base total, **la saturación de uno infla la
participación de todos los demás**.

Dos medidas, las dos necesarias:

1. Tope por término en el config, leído en el scraper con `kw.get("max_items", default)`.
2. Una tabla en el informe: qué términos saturaron, en cuántas ventanas, con qué tope. Más
   la frase que lo interpreta: *donde el documento los compara con otros, la diferencia
   verdadera es más grande que la que muestra la tabla, no más chica.*

## Gotcha de logs

Los logs del actor se redirigen al cliente y con cientos de corridas son ilegibles (2,6 MB
por barrido). Bajar a `WARNING` los loggers `apify_client` y `apify` ayuda pero **no alcanza**:
el actor crea un logger por corrida (`apify.<actor> runId:XXX`) con nivel propio, y el
registro se propaga igual a los handlers de raíz.

Y al redirigir a archivo, Python **bufferiza stdout**: las líneas de progreso del scraper no
aparecen hasta que el buffer se vacía, mientras el ruido del actor sí sale. Corré con
`python -u` cuando mandes el barrido a un log.

## Priorizar la des-saturación por rendimiento, no por nivel de saturación

Cuando el presupuesto no alcanza para des-saturar todo —lo normal—, el criterio intuitivo
(«empecemos por el que más satura») suele ser el peor. Lo que importa es **cuántos trinos
del país objetivo compra cada dólar**.

Medición real (la escucha de espacio cívico, 2026-09-15), con la señal léxica `co_score >= 3` como proxy:

| Término | Capturado | % colombiano |
|---|---|---|
| `feminazi` | 3.900 | **4%** |
| `ideología de género` | 3.900 | 13% |
| `lideresa` | 3.900 | 20% |
| `ESMAD` | 960 | **98%** |
| `UNDMO` | 1.142 | **99%** |

`feminazi` saturaba 13 de 13 ventanas y era el candidato obvio; des-saturarlo costaba $4,47
de los $8 disponibles y habría comprado ~700 trinos colombianos. Los mismos ~$5 repartidos
en doce términos anclados compraron **22.893 trinos**, la mayoría colombianos. El insulto es
paneuropeo; la sigla de la fuerza pública es solo de acá.

El cálculo se hace **antes de gastar** y sale gratis: `co_score` ya está en el corpus
capturado.

## Des-saturar es todo o nada por término

Un término se re-captura en **todas** sus ventanas o en ninguna. Hacerlo en algunas produce
un salto de volumen a mitad de la serie que parece un cambio en la conversación y es un
cambio de instrumento — el peor tipo de artefacto, porque es invisible en la gráfica.

Por eso el driver de des-saturación va término por término, no ventana por ventana, y chequea
el saldo **entre términos**: un corte por presupuesto deja términos enteros bien medidos en
vez de series rotas.

Y no borres los archivos viejos antes de re-capturar: apartalos a otra carpeta. Si la corrida
falla a mitad, se restauran. Si falla dejando archivos nuevos parciales, hay que borrarlos
**antes** de restaurar, o quedan pares (término × ventana) duplicados que inflan los conteos
crudos aunque el dedup por id proteja el corpus.
