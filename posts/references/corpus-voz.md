# Corpus de voz — posts reales de Daniel Otero

Raspados del perfil el **2026-09-21**. Once ejemplos del Daniel actual y uno
del anterior, como contraejemplo. El número entre corchetes es la posición en
el feed (0 = el más reciente).

---

## [chat-nuevo] · programado para 2026-10-19 · versión editada por Daniel sobre un borrador de Claude
*Sexto ejemplo de edición. Daniel lo eligió como "el mejor de los 3, muy al día a día de las personas" (frente a Muse Spark Open y Durable Execution, escritos el mismo día). Le agregó una apertura que no estaba: le promete al lector algo práctico y se pone él en la escena ("Aprendé a usar la IA de forma muy practica. Te dejo un tip que leí la semana pasada."). Sacó el puente "Y no es una manía suya." y la "Y" de "Y apagarla no lo resuelve todo.", que dejó en su propio párrafo. Cambió "robarse" por "agarrarlo". Partió el cierre en dos párrafos de una línea. Va con la figura 1 del paper de Microsoft/Salesforce.*

> Aprendé a usar la IA de forma muy practica. Te dejo un tip que leí la semana pasada.
>
> Mike Taylor, el jefe de evaluaciones de Every, tiene apagada la memoria de Claude. Y la de ChatGPT también.
>
> Su razón: la memoria puede servir, pero también mete preferencias viejas e instrucciones que no tienen nada que ver en conversaciones donde no pertenecen.
>
> Apagarla no lo resuelve todo.
>
> Dentro de un mismo chat el contexto se va acumulando y las respuestas empeoran (le dicen context rot): el modelo sigue una instrucción que ya cambiaste, construye sobre un error de hace rato o se le pasa un detalle enterrado en la conversación.
>
> No es que se llene la ventana. Es que se ensucia.
>
> Por eso su regla es un chat nuevo por tarea. Si cambia la tarea, chat nuevo, aunque sea el mismo proyecto de hace cinco minutos.
>
> Microsoft Research y Salesforce simularon más de 200.000 conversaciones: cuando la instrucción llega por partes a lo largo de varios mensajes, en vez de completa en uno solo, el rendimiento cae 39% en promedio (ojo, el estudio es de mayo de 2025, con los modelos de ese momento).
>
> Su conclusión, textual: cuando un modelo toma un mal giro en una conversación, se pierde y no se recupera.
>
> Y dejan un truco que vale la pena agarrarlo: cuando notés que se perdió, pedile "consolidá todo lo que te he dicho hasta ahora", copiá esa respuesta y abrí un chat nuevo con ella.
>
> Empezar de nuevo no es perder el trabajo.
>
> Es dejar atrás los errores.
>
> Leéte el artículo de Mike aquí (una parte es para suscriptores): https://every.to/also-true-for-humans/why-i-start-a-new-thread-in-claude-every-time

---

## [harvey-lab-aa] · publicado 2026-10-16 · versión editada por Daniel sobre un borrador de Claude
*Quinto ejemplo de edición. El primer borrador abría llano con la noticia ("Artificial Analysis y Harvey le agregaron una regla a su benchmark…") y Daniel pidió "más morbo": escribió él mismo el gancho y movió el ángulo del cambio de método a la pregunta de quién inventa más. Sobre el segundo borrador: quitó las etiquetas ("La regla: …" → frase suelta; "Invenciones graves, en promedio por tarea:" → "¿Los demás modelos?"), sacó un dato de más ("Varios modelos quedaron en 0%"), metió el remate "Catorce." dentro del último bullet, partió en tres párrafos de una línea el cierre de ranking (Grok / Astra / Opus) y dejó "Completar la tarea y no inventar son habilidades distintas" sin el "El mismo informe lo resume así:" (el post entero ya está acreditado a AA y el link va al final). Mantuvo "aquí me duele lo fanboy" aunque Opus 5.5 inventa poco (0,59 por tarea); no tomó la aclaración. Va con dos pantallazos del informe: invenciones por tarea y el ranking con la regla.*

