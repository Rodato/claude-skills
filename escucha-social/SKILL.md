---
name: escucha-social
description: >-
  Receta para escuchas sociales en X (Twitter) que terminan en un .docx
  defendible: diseño de keywords con anclaje por país, captura por ventanas
  vía Apify, clasificación LLM sobre taxonomía cerrada, y un reporte que
  separa LO MEDIDO de LA LECTURA, declara su propia cobertura y desglosa las
  cifras gruesas antes de que alguien las cite. Úsala al arrancar, extender o
  revisar una escucha social —una existente o una nueva— y sobre todo
  cuando el corpus sea chico, parcial o sesgado por el diseño de búsqueda:
  el problema de estos informes no es graficar, es no afirmar de más.
---

# Escucha social en X — del barrido al reporte que aguanta

Receta para un pipeline de escucha digital que va de un brief con keywords a un
`.docx` que un cliente puede citar sin quedar expuesto. Dos proyectos vivos la
implementan; el segundo se portó del primero a mano, y esta skill existe para que
el tercero no repita ni el copy-paste ni los errores que ya se pagaron.

**La tesis:** montar el scraper es la parte fácil y barata. Lo difícil —y lo que
distingue un informe de escucha de un tablero de conteos— es **decir con cuánto se
cuenta antes de afirmar nada**, y desglosar toda cifra gruesa hasta el número que
de verdad aguanta.

## Cuándo usarla

- Arrancar una escucha nueva en X sobre un tema de conversación pública.
- Extender una existente: más ventana, más keywords, otra plataforma, otra iteración.
- Escribir o revisar el `.docx` de resultados.
- Revisar un hallazgo antes de entregarlo ("¿este 20% se sostiene?").
- Diseñar la taxonomía de clasificación de un corpus de texto social.

## Proyectos de referencia (leé el código real antes de inventar)

La receta sale de dos escuchas reales en Colombia, en repos privados. Si en esta carpeta
existe `LOCAL.md` (no se versiona), ahí están sus rutas: leé ese código antes de inventar.

| | **Movilidad eléctrica** | **Espacio cívico** |
|---|---|---|
| Tema | Movilidad eléctrica / híbridos en Colombia | Espacio cívico en Colombia |
| Keywords | 25, del brief del cliente | 45 en 7 bloques, de notas de reunión |
| Corpus | Keywords + **hilos de respuestas** | Keywords + **barrido por cuenta** (`emite` / `menciones`) |
| Eje del reporte | Dos conversaciones que no se tocan | Espacio en uso vs. espacio en disputa |
| Extras propios | `scrape_replies` | `cobertura.py`, variantes ancladas, corte por cambio de gobierno |

La de espacio cívico es la más madura: si vas a portar algo, portá de ahí. Su `README.md`
lista los gotchas del proyecto; esta skill guarda los que **trascienden** el proyecto.

---

## La regla madre: un dato no es un hallazgo

Todo lo demás es plomería. Esto es lo que hace que el informe aguante.

### 1. La cifra gruesa casi siempre mezcla dos cosas — desglosala antes de publicarla

Ejemplo, con cifras ilustrativas: el clasificador devuelve **20% de trinos que
estigmatizan**. Titular con eso sería un error si el 40% de esos trinos está
encuadrado como **disputa partidista** —el insulto apunta a un bando y quien se
organiza queda de paso— y solo el **1%** de la base nombra efectivamente a una
organización.

El informe publica el desglose completo y **la lectura sostiene la cifra chica**:

> 20% total → 8% partidista + 12% fuera de la trinchera → 1% nombra una organización

Regla operativa: **antes de reportar una proporción, cruzala con el encuadre.** Si
una porción grande vive dentro de otra categoría que explica mejor el fenómeno, la
cifra gruesa no es el hallazgo — es la pregunta. Y la distinción tiene que servirle
a alguien: en este caso, lo partidista se combate cambiando el clima político (fuera
del alcance del cliente) y lo otro disputando el sentido de organizarse (a su alcance).

### 2. Separar LO MEDIDO de LA LECTURA, en secciones distintas y anunciadas

La sección «Lo que se midió» contiene **solo** conteos y proporciones del dataset.
La sección «Lectura» contiene interpretación y **lo dice en su primera línea**. La
portada trae un bloque «Cómo leer este documento» que explica la separación. Nunca
una afirmación interpretativa vestida de número.

### 3. La prosa de la lectura es condicional al dato, no escrita de antemano

`sec_lectura()` en `report.py` ramifica: si `n_uso > n_disp` escribe un párrafo, si
`n_disp > n_uso` escribe otro —en negrita, porque es la señal preocupante— y si
empatan lo dice. Igual con estigmatización (tres ramas) y con efecto inhibitorio
(el umbral `< 5%` cambia la frase entera).

