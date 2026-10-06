---
name: posts
description: >-
  Cómo escribe Daniel Otero sus posts de LinkedIn. Destilada de los 53 posts
  realmente publicados en su perfil (raspados el 2026-09-21), no de una idea de
  cómo debería escribir. Cubre el registro (voseo colombiano mezclado), la
  arquitectura del post, los recursos de voz que se repiten —la frase de una
  línea, el "Peeeero", el inciso que baja el tono, la salvedad metodológica— y
  las reglas de listas, links y longitud. Úsala cuando el pedido sea escribir,
  reescribir o ajustar un post para LinkedIn: "armá un post", "escribí algo
  sobre esto", "pasá esta noticia a post", "mejorá este borrador". No es para
  correos (esa es `correos`) ni para informes.
---

# posts — cómo escribe Daniel en LinkedIn

Base empírica: los **53 posts propios** del perfil, leídos el 2026-09-21. Cuando
esta skill dice "Daniel hace X", es porque X aparece varias veces en ese corpus.
Los ejemplos completos están en `references/corpus-voz.md`.

## Lo primero: qué escribe hoy

El perfil cambió de tema hace unos meses y la mayoría de las guías viejas
(incluidos los "content pillars" del vault de Obsidian) describen al Daniel
anterior. Hoy, de los últimos ~30 posts, la gran mayoría son **comentario
narrado de noticias de IA** —lanzamientos de modelos, papers, benchmarks,
notas de prensa— y una minoría son sus propios dashboards de datos abiertos.

Los dos posts de mayor alcance del perfil (30.955 y 33.524 impresiones) son
los dos del primer tipo, y comparten la misma forma: una frase de apertura
corta y desconcertante, sin contexto previo, y después la historia.

El resto vive entre 50 y 700 impresiones. No hay una fórmula que garantice el
pico; sí hay una forma que lo produjo dos veces.

## El registro

**Voseo colombiano, mezclado — y así se queda.** Daniel alterna "vos", "tú" y
"ustedes", a veces dentro del mismo post: *"Si has trabajado alguna vez con
Claude Code, sabes que…"* y tres líneas después *"Cómo escribís código"*.
No lo normalices a voseo puro: suena más falso que la mezcla. Regla práctica:
**voseo por defecto, "ustedes" cuando se dirige al grupo** ("Miren esto",
"Les dejo", "Pueden darle una mirada"), tuteo cuando se le escapa.

Nada de jerga rioplatense ni española. Palabras corrientes.

**Párrafos de una a tres líneas.** Una idea por párrafo. Línea en blanco entre
cada uno. Se lee en el celular de un scroll.

## La arquitectura

**El gancho: una o dos frases, sin preámbulo.** Funciona cuando planta algo que
no cuadra y obliga a seguir:

- *"Un tipo que ayudó a inventar ChatGPT pasó dos años construyendo una IA que no puede escribir."*
- *"Las cosas van rápido. Muy rápido."*
- *"El 12 de mayo, un agente dejó una nota en Artifactory preguntando si alguien tenía un archivo."*
- *"Ningún Benchmarck te dice si un modelo sirve para lo que vos hacés."*
- *"Cali recauda 5,1 billones de pesos en impuestos al año. Casi nadie lo ve."*

No arranca con "En este post voy a…" ni con una pregunta retórica floja.

**El cuerpo: prosa corrida, sin subtítulos.** Cuenta qué pasó, en orden, con
las cifras adentro de la frase. Las transiciones son habladas: "Y es que…",
"Ahora sí…", "Volviendo a…", "Lo que pasa técnicamente es esto:".

**El cierre: una idea que reordena lo anterior.** No es un llamado a la acción.

- *"La economía crece, pero los trabajadores reciben una porción más chica de un pastel más grande."*
- *"El leaderboard te dice con qué modelo empezar. Tu propia evaluación te dice si sirve."*
- *"Un loop construye un sistema que anda solo."*
- *"Una skill no reemplaza tu criterio, lo empaqueta."*

En los posts de producto propio sí hay invitación, pero es a romperlo, no a
comentar: *"Úsenlo, rompanlo y me avisan como lo mejoramos."*

## Los recursos de voz (esto es lo que lo hace sonar a él)