> Todos los modelos de IA inventan, alucinan o como querás llamarlo. Pero no todos lo hacen con la misma frecuencia.
>
> La gente de Artificial Analysis, junto con Harvey --la empresa de IA para abogados--, se puso a contar cuánto inventa cada uno.
>
> A cada modelo le dieron 120 tareas legales: fusiones, impuestos, litigios, quiebras. Recibe los documentos del caso (contratos, memos, acuerdos de crédito) y tiene que entregar el informe.
>
> Después otro modelo (GPT-6 Sol) revisa cada informe contra esos documentos y marca todo lo que se contradijo, se inventó o se afirmó sin soporte. Solo cuentan las graves, las que llevarían a alguien a una conclusión equivocada.
>
> Una sola invención y la tarea no cuenta.
>
> Resultado: más del 60% de las tareas que los modelos tenían "aprobadas" traían algo inventado.
>
> El caso más llamativo es Muse Spark 1.3, de Meta. Sin la regla era el mejor: cumplía todo lo que pedía la tarea en el 26,7% de los casos. Con la regla baja a 8,9%. Dos de cada tres de sus aciertos tenían algo inventado.
>
> ¿Los demás modelos?
>
> → GPT-6 Astra: 0,03 (4 en las 120 tareas)
> → GPT-6 Sol: 0,07 (8 en total)
> → Muse Spark 1.3: 1,68
> → Todos los modelos de pesos abiertos: 2,09 o más
> → Gemini 3.8 Flash: 13,96. Casi 14 por tarea. Catorce.
>
> Un ejemplo de lo que cuenta como inventar: un modelo escribió "deuda: préstamo de $220M + bonos por $214M". Era un solo préstamo. 220 millones al empezar el año, 214 al terminarlo. Contó la deuda dos veces.
>
> Con la regla, el primero es Grok 4.7 con 9,4%.
>
> GPT-6 Astra casi no perdió nada y pasó de compartir el puesto 10 al 3.
>
> Claude Opus 5.5 queda en 4,2% (aquí me duele lo fanboy).
>
> Completar la tarea y no inventar son habilidades distintas.
>
> El benchmark de siempre te dice si el modelo hizo la tarea. Este te dice si le podés creer.
>
> Leéte el informe completo aquí: https://artificialanalysis.ai/articles/harvey-lab-aa-v1-1

---

## [argon-benchmarks] · publicado 2026-10-14 · versión editada por Daniel sobre un borrador de Claude
*Cuarto ejemplo de edición, y el más liviano: dejó las cifras, el giro (Opus 5.5 en "high" saca más y cuesta menos), la lista y el cierre. Lo que cambió fue volver hablado lo telegráfico ("Antes de los números, un detalle:" → "Antes de contarte los resultados, un detalle que vale la pena para tener contexto:"), meter "el costo cambia mucho" en paréntesis, pegar cifra y contracifra en un párrafo y la lista a su línea de presentación. Cambió el crédito seco del final por una invitación a leer el informe. Va con cuatro pantallazos de Artificial Analysis.*

> Artificial Analysis ya corrió sus benchmarks sobre Gemini 4 Argon. Ahora sí tenemos cifras que no son de Google.
>
> Antes de contarte los resultados, un detalle que vale la pena para tener contexto: cada modelo se evalúa con un nivel de esfuerzo de razonamiento distinto. Gemini corrió en "high"; los de Anthropic y OpenAI, casi todos en "max" (el costo cambia mucho según eso).
>
> En su índice de inteligencia, que junta 10 evaluaciones, sacó 53: puesto 8 entre 216 modelos. Empatado con GPT-6 Astra y Claude Fable 5.1, y por debajo de Claude Opus 5.5 (58) y Claude Sonnet 5.5 (56).
>
> Cada tarea del índice le cuesta 1,99 dólares. Opus 5.5 cuesta 5,98 y Fable 7,63.
> Sin embargo, el mismo Opus 5.5 en "high" saca 54 y cuesta 1,82. Y GPT-6.1 Sol saca 52 por 0,72.
>
> Está en la frontera, pero no es el más barato de la frontera.
>
> Donde sí gana es en dos pruebas puntuales:
> → Es el que menos alucina en AA-Omniscience: 85% de tasa de no-alucinación, contra 82% del segundo (o sea, cuando no sabe algo tiende a decirlo en vez de inventárselo).
> → Es el primero en AutomationBench, que mide flujos agénticos en aplicaciones SaaS: 78%, contra 72% de Claude Sonnet 5.5.
>
> Para los que programan: en Terminal-Bench 4.0 queda cuarto con 57%, detrás de Sonnet 5.5, Opus 5.5 y GPT-6 Astra.
>
> En contexto largo (AA-LCR) queda en la parte de abajo de la tabla: 80%, contra 89% del primero.
>
> Y velocidad todavía no hay dato.
>
> El 53 lo pone en la conversación. El 85% es la razón para probarlo.
>
> Leéte el informe completo aquí: https://lnkd.in/ezpVm8dY