Esto no es coquetería: es lo que permite **regenerar el informe cuando entren más
datos sin reescribir la interpretación a mano**, y lo que evita que quede una frase
del borrador anterior contradiciendo la tabla de al lado.

### 4. Declarar la cobertura ANTES de cualquier proporción

Si el barrido se interrumpió, el informe lo dice en la sección de método, en negrita,
con tabla por bloque y lista de los términos que nunca se buscaron. En la escucha de espacio cívico el
hueco **no fue aleatorio** (las corridas salen en orden de keyword, así que se perdió
el final de la lista y dos bloques quedaron en cero) — y esos bloques eran centrales
al encargo. Una proporción sobre esa base subestima justo lo que no se buscó.

`cobertura.py` (en `templates/`) calcula esto solo. **Corrélo siempre antes de `report`.**

### 5. Distinguir el vacío de diseño del vacío de la conversación

Un `estigmatiza` bajo puede significar que no hay ataques… o que **ninguna keyword
salió del vocabulario de los detractores**. En la escucha de espacio cívico se buscó con las palabras de
las organizaciones y del encargo; por eso el informe escribe:

> "Es un vacío de diseño, no necesariamente de la conversación."

Toda ausencia notable en los datos exige preguntarse si el instrumento podía verla.

### 6. Una sección «Qué no puede responder este ejercicio»

Fija y explícita, con los límites estructurales: mide conversación *sobre* el tema,
no el tema; X no es la opinión pública; ventana ≠ causalidad; la clasificación
automática tiene margen de decenas de casos, sirve para proporciones y contrastes,
no para cifras exactas.

### 7. Entregar la base auditable junto al .docx

`base_analisis.csv` y `base_cuentas.csv` salen del mismo `report.py`. **El cliente
tiene que poder verificar cualquier número del documento.** Un informe de escucha sin
su CSV es una opinión con tablas.

### 8. Buscá en el vocabulario del fenómeno, no en el del encargo

Los conceptos del encargo suelen venir en **registro jurídico o institucional** —«espacio
cívico», «libertad de asociación», «transición energética justa»— y casi nadie escribe así.
Rastrearlos devuelve comunicados y foros de cooperación, no conversación.

El registro que importa es el **vernáculo**, e incluye el de los detractores: «feminazi»,
«falsas ONG», «me reportaron la cuenta», «viven de la cooperación». Medido en la escucha de espacio cívico: el
registro jurídico dio 2 trinos colombianos de cada 60; una sola ventana del vernáculo dio
1.726 items.

Al cambiar de registro, **no borres el viejo: degradalo a contraste medible** (`registro:
juridico`). Así el informe puede afirmar con números *cuánto* rinde cada uno, que es en sí
un hallazgo, en vez de pedir que se le crea.

### 9. Un piloto de una ventana antes de comprometer presupuesto

Nunca lances el barrido completo con queries sin medir. Corré **todas las keywords nuevas
sobre una sola ventana**, mirá el rendimiento término por término y recién ahí extrapolá.
En la escucha de espacio cívico el piloto costó **$0,43** y reveló tres cosas que habrían arruinado el barrido
completo: cinco términos saturando el tope, dos keywords duplicadas entre bloques, y que el
núcleo de género pesaba el 47% del volumen.

### 10. Un término saturado no mide volumen

Si un término toca su tope de resultados, su cifra dejó de ser una medida: es un piso. Y el
daño no queda ahí — **sesga hacia arriba la participación de todos los demás**. Si «feminazi»
devuelve su tope todos los meses y «personería jurídica» devuelve cinco trinos, la distancia
real entre los dos es mayor que la de la tabla, no menor.

Dos cosas: un tope por término (`max_items:` en su propia línea del config) para los que
saturan, y una tabla en el informe que diga **cuáles saturaron y en cuántas ventanas**.

---

## El pipeline

```
scrape_x.py      →  normalize.py  →  classify.py  →  cobertura.py  →  report.py
scrape_cuentas.py   dedup + señal    OpenRouter      qué falta        .docx + CSV
  Apify (X)         de país          (taxonomía)                      + figuras
```

| Paso | Qué hace | Detalle |
|---|---|---|
| `scrape_x` | Keyword × ventana mensual vía actor Apify. Reanudable. | `references/captura.md` |
| `scrape_cuentas` | Cuentas objetivo en dos modos: `from:` y mención | `references/captura.md` |
| `normalize` | Dedup por id, acumula keywords por tweet, `co_score` léxico | `references/captura.md` |
| `classify` | LLM barato sobre taxonomía cerrada. Caché por id. | `references/clasificacion.md` |
| `cobertura` | Qué (keyword × ventana) se capturó y qué no | `references/captura.md` |
| `report` | `.docx` medido/lectura + CSV auditables + PNG 300dpi | `references/reporte.md` |