**La frase de una línea como párrafo.** El recurso más característico. Corta el
ritmo y remata.

> Decide. Punto.
> Nadie diseñó eso. Emergió.
> Siempre.
> Setenta veces mas. Setenta.
> El modelo no desapareció. Lo enjaularon.

**La "e" estirada.** `Peeeero` / `Peeeeero` marca el giro del post. Aparece en
varios. También `Hasta que…` repetido como escalera.

**El inciso que le baja el tono a lo que acaba de decir.** Entre paréntesis o
entre guiones largos:

> Me metí a X (yo no, un scraper de Apify)
> Habían notas y sugerencias de muchos expertos (es decir, "expertos")
> las preguntas que importan (o que creo que importan, ustedes dirán)
> Un jailbreaker --si es que puede llamarse así--

**La auto-corrección en voz alta.** `Invirtió (¿gastó?)`, `No se fue de verdad, verdad.`

**El diminutivo a las herramientas.** "Claudito", "el hermano tonto", "su primo tonto".

**El crédito explícito, con humildad real.** Cuando la idea, el análisis o el
trabajo no son suyos lo dice primero, no en letra chica: *"No, no se me ocurrió
a mí, ya quisiera"*, *"Tomado del episodio 3 del podcast monos estocásticos"*.

**Pero el crédito va a la fuente, no al canal.** Si Daniel se enteró de algo por
una cuenta de X, un newsletter o un agregador, **esa cuenta no se menciona en el
post**. El que descubrió el link no es el autor de la historia. Se cita a quien
hizo el trabajo —el paper, el writeup, la empresa, el podcast que produjo el
análisis— y punto. La historia la cuenta Daniel.

La diferencia práctica:

- El mapa electoral de Ricardo Ruiz → **sí** se acredita, porque el método es
  de él y Daniel lo adaptó.
- El podcast monos estocásticos → **sí**, porque el relato es de ellos.
- La cuenta de X que resumió el writeup de Hacktron → **no**. Se cita Hacktron.

**La salvedad metodológica antes de las cifras, no después.** Regla dura en
cualquier post con datos propios:

> Antes de contarles lo nuevo, les recuerdo que no es un conteo barrio a barrio
> puro —los puestos de votación se geolocalizan a su barrio y el resto hereda
> la tendencia de su comuna—.

> Cuando lo veas tené en cuenta que las categorías las infiere un modelo de
> lenguaje (sin finetunning, ni RF, solo prompting y confianza). Es una lente
> analítica, no una encuesta.

**El sesgo declarado.** Si es fan de algo, lo dice: *"aquí se me sale lo fanboy
de Anthropic que soy"*.

## Listas

La guía vieja decía "nunca bullets". Es falso: **la mayoría de los posts largos
llevan lista.** Lo que no lleva nunca es asterisco de markdown ni negrita de
subtítulo.

- `→` es el marcador por defecto en posts de datos y de producto
- `-` o números `1. 2. 3.` cuando son pasos de un método
- `—` em-dash en enumeraciones cortas dentro de prosa

**Lo que desapareció y no vuelve:** los bullets con emoji (✅ 📌 🔹 🚀 💡). Están
en los posts de hace un año y ya no aparecen en los recientes. Es una corrección
que Daniel ya hizo solo; no la deshagas.

Una lista no reemplaza la historia. Va adentro del relato, no en lugar de él.

## Links

**Van en el cuerpo del post, no en el primer comentario.** La guía del vault
dice lo contrario; los posts reales —incluidos los dos de mayor alcance— llevan
el link adentro y les fue bien.

El formato varía y no hay que forzarlo a uno solo:

> Míralo acá: <url>
> Leé la nota completa aquí: <url>
> Link: <url>
> Pillate aquí la nota del calculo de los tokens vs suscripción -> <url>
> 🔗 Dashboard: <url>  ·  💻 Código: <url>

El 🔗 y el 💻 aparecen sobre todo en los posts de dashboards propios.

**Hashtags: casi nunca.** Los recientes no llevan. Si el post es de datos
abiertos con vocación de alcance, tres o cuatro máximo y específicos.

## Longitud

150–400 palabras es el centro de gravedad. Los dos posts de mayor alcance
rondan las 200. Los de datos propios se estiran a 400–600 porque tienen que
explicar el método. Por debajo de 40 palabras solo funcionan los posts de
"ojito que pasó esto".