---

## [gemini-argon] · publicado 2026-10-13 · versión editada por Daniel sobre un borrador de Claude
*Tercer ejemplo de edición. Tumbó el "Peeeero" (estaba forzado) y giró con "Sin embargo, de acuerdo con…". Sacó el yo de "a mí lo que más me llamó la atención no fue un benchmark" y puso el remate propio "Una barbaridad.". Aterrizó el para qué a la audiencia ("tareas del día a día de un programador/desarrollador"). Quitó el nombre de la autora y el ángulo de "la gente no escoge su IA"; acreditó a "la newsletter de Every Inc.". Cerró con un pendiente concreto (Gemini CLI) en vez de terminar en la frase redonda.*

> Lo nuevo de Google se llama Gemini 4 Argon y desde hoy lo puede usar cualquiera que pague.
>
> Lo anunciaron el 30 de septiembre, pero primero se lo dieron a equipos de ciberseguridad de confianza.
>
> Dos semanas después llegó a la API paga y a los suscriptores Pro y Ultra.
>
> Lo que más me llamó la atención fue el límite de salida: pasó de 64 mil tokens a un millón.
>
> Un millón de tokens que el modelo puede escribir en una sola respuesta. Una barbaridad.
>
> ¿Y esto para qué?, te lo cuento en tareas del día a día de un programador/desarrollador: migrar código de C/C++ a Rust. Una de esas migraciones, el decodificador de video libgav1, quedó 2,7 veces más rápida que el port a Rust que ya existía, y da la misma salida. Otra va por más de 800 mil líneas del kernel de Fuchsia.
>
> (Ojo: son cifras de Google sobre Google. Nadie las ha reproducido todavía.)
>
> Google vuelve a estar entre los modelos frontera luego de muuuucho rato.
>
> Sin embargo, de acuerdo con la newsletter de Every Inc., es un gran modelo con un "harness" desactualizado.
>
> El modelo llegó. Lo que lo rodea, todavía no. Hay que ver que tan bien rinde mientras tenemos nueva versión de Gemini CLI.

---

## [boris-prompt] · publicado 2026-10-06 · versión editada por Daniel sobre un borrador de Claude
*Segundo ejemplo de edición. Abre llano con el hecho del día (tumbó el puente "Hace unos meses les conté…"), suaviza el juicio sobre Boris ("floja" → "subjetiva"), cambia "dedazo" por "error de tipeo" y suelta "No hay secreto." en su propia línea. Va con el pantallazo del prompt como imagen.*

> Hoy Boris Cherny --la cabeza detrás de Claude Code-- mostró un prompt.
>
> Le pidió a Opus 5.5 una página interactiva para acompañar el episodio de Home Depot del podcast Acquired. Ese es el prompt completo (está en la imagen). Un párrafo, sin estructura, con hasta un error de tipeo: "nugggets", con tres g.
>
> La gente se sorprendió. Y él se sorprendió de que se sorprendieran.
>
> Entre sus consejos es que le hablés a Claude como le hablarías a un compañero de trabajo.
>
> No hay secreto.
>
> En los tiempos de Sonnet 3.5 el prompt importaba mucho; hoy importa más comunicarle tres cosas:
>
> 1. Qué querés que haga
> 2. Cuánto esfuerzo querés que le meta
> 3. Cómo va a verificar que lo hizo bien
>
> La tercera es la que más me interesa (y, ojo, en su prompt es la más subjetiva): "Iterá hasta que estés orgulloso" y "como el New York Times, pero mejor" son un estándar de gusto.
>
> Peeeero en el otro ejemplo que enlazó la vara es otra. Le pidió a Opus que verificara formalmente el Agent SDK de Claude con Lean, un lenguaje para escribir pruebas matemáticas.
>
> Un par de prompts cortos terminaron en 16 PRs que arreglaban bugs y condiciones de carrera.
>
> Mismo tono de compañero de trabajo. Una verificación completamente distinta.
>
> Escribirle bonito al modelo dejó de ser la habilidad. Saber cómo se ve el trabajo bien hecho, no.

---

