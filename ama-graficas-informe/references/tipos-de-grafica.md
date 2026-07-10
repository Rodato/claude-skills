# Catálogo de tipos de gráfica

La gráfica por defecto del informe es la **barh por género** (ver
`estilo-y-paleta.md`). Pero el tablero del bot (`Lineabase2026/tablero/bot.py`)
resuelve otros tipos de pregunta con funciones `_fig_*` dedicadas, todas en el mismo
estilo claro. El dispatcher `_pregunta(df, key) -> (figura, csv, slug)` elige cuál
usar según la pregunta. Este catálogo es lo que reusás cuando una variable no es una
distribución simple por género.

Colores comunes en `bot.py`:

```python
ACENTO = "#6cd2ff"   # azul AMA (barras de conteo genéricas)
VERDE  = "#1a9850"   # "bueno" (sí, recomienda)
ROJO   = "#d73027"   # "malo" (no, problemas)
GRIS   = "#95a5a6"
LIKERT_COLORES = ["#d73027", "#fc8d59", "#fee08b", "#91cf60", "#1a9850"]  # 1→5 rojo→verde
```

## `_fig_si_no(n_si, n_no, titulo, si_es_bueno=True)`
Pregunta binaria (¿usó el bot?, ¿recomienda?, ¿tuvo problemas?). Dos barras
horizontales, verde/rojo según `si_es_bueno` (para "¿tuvo problemas?" se invierte).
Etiqueta `f"{v}  ({pct:.0f}%)"`. Sin eje X, spines ocultos. **Usar** para sí/no simples.

## `_fig_ciudad(counts)`
Conteo por ciudad (una barra por ciudad, color `ACENTO`). **Usar** para "respuestas
por ciudad" y cualquier conteo simple de una categórica nominal.

## `_fig_likert(df)` — 5 escalas apiladas 100%
Barras horizontales **100% apiladas** (1→5) para varias afirmaciones Likert a la vez.
Cada afirmación es una barra; los 5 segmentos usan `LIKERT_COLORES`; etiqueta el % del
segmento si `>= 8`. El ytick muestra el promedio: `f"{label}  (prom {mean:.1f})"`.
Leyenda de las 5 categorías abajo (`ncol=5`). **Usar** para comparar el reparto de una
escala de acuerdo entre varias afirmaciones. No usa la paleta de género (usa la
diverging rojo→verde).

## `_fig_likert_one(s, label)`
Distribución 1–5 de **una sola** afirmación Likert. Cinco barras horizontales con
`LIKERT_COLORES`, título con promedio y n: `f"{label} · promedio {prom:.1f}/5 (n={len(s)})"`.
**Usar** cuando el usuario quiere ver una afirmación en detalle.

## `_fig_barh(labels, values, titulo, color=ACENTO, pct_base=None, nota=None)`
Barh **genérica** (una barra por categoría). El resto de los `_fig_*` de conteo la
llaman por dentro. `pct_base` fija el denominador del %; `nota` va como xlabel gris en
cursiva. **Usar** como primitiva para cualquier ranking de categorías.

## `_fig_multi(s, labelmap, titulo)` — opción múltiple
Descompone un `select_multiple` (códigos separados por **espacio**) vía `_multi_counts`,
cuenta menciones por etiqueta y grafica ordenado desc. **% sobre encuestados que
respondieron** (no sobre menciones), con nota `"% sobre {resp} que respondieron ·
pueden marcar varias"`. Devuelve `(fig, csv)`. **Usar** para preguntas de marcar
varias. (Nota: aquí el denominador es distinto al de la barh por género multi-respuesta
del informe, que reparte 100% sobre menciones — elegí según lo que la pregunta exija.)

## `_fig_ordinal(s, orden, titulo, nota=None)` — opción única con orden fijo
Opción única con **orden semántico** dado por una lista `[(codigo, etiqueta), ...]`.
Cuenta con `value_counts()` respetando ese orden y **descarta códigos basura** (los que
no están en `orden`). % sobre el total válido. **Usar** para escalas ordinales de
opción única (tiempo por sesión, forma de conversación, tiempo de internet).

## `_fig_frecuencia(s, titulo)` — entero en bins
Convierte un entero a bins fijos (`0`, `1–2`, `3–5`, `6 o más`), **descartando
outliers** (`where(x.between(0, 40))`). Nota con n y promedio. **Usar** para conteos
tipo "¿cuántas veces usaste el bot?".

## Dispatcher `_pregunta(df, key)`
Traduce la key del selector a la `_fig_*` correcta y devuelve `(figura, csv_df, slug)`.
El `slug` nombra los archivos de descarga. Los mapas código→etiqueta
(`RAZONES_NO_USO`, `PROBLEMAS_TIPOS`, `TIEMPO_SESION`, `FORMA_CONV`, `TIEMPO_INTERNET`,
`TEMAS_FUTUROS`) están al inicio del módulo; los códigos que no figuran en el mapa se
descartan solos. Al agregar una pregunta: mapa nuevo → rama en `_pregunta` → entrada en
`PREGUNTAS`.

⚠ **Gotcha de datos:** `_Cu_nto_tiempo_naveg_al_d_a_por_internet` tiene los labels de
Kobo **editados y desalineados** de los códigos. Se lee por **código** (`TIEMPO_INTERNET`)
y la gráfica lleva aviso; verificar rangos con campo antes de usar en informe.

## Excepciones demográficas (NO son barh por género)

`Preprocesamiento/src/graficas_demograficas_informe.py` se sale del molde canónico:

- **Sexo por ciudad** (`grafica_sexo_por_ciudad`): barras **verticales** agrupadas
  (`ax.bar`), eje X = ciudad, una barra por sexo (usa la paleta de género), etiqueta
  solo `%`. Spines top/right ocultos. Grupo **Tratamiento** (no Control).
- **Etnia** (`grafica_etnia_por_ciudad`): barh pero con **gradiente por ciudad** — azul
  `plt.cm.Blues` para Iquitos, naranja `plt.cm.Oranges` para Lago Agrio — **no** la
  paleta de género (la categoría es etnia, no sexo).
- **Riqueza** (`grafica_riqueza_por_ciudad`): barras verticales, eje X = escalón 1-9,
  solo Hombre/Mujer (los demás con n muy chico).

Y `graficas_bot_informe.py`: misma paleta pero el **eje es la ciudad** (Iquitos
`#6cd2ff` / Lago Agrio `#fc684f`), no el género — porque el dataset del bot no tiene
sexo. Barras verticales, % en el eje Y.

**Regla:** la paleta `COLORES` es por **género**. Cuando el desglose es por ciudad se
reusan los mismos hex (azul/coral) pero como identidad de ciudad; cuando es por una
categórica sin orden (etnia) se usa un gradiente secuencial, no la paleta.