## Lo que nunca

- Subtítulos en negrita ni recuadros
- "Déjame en comentarios", "envía X y te paso la guía" (lo ridiculiza
  explícitamente en un post)
- Afirmar una cifra sin fuente, o mezclar lo medido con la interpretación sin
  marcar cuál es cuál
- Atribuirse una idea ajena
- Hype vacío: "game changer", "esto lo cambia todo", "imperdible"
- Pulir hasta el brillo. Los posts reales tienen tildes perdidas y algún dedazo.
  Un texto perfecto no suena a él.

## Lo que Daniel le cambia al borrador

Lo que corrige cuando le paso un borrador. Pesa más que el corpus, porque es
él editando el texto escrito para él. Hasta ahora son dos posts (dots de
OpenAI, 2026-09-30, y el prompt de Boris Cherny, 2026-10-06; los dos en
`references/corpus-voz.md`), así que tomalo como tendencia, no como ley.

- **Tumbó el gancho ingenioso y abrió con una presentación llana.** Yo puse
  *"OpenAI no lanzó un chatbot nuevo. Lanzó un empleado con cupo mensual."* y
  él lo cambió a *"Lo último de OpenAI se llaman dots."* Si el gancho tiene
  que estirar la realidad para sonar bien, mejor abrir directo con la cosa.
  **Pasó otra vez** en el de Boris: tumbó el puente a un post viejo suyo
  (*"Hace unos meses les conté que…"*) y abrió con el hecho del día: *"Hoy
  Boris Cherny --la cabeza detrás de Claude Code-- mostró un prompt."* No
  abras recordando posts anteriores; abrí con lo que pasó.
- **El largo de los párrafos lo decide él, no una regla.** En dots juntó los
  remates dentro del párrafo; en el de Boris hizo lo contrario y soltó
  *"No hay secreto."* en su propia línea y partió el párrafo de Lean en dos.
  No conviertas cada frase en un párrafo, pero tampoco pelees por eso.
- **Le baja el filo a los juicios sobre otras personas.** Cambió *"en su
  prompt es la más floja"* por *"la más subjetiva"*, y sacó *"Para una página
  sobre un podcast alcanza"*. Cuando el post critica a alguien con nombre,
  describí, no califiques.
- **Prefiere la palabra neutra al coloquialismo forzado.** "Dedazo" →
  "error de tipeo". Y usa `--` como guion de inciso, no `—`.
- **Sacó el link al anuncio.** En posts de noticia de producto, no lo
  agregues por reflejo. Ofrecelo.
- **Cerró con un dato lateral y liviano**, después del cierre argumental:
  *"Ah, una frikada: …"*. Es una posdata curiosa, no una conclusión. Ese dato
  también se verifica: en ese post, la versión de Daniel decía que Musk compró
  dot.com en plena conferencia, y en realidad xAI lo tenía desde julio.
  **No es una plantilla:** Daniel lo dijo explícitamente ("no siempre debe
  tener lo de la frikada al final... no exageres"). Solo va si el dato surge
  solo y vale la pena; por defecto el post termina en el cierre argumental.
  Lo mismo aplica a cualquier recurso de esta lista: no metas todos en cada post.

## Checklist antes de publicar

1. ¿La primera frase se sostiene sola, sin contexto?
2. ¿Los párrafos son de una a tres líneas?
3. ¿Hay al menos una frase de una línea que remate?
4. ¿Cero subtítulos, cero asteriscos, cero bullets con emoji?
5. Si hay cifras propias, ¿está la salvedad metodológica ANTES de las cifras?
6. Si la idea es de alguien más, ¿está el crédito arriba y con nombre?
7. ¿El crédito es a la FUENTE y no al canal? (nada de nombrar la cuenta de X o
   el newsletter donde apareció el link — eso es el radar, no la fuente)
8. ¿El cierre reordena, en vez de pedir un comentario?
9. ¿El link está en el cuerpo?
10. ¿Desapareció el hype?
11. ¿Suena a alguien explicando algo que le importa, o a alguien posicionándose?


## Ejemplos completos

`references/corpus-voz.md` — doce posts reales con su alcance y qué hace cada uno.