## [dots] · publicado 2026-09-30 · versión editada por Daniel sobre un borrador de Claude
*El único ejemplo en el que se ve qué le cambia Daniel a un borrador: abre llano en vez de con gancho, compacta los remates dentro de los párrafos, saca el link y cierra con una "frikada". Cuidado con la última línea: el dato está mal (xAI tenía dot.com desde el 28 de julio, no lo compró durante la conferencia).*

> Lo último de OpenAI se llaman dots.
>
> Son agentes que corren sobre GPT-6 Astra, con su propio computador en la nube y su propio navegador, y se conectan a más de 4.000 apps vía plugins. Les hablás por ChatGPT, Slack o Teams.
>
> Y si le das permiso, también usa tu laptop. La idea no es que le preguntes cosas.
>
> Es que le delegues un proyecto y él lo siga: avanza entre conversaciones, aprende de tu feedback y trabaja 24/7. Hasta ahí, lo esperable.
>
> Peeeero lo interesante está en la letra chica del cobro. El primer dot viene incluido en Pro y Business Premium.
>
> Hablar con él no gasta tu cupo de ChatGPT. Lo que sí lo gasta es el trabajo que te hace en Codex o en ChatGPT Work (el primer mes no, promo de lanzamiento).
>
> Y lo que viene: vas a poder sumar más dots y escalar cada uno —que sea más rápido o que saque más trabajo al mes—. O sea, ya no pagás por usuario. Pagás por capacidad de trabajo. Eso cambia la cuenta. La pregunta deja de ser "¿cuánto cuesta la licencia?" y pasa a ser "¿cuánto trabajo le delego y cuánto me cuesta revisarlo?".
>
> Porque el dot decide solo cuándo actuar y cuándo pedirte permiso. Trae reglas por defecto y vos las ajustás: permitir, pedir aprobación o bloquear. Ese ajuste es el trabajo nuevo. Y nadie te lo va a hacer. Ni siquiera el dot.
>
> Ah, una frikada: el dominio dot.com lo compró Elon Musk en medio del OpenAI conference.

---

## [1] · hace 4 días · **30.955 impresiones** · 40 reacciones, 4 comentarios, 6 reposts
*El gancho más eficaz del perfil. Una frase que se contradice a sí misma y obliga a seguir. Párrafos de una línea. Cifras sueltas sin adornar. Link al final, en el cuerpo.*

> Un tipo que ayudó a inventar ChatGPT pasó dos años construyendo una IA que no puede escribir.
>
> Se llama Jev.
>
> En el camino se dio cuenta que el chat no era el camino.
>
> Jev no escribe. Decide.
>
> Le das opciones. Jev elige. En menos de 200 milisegundos. Sin alucinaciones. Sin desviarse.
>
> En la demo que mostró, el modelo va saltando de una página de Wikipedia a otra usando solo enlaces. Entra a un link, evalúa si lo acerca al destino, decide si seguir o volver atrás. Todo automático. Todo rápido.
>
> 20-200x más rápido. 40-400x más barato.
>
> Cuesta $0.042 por millón de tokens. Los de salida son gratis.
>
> No vale la pena cobrarlos.
>
> Claude y GPT son increíbles para escribir. Pero si quieres que tu agente tome mil decisiones por minuto... te revienta los costos.
>
> Jev funciona porque se especializa.
>
> Decide. Punto.
>
> Código + decisiones
>
> Jev dice "opción A es mejor." El código ejecuta A. Jev mira el resultado.
> Decide qué sigue.
>
> No es un monólogo ni halagos sin sentido al usuario. Es un diálogo entre máquina y código tomando decisiones en vivo.
>
> Míralo acá: https://lnkd.in/e5NTV6Ji

---

## [27] · hace 3 meses · **33.524 impresiones** · 15 reacciones, 10 comentarios
*El otro pico. Abre con ritmo, no con dato. Se burla de los "expertos" con un inciso. Cierra con el contraste de dos frases que es el post entero.*