```bash
/opt/homebrew/bin/python3.14 -m venv .venv && .venv/bin/pip install -e .
cp .env.example .env      # APIFY_TOKEN + OPENROUTER_API_KEY

.venv/bin/python -m pipeline.scrape_x --dry-run --windows 6   # queries sin gastar
.venv/bin/python -m pipeline.scrape_x --smoke                 # 2 kw × 1 ventana
.venv/bin/python -m pipeline.scrape_x --windows 6
.venv/bin/python -m pipeline.classify --limit 60              # smoke barato
.venv/bin/python -m pipeline.classify
.venv/bin/python -m pipeline.cobertura                        # ANTES de reportar
.venv/bin/python -m pipeline.report
```

## Los seis gotchas que se pagan caro

Cada uno costó una corrida perdida o un dato invertido. El detalle está en los
references; esto es el índice para no releer todo.

1. **`lang:es` no acota por país.** Trae México, Argentina, España, Chile, Perú. El
   país se decide **por contenido en la clasificación**, no por la `location` del
   perfil (vacía en buena parte de las cuentas colombianas). → `captura.md`
2. **Los términos genéricos son casi todos de otros países.** Medido: `"espacio
   cívico"` dio 2/60 colombianos, `ONG Colombia` dio 56/60. Solución: cada término
   genérico corre en **dos versiones, amplia y anclada**; el dedup por id evita el
   doble conteo. → `captura.md`
3. **Un tope de cuota no se reintenta: se aborta.** Tratarlo como fallo transitorio
   perdió 128 corridas en silencio. `QuotaExceeded` corta el barrido y avisa. →
   `captura.md`
4. **La concurrencia depende del plan:** 5 corridas en Free, 32 en Starter; la sobrante se
   rechaza al instante. Verificá el plan con la API antes de fijar `--workers` — un default
   de 4 heredado del plan free hace un barrido 4 veces más lento del necesario. → `captura.md`
5. **Ejercer ≠ denunciar.** El error más costoso de la clasificación: la primera
   versión contaba como ataque los comunicados que *rechazan* señalamientos, y el
   dato salía **invertido**. Dos campos booleanos separados, y lo mismo con el
   efecto inhibitorio (denunciar un riesgo no es haberse replegado). →
   `clasificacion.md`
6. **Dos bloques del config con la misma keyword** producen el mismo slug de archivo: la
   segunda se salta en silencio, pero cuenta doble en cobertura y en la tabla de
   rendimiento. Chequealo con un `Counter` sobre `q` antes de barrer. → `captura.md`
7. **El modelo devuelve valores fuera del enum** —incluso el nombre de otro campo
   como valor—. Se fuerza en la normalización (`_pick`, `_clean_multi`), no en el
   reporte. → `clasificacion.md`

## Checklist antes de entregar

- [ ] `cobertura.py` corrido; si hay huecos, están declarados en el `.docx`.
- [ ] Toda cifra gruesa de un booleano, cruzada con el encuadre y desglosada.
- [ ] La sección de lectura no afirma nada que la tabla no sostenga.
- [ ] Las ausencias tienen su párrafo de "vacío de diseño vs. de la conversación".
- [ ] Existe «Qué no puede responder este ejercicio».
- [ ] `base_analisis.csv` sale junto al `.docx`.
- [ ] Poblaciones distintas (keywords vs. cuentas, `emite` vs. `menciones`) no se
      mezclaron en ninguna proporción, y la tabla lo advierte.
- [ ] Los términos que saturaron el tope están declarados.
- [ ] Si el cliente exige validación humana de la codificación automática, existe el reporte
      de concordancia — o el informe declara que sus cifras son provisionales.
- [ ] Los datos crudos NO se commitean: `data/` va en `.gitignore`; el repo guarda
      el pipeline, no el corpus.

## Templates

Código ya genérico, listo para copiar a `pipeline/` de un proyecto nuevo:

| Archivo | Qué trae |
|---|---|
| `templates/_common.py` | Cliente Apify, `chunk_windows`, `build_query`, `QuotaExceeded`, guardado de raw |
| `templates/cobertura.py` | Auditoría de (keyword × ventana) capturado vs. pedido |
| `templates/docx_helpers.py` | `_style`, `p`, `bullet`, `table`, `num`, `pct`, `figura`, `multi_counter` |
| `templates/charts.py` | Paleta validada + 6 gráficas a 300 dpi para incrustar |
| `templates/config.yaml` | Esqueleto comentado: ventana, keywords con `bloque`/`detecta`/`nivel`/`registro`, cuentas |
| `templates/qa.py` | Muestra estratificada del 10% para codificación humana + κ de Cohen |

Lo que **no** es template y hay que escribir por proyecto: la taxonomía y el
`SYSTEM_PROMPT` de `classify.py`, y las secciones de `report.py`. Ahí vive el
encargo. → `references/clasificacion.md` y `references/reporte.md`.
