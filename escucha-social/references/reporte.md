# El reporte: estructura, prosa condicional y gráficas

## Estructura canónica del `.docx`

| Sección | Contenido | Regla |
|---|---|---|
| **Portada** | Tabla de metadatos + «Cómo leer este documento» + definición del objeto | El objeto de estudio se define acá, en una frase, antes de todo |
| **1. Qué se hizo** | Método, embudo, cobertura, límites, rendimiento por keyword | La cobertura va **antes** que cualquier proporción |
| **2. Lo que se midió** | Solo conteos y proporciones | Ni una interpretación |
| **3. Lectura** | Interpretación, anclada al número que la sostiene | Anuncia que es interpretación en su primera línea |
| **Anexo** | Trinos ilustrativos por encuadre | "Ejemplos del lenguaje que circula, no los más representativos" |

Además, siempre: `base_analisis.csv` junto al `.docx`.

### La portada define el objeto

```
Qué se entiende acá por espacio cívico
La capacidad de las organizaciones y la ciudadanía de expresarse, reunirse, asociarse e
incidir en lo público sin miedo. El objeto observado no son las organizaciones ni si tienen
razón: es el estado del espacio en el que operan.
```

Esa frase —qué **no** es el objeto— es la que evita que el informe derive a evaluar a las
organizaciones en vez del entorno. Escribila antes de escribir el resto.

### El embudo: de lo capturado a la base de análisis

| Etapa | Trinos | % del capturado |
|---|---|---|
| Trinos únicos capturados | 10.000 | 100% |
| Relevantes al tema | … | … |
| Conversación colombiana | … | … |
| Base de análisis (confianza ≥ 0,5) | … | … |

Debajo, en cursiva, **por qué se cayó cada escalón**: cuántos relevantes eran de otros países,
y que el país se determinó por contenido y no por la `location` del perfil.

### Límites: cinco bullets fijos

Muestra ≠ censo (hay tope por keyword × mes, los volúmenes son orden de magnitud);
X no es representativo de la opinión pública; la clasificación automática tiene margen de
decenas de casos y sirve para proporciones y contrastes, no para cifras exactas; el tema se
juega también donde no hay registro digital; una comparación antes/después contrasta
períodos de distinta duración y carga noticiosa — sirve para ver cambios de composición,
no para atribuir causas.

## Un eje que ordena toda la lectura

Cada escucha necesita **un eje** que agrupe las categorías en dos familias que signifiquen
algo distinto. No es decoración: es lo que convierte 12 encuadres en un hallazgo.

| Proyecto | Eje |
|---|---|
| Espacio cívico | **Espacio en uso** (ejerce, agenda, convoca) vs. **espacio en disputa** (denuncia, estigmatización, riesgo, marco legal, financiación) |
| Movilidad eléctrica | **Dos conversaciones que no se tocan** (la del ahorro vs. la del ambiente) |

En código son dos listas de constantes (`ENC_USO`, `ENC_DISPUTA`) que se usan tres veces:
para la gráfica de encuadres, para la comparación antes/después y para el primer párrafo de
la lectura.

## Prosa condicional al dato

El párrafo se elige según el número. Patrón real de `sec_lectura()`:

```python
if n_uso > n_disp:
    p(doc, f"Predomina el espacio en uso: {pct(n_uso, n)} …")
elif n_disp > n_uso:
    p(doc, f"Predomina la disputa: {pct(n_disp, n)} …", bold=True)   # negrita: es la señal preocupante
else:
    p(doc, f"Uso y disputa quedan parejos ({pct(n_uso, n)} y {pct(n_disp, n)}).")
```

Tres ramas para estigmatización —`den > est*2` (la alarma domina al ataque), `est > 0`
(hay ataque, hay que desglosarlo), `est == 0` (no hay: sospechá del instrumento)— y un
umbral que cambia la frase entera en efecto inhibitorio:

```python
("Es el indicador más importante y el más difícil de capturar en redes: el miedo rara vez
  se publica. Su ausencia en X no es evidencia de que no exista; es evidencia de que esta
  metodología no lo alcanza y de que hay que buscarlo con entrevistas."
 if inh / max(n, 1) < 0.05 else
 "Es una proporción alta para un indicador que normalmente no se publica, y merece revisión
  caso por caso antes de sostenerla.")
```