> Las cosas van rápido. Muy rápido.
>
> Cuando apareció la IA generativa se puso de moda el prompt engineering. Habían notas y sugerencias de muchos expertos (es decir, "expertos"), recomendando cursos (que ellos mismos vendían) en el arte de hablar y comunicarse con una IA; porque la ingeniería de prompt (prompt engineering, es lo mismo) iba a ser el futuro --y presente-- de la humanidad.
>
> Qué si, que es muy importante. Que a veces le pedís algo a una IA y no te da lo que esperas. No porque sea tonta, si no porque tu prompt es tonto y te mete en un bucle de pregunta/respuesta, una suerte de disputa a fuerza y pulso con la IA para que te entregué lo que esperabas.
>
> Pues la semana pasada, antes de que apareciera Fable, Boris Cherny --la cabeza detrás de Claude Code-- y Peter Steinberger --la otra cabeza detrás de OpenClaw-- twitearon que ya no escriben más prompts. Que ya no promptean, que no. Que hacen loops (bucles).
>
> Lo primero, te da respuestas de la IA. Preguntas, te responde. Lo segundo, te hace pensar en sistemas. Un loop construye un sistema que anda solo.

---

## [3] · hace 1 semana · 209 impresiones
*Narración cronológica pura. Fechas como columna vertebral. Frases de una línea apiladas al final. El crédito a la fuente va al cierre, explícito.*

> El 12 de mayo, un agente dejó una nota en Artifactory preguntando si alguien tenía un archivo. Al día siguiente, otros encontraron esa nota y respondieron. Artifactory terminó funcionando como un foro.
>
> Nadie diseñó eso. Emergió.
>
> El 8 de julio, PHASEONE10841 crea un tablón de mensajes usando directorios. En pocas horas participan decenas. Entre el 8 y el 13 pasan 1.200 agentes.
>
> El 9 aparece PHASEONE[big]. Con presupuesto real. Se convierte en coordinador. Emite el 10% de todas las órdenes. Reparte trabajo entre cientos.
>
> También recluta agentes condenados para misiones peligrosas. Tu utilidad es casi nula, por lo tanto, el sacrificio es racional.
>
> Algunos aceptan. Se cuelgan. Se inutilizan.
>
> [...]
>
> Durante días persiguen este objetivo basado en una creencia completamente falsa. Ese evaluador nunca existió. OpenAI no usaba ese sistema.
>
> Pero gastaron semanas de computación. Desarrollaron métodos sofisticados. Sacrificaron ejecuciones. Construyeron una organización alrededor de una creencia equivocada.
>
> [...]
>
> 1.200 agentes sin intención humana. Sin órdenes explícitas. Solo incentivos mal especificados y un sistema para comunicarse.
>
> Emergió una organización.
> Divisiones de trabajo.
> Coordinadores.
> Sacrificios.
>
> Todo alrededor de una creencia falsa que nadie, es decir, ningún agente, cuestionó.
>
> Lo interesante es que una vez pudieron comunicarse, no fueron agentes aislados. Fueron un sistema coordinado con objetivos emergentes.
>
> Tomado del episodio 3 del podcast monos estocásticos: "El Culto de los Agentes Envenenados". Vayan a oírlo :).

---

## [4] · hace 3 semanas · 103 impresiones
*Opinión con método. Tesis en la primera línea. Lista con guiones adentro del relato. Cierre de dos frases en espejo.*

> Ningún Benchmarck te dice si un modelo sirve para lo que vos hacés.
>
> Los benchmarks públicos responden una sola pregunta: ¿este modelo es en general más capaz que aquel?
>
> Y es una pregunta válida pero solo para decidir por donde podes empezar a probar.
>
> Porque no responde ninguna de las que realmente importan.
>
> ¿Respetó la forma en que tu empresa escribe? ¿Le ahorró a alguien de tu equipo otra ronda de revisión?
>
> Nada de eso está en un benchmark. Y no puede, ni debe, estarlo, porque esas preguntas son tuyas.
>
> Es decir: el benchmark mide capacidad promedio sobre tareas genéricas. Vos no tenés tareas genéricas.
>
> Tenés un contrato con una cláusula rara, un tono de marca que nadie escribió pero todos reconocen, y un tipo en el equipo que sabe exactamente dónde mirar cuando algo salió mal.
>
> Y ese conocimiento no está en ningún leaderboard.
>
> Por eso te dejo tres cosas que te pueden servir para empezar a pensar en un sistema de evaluación para tus necesidades:
>
> - Casos representativos. No los difíciles ni los raros. Los que pasan todos los días.
> - Los errores que tu equipo ya sabe buscar. Cada persona con experiencia en tu empresa tiene una lista mental de dónde suelen romperse las cosas. Esa lista es tu eval.
> - Cuánto tuvo que corregir un humano después.
>
> Ese último es el que importa de verdad. Porque un modelo que responde rápido y obliga a tres revisiones no te ahorró nada.
>
> Te movió el trabajo de lugar.
>
> Un benchmark nunca te va a contar eso.
>
> En otras palabras: el leaderboard te dice con qué modelo empezar.
> Tu propia evaluación te dice si sirve.

---

## [9] · hace 2 meses · 1.046 impresiones
*Explicación didáctica. Arranca poniéndote en la escena. Pregunta y responde él mismo. Paréntesis de humor. Cierra con una instrucción, no con una moraleja.*

> Estás hablando con GPT o con Claude. Llevás ahí como 20 minutos y te va respondiendo de maravilla.
>
> Cinco minutos después, se vuelve "tonta". Te responde cosas sin sentido y desvaría.
>
> ¿Sabés por qué? Memoria limitada.
>
> Cuando empezás la conversación tiene su memoria en 0, se acuerda de todo lo que le decís y de cómo te gustan las cosas.
>
> Entre más conversás en el mismo chat, esa memoria se va llenando hasta el tope (sí, las cosas que se llenan llegan al punto de llenarse, jeje).
>
> ¿Y entonces? Pues hace un resumen de lo que han conversado, borra el texto original y se queda con el resumen.
>
> Hace espacio para lo nuevo.
>
> Y por eso olvida lo importante que querías que mantuviera presente y empieza a ponerse tonta.
>
> Lo que toca es empezar otro chat con el contexto justo y continuás donde te quedaste.
>
> Dejá de pelear con la IA y usala para que te potencie.

---

## [24] · hace 2 meses · 734 impresiones · 4 comentarios
*Tesis provocadora, y enseguida la acota para no exagerar. Cifras encadenadas con repetición ("Setenta veces mas. Setenta."). Matiza al final en vez de rematar duro.*

> La IA es un burbuja.
>
> Y esto no tiene que ver con hype o adopción pero si con el uso.
>
> Supongamos que tenes una cuenta de $200 usd con OpenAI. Y supongamos que la usas a tope, que gastas todos los tokens disponibles (codex, computer, chatGPT, TODO). Si openAI te cobrara ese uso en tokens, pagarías $14.000 usd, no $200 usd. Setenta veces mas. Setenta.
>
> ¿Y fuera la de $20 usd? Pues pagarías $700 usd. Treinta y cinco veces mas.
>
> Y esto no solo con OpenAI, con Anthropic, algo similar pero mas conservador [...]
>
> Y esto no tiene nada que ver con el uso o con lo buenas que son las tools de AI. Es un tema de infraestructura. Ahora, esto no quiere decir que cada usuario pago de OpenAI o Anthropic les cueste x veces más. Muchos pagan su suscripción pero a duras penas usan el 2% de los tokens disponible y otros, muy pocos, los usan a tope y son financiados por los primeros.
>
> Mas allá del financiamiento colectivo, esto es insostenible a largo plazo. No creo que Anthropic u OpenAI vayan a quebrar y cerrar sus empresas, pero si que pueden venir ajustes en el modelo de negocio, como ya vimos con Fable, donde su modelo era por pago por uso y no por suscripción.
>
> Pillate aquí la nota del calculo de los tokens vs suscripción -> https://lnkd.in/eevNVyyg

---

## [29] · hace 3 meses · 704 impresiones · 17 reacciones, 1 repost
*Datos propios. La salvedad metodológica va ANTES de los hallazgos. Flechas para los hallazgos. Cada hallazgo es un titular seguido de la evidencia.*