**Cada rama tiene que ser una afirmación distinta, no la misma frase con otro número.** Si
las tres ramas dicen lo mismo, el eje no estaba midiendo nada.

## Desglosar la cifra gruesa: el patrón

Una tabla con la jerarquía sangrada, y debajo el párrafo que dice cuál sostener (cifras
ilustrativas):

```
Ejercen lenguaje deslegitimador (total)              2.000   20,0%
   · de los cuales, dentro de la pelea partidista      800    8,0%
   · fuera de la pelea partidista                    1.200   12,0%
   · que además nombran una organización               100    1,0%
Denuncian o analizan estigmatización ajena             700    7,0%
Describen efecto inhibitorio consumado                  50    0,5%
```

> "La cifra gruesa (20%) mezcla dos cosas. 40% de esos trinos está encuadrado como
> disputa partidista: hostilidad contra una figura o un bando, donde quien se organiza queda
> de paso. El dato que sostiene una afirmación sobre espacio cívico es el otro: 12,0% de la
> base deslegitima a quien se organiza fuera de esa trinchera."

Y el cierre que lo vuelve accionable: "lo primero se combate cambiando el clima político,
que no está al alcance de una organización; lo segundo, disputando el sentido de lo que
significa organizarse, que sí lo está."

## Comparación antes/después de una bisagra

Si el corpus cruza un hecho que parte la conversación (cambio de gobierno, una ley, un
escándalo), esa fecha es la bisagra analítica y se declara como constante:

```python
CAMBIO_GOBIERNO = date(2026, 8, 7)
```

Tres cuidados:

1. **Solo si hay volumen a ambos lados.** El umbral usado es `len(antes) >= 20 and
   len(despues) >= 20`; si no, el informe lo dice y deja la comparación pendiente.
2. **Comparar participaciones dentro de cada período, nunca volúmenes** — los períodos
   tienen distinta duración.
3. **El delta va en puntos porcentuales** (`{d - a:+.1f} pp`), no en "%", que se confunde con
   variación relativa.

## Helpers de python-docx (`templates/docx_helpers.py`)

`num()` merece una nota: miles con punto, como se escribe en Colombia. Está aislado en su
propio helper **porque aplicar `.replace(",", ".")` sobre una frase entera se come las comas
de la prosa.**

`figura()` inserta un PNG con pie en gris a 8 pt. Las gráficas **acompañan a la tabla, no la
reemplazan**: todo lo graficado está también tabulado, porque el cliente audita sobre la
tabla.

`multi_counter()` cuenta columnas multi-etiqueta (`"a, b, c"`). Cuando se usa, el pie de la
gráfica debe advertir que **la suma supera el total de la base**.

## Anexo

Por encuadre, los 3 trinos con más engagement (`sort_values(["likes","retweets"])`), texto
recortado a 280 caracteres, cita entre comillas angulares, y debajo `@autor · N likes ·
N retrinos` en gris 8 pt. Grupos con menos de 2 trinos se saltan.

El encabezado dice que son **ejemplos del lenguaje que circula, no los más representativos
en sentido estadístico**, y que es contenido público citado textualmente.

## Gráficas (`templates/charts.py`)

Paleta validada con el validador de la skill `dataviz` en modo light: azul `#2a78d6` y rojo
`#e34948` como par divergente (CVD ΔE 21.6, visión normal ΔE 32.3). PNG a **300 dpi** para
incrustar en el `.docx`.

Reglas que se respetan: marcas delgadas, ejes y grilla recesivos, etiquetas directas
selectivas, texto en tinta y **nunca** en el color de la serie, leyenda siempre que haya dos
series, ningún eje doble, y **una sola serie usa un solo tono** — nunca ciclar color por barra.

Las seis figuras de la escucha de espacio cívico: volumen mensual (con línea punteada en la bisagra), encuadre
uso/disputa, libertades, postura por actor, restrictores, antes/después.

## Gotcha de pandas

```python
fechas.dt.tz_localize(None).dt.to_period("M")
```

`.to_period()` descarta la zona horaria y emite un warning. Como todo está en UTC, se quita
antes explícitamente.