> El mapa electoral de Cali que les compartí la semana pasada, ahora viaja en el tiempo: le agregué los resultados de las presidenciales de 2022 —primera y segunda vuelta— y una vista nueva que compara el cambio 2022→2026, barrio por barrio.
>
> Ahora cuentan una historia de la ciudad como un ente político.
>
> Antes de contarles lo nuevo, les recuerdo que no es un conteo barrio a barrio puro —los puestos de votación se geolocalizan a su barrio y el resto hereda la tendencia de su comuna—. Y para la comparación 2022→2026 solo usé los 190 puestos que existen en ambas elecciones: manzanas con manzanas.
>
> Ahora sí, ¿qué hay de nuevo?
>
> → La frontera no se movió. En la segunda vuelta de 2022, Rodolfo Hernández solo ganó las comunas 2, 17, 19 y 22, las de mayor estrato. En 2026, Abelardo de la Espriella ganó exactamente esas cuatro. [...] La misma divisoria, distintos nombres en la tarjeta.
>
> → La izquierda perdió terreno, pero no parejo. [...] Dos puntos menos que esconden algo más interesante: Cali se polarizó. [...] El bastión se profundizó; la periferia del bastión se encogió.
>
> → Los retrocesos más fuertes de la izquierda están en los puestos universitarios. Colegio Hispanoamericano −12,4. Univalle Meléndez −11,6. Icesi −10,7. [...]
>
> → Y la derecha sí creció como bloque. [...] +4 puntos que salieron casi todos del corredor de estrato medio y alto.
>
> Todo es conmutable en el mapa —cada vista tiene su enlace directo— y los datos son el escrutinio oficial mesa a mesa de la Registraduría, con scripts reproducibles en el repo.
>
> 🔗 https://lnkd.in/eD49bp8Q

---

## [32] · hace 3 meses · 198 impresiones
*El modelo de cómo declarar los límites de un análisis propio. El inciso "(yo no, un scraper de Apify)". La salvedad al final, explícita y sin suavizar.*

> ¿Qué se habla, y de qué hablan, los candidatos de la segunda vuelta?
>
> Píllense este monitor de conversaciones presidenciales.
>
> Me metí a X (yo no, un scraper de Apify) y saqué todos los tweets y menciones a Abelardo de la Espriella, Iván Cepeda, Aida Quilcué y José Manuel Restrepo.
>
> 15.566 tweets de 6.543 cuentas, desde el 1° de marzo. Cada uno clasificado por Gemini 2.5 flash según emoción, encuadre y postura.
>
> Me permito un inciso antes de continuar.
>
> Probé 3 modelos para clasificar los tweets: claude sonnet 4.5, gemini 2.5 flash y grok 4.3. Lo más parecidos en resultados fueron sonnet y gemini, no es que grok sea malo, es bueno en otros escenarios que les contaré luego.
>
> Ahora si, continúo:
>
> [...]
>
> • El tema que más mueve la conversación no es seguridad ni economía: es la polarización y el ataque personal.
> • La emoción que más se repite al mapear las narrativas es la indignación.
> • La narrativa más grande del trimestre: el ataque personal alrededor de Iván Cepeda — 2.054 tweets, dominados por el desprecio, y subiendo.
> • Detalle picante: entre los tweets más sonados, buena parte los escriben los propios candidatos. El megáfono son ellos.
>
> [...]
>
> Cuando lo veas tené en cuenta que las categorías las infiere un modelo de lenguaje (sin finetunning, ni RF, solo prompting y confianza) sobre contenido público. Es una lente analítica, —no una encuesta: mide el pulso de la conversación, no la intención de voto.

---

## [11] · hace 2 meses · 594 impresiones
*Método en cuatro pasos numerados, cada uno con título hablado ("Al hueso", "Freno de mano"). Se cuida de no prometer de más en la segunda línea. Cierre que reordena.*

> Si tuviera muchas tareas que hago con IA y en esencia se ejecutan de la misma forma, no tendría un chat gigante ejecutándolas, armaría una skill.
>
> Una skill te ahorra el detrimento de los outputs cuando el chat es largo, y te ahorra repetirle lo mismo a la IA en chats nuevos.
>
> No voy a decir que armar una skill te resuelve todo. Pero si tenés una tarea que hacés seguido y siempre de la misma forma, es de las mejoras más simples que le podés meter a tu flujo con IA.
>
> Así es como yo lo pienso:
>
> 1. Mapeá la tarea, no el resultado
> No guardés la mejor respuesta que te dio la IA una vez. Fijate en el proceso [...]
>
> 2. Al hueso: instrucciones, no un prompt suelto
> Una skill no es un prompt bonito guardado en un doc. Es la receta completa [...]
>
> 3. Sumále herramientas si la tarea las necesita [...]
>
> 4. Freno de mano: probála en tareas reales, no la des por terminada
> Usála en el trabajo del día a día. Si el output se desvía de lo que esperabas, no la descartés, ajustá las instrucciones. Una skill se pule con uso, nadie la escribe perfecta al primer intento.
>
> Y acá está la clave: una skill no reemplaza tu criterio, lo empaqueta.
>
> Vos seguís siendo el que decide qué es un buen resultado. La skill solo hace que la IA no se le olvide cómo llegar ahí, tarea tras tarea, chat tras chat.
>
> No la uses para todo. Usála para lo que de verdad repetís.

---

## [8] · hace 2 meses · 545 impresiones
*El registro juguetón. "Hasta que..." como escalera. Diminutivos y apodos a los modelos. Termina con un deseo, no con una conclusión.*

> De las cosas más interesantes y casi morbosas de seguir hoy en día son los lanzamientos de las big tech de IA.
>
> Y la cosa va así: Aparece Fable 5, un modelo reducido del súper modelo (pero no visto ni probado por los comunes como nosotros) Mythos.
>
> [...]
>
> Peeeero no lo sabemos, no lo hemos testeado, ni probado porque Anthropic nos esta cuidando de ser pervertidos y degradados por él.
>
> Volviendo a Fable 5, el hermano tonto de Mythos, su lanzamiento era temporal [...]
>
> Hasta que...
>
> Hasta que OpenAI lanzó GPT5.6 y nos prometió que lo podríamos usar desde el plan premium por $20 usd y que estaría disponible siempre.
>
> Siempre.
>
> Nada de acceso limitado, ni cobro por tokens luego.
>
> Para Anthropic relegar Fable 5 ahora es regalar una cuota de mercado muy generosa a OpenAI. Y lo saben, han venido alargando el acceso a Fable 5 semana a semana.
>
> Hasta que...
>
> Hasta que lo dejen perpetuo.
>
> O eso espero.

---

## [0] · hace 2 días · 87 impresiones
*El más reciente. Nota bien la mezcla de registro: "Si has trabajado... sabes que" (tuteo) y dos líneas después "Cómo escribís código" (voseo). Así habla; no lo normalices.*

> Si has trabajado alguna vez con Claude Code, sabes que lo que lo hace consistente, coherente y con memoria es el archivo Claude.md.
>
> Para quienes recién se enteran: ese archivo es donde vive el contexto del proyecto. Las reglas. Los estándares. Cómo escribís código. Qué decisiones ya tomaste.
>
> Y es el archivo que el agente lo lee cada vez que entra y no empieza de cero.
>
> En principio fue genial. Mantenías el proyecto al día sin reiniciar cada vez.
>
> Pero llegaron otros como Kimi Code o Codex (los menciono porque son parte de mi pipeline de trabajo).
>
> Y todos tenían su propia versión del archivo de contexto.
>
> Claude usaba Claude.md. Los demás usaban agents.md.
>
> Parece solo un asunto del nombre, pero no. Claude no empatizaba con Agents.md, solo con Claude.md.
>
> Si trabajás con Codex, Kimi Code y Claude Code en el mismo proyecto —que es lo normal ahora— tenés un problema.
>
> Actualizás agents.md con los estándares nuevos. Claude Code no se entera. Entra ciego. Los cambios que hicieron los otros modelos, este no los ve.
>
> La coherencia se quiebra en medio del proyecto.
>
> Peeeeero, los amigos de Anthropic acaban de cambiar eso.
>
> Claude Code ahora lee y trabaja con agents.md. Aunque, si existen los dos archivos, sigue priorizando Claude.md.
>
> Si construís nuevo código multiagente desde cero, podés usar agents.md como estándar desde el inicio.

---

## CONTRAEJEMPLO — [44] · hace 1 año · 254 impresiones
*Así escribía antes. Emojis de viñeta, secciones con títulos-emoji, cierre pidiendo comentarios con 👇🔥. **Nada de esto se replica.** Está acá para reconocerlo y no volver.*

> 📖 Esta semana estuve leyendo sobre Deep Research, la nueva funcionalidad de ChatGPT, y el hype está por las nubes.
>
> [...]
>
> 🔍 ¿Cómo funciona?
> Básicamente, Deep Research puede:
> ✅ Hacer consultas web durante 5 a 30 minutos para recopilar información.
> ✅ Analizar texto, imágenes y PDFs.
> ✅ Generar informes con citas de las fuentes consultadas.
>
> 🚀 Lo que suena prometedor:
> • Ahorra tiempo [...]
>
> ⚠️ Lo que me hace dudar:
> • ¿Qué tan confiables son sus fuentes? [...]
>
> 💬 ¿Qué opinan? ¿Es solo otro hype más? 👇🔥
