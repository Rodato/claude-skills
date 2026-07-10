---
name: ama-graficas-informe
description: >-
  Estilo canónico de gráficas del informe del programa AMA: barras horizontales
  por género con una paleta fija (Hombre azul / Mujer coral / No binaria púrpura /
  Prefiero no decir gris), % dentro de cada género, exportadas a 300 dpi + PDF.
  Usala cuando tengas que crear, replicar o extender gráficas de encuesta AMA —
  línea base (Iquitos/Lago Agrio), el tablero (Cobija/Leticia) o el endline — para
  que el look, la paleta y las reglas de forma no se reinventen en cada informe.
---

# AMA — gráficas del informe

Estilo visual **compartido** entre tres frentes del programa AMA. Toda gráfica de
distribución de respuestas de encuesta sale de esta misma receta: **barras
horizontales agrupadas por respuesta, una barra por género, porcentaje calculado
dentro de cada género, 300 dpi**. Se reusa sin cambios entre línea base, tablero y
endline: si vas a graficar resultados de la encuesta AMA, replicá esto, no inventes.

## Implementaciones de referencia (leé el código real antes de inventar)

| Frente | Archivo | Qué aporta |
|---|---|---|
| Línea base Iquitos/Lago Agrio | `Preprocesamiento/src/generar_graficas_informe.py` | Generador canónico: 30 PNG (P31-P46) + PDF consolidado. La `crear_grafica()` es el patrón madre. |
| Demográficas | `Preprocesamiento/src/graficas_demograficas_informe.py` | Sexo/etnia/riqueza. **Excepciones** al estilo (barras verticales, gradiente por ciudad). |
| Bot por ciudad | `Preprocesamiento/src/graficas_bot_informe.py` | Misma paleta pero eje = ciudad (Iquitos azul / Lago Agrio coral). |
| Tablas fuente | `Preprocesamiento/src/variables_encuesta_informe.py` | Cómo se derivan las distribuciones por sexo desde el dataset unificado. |
| Tablero Streamlit | `Lineabase2026/tablero/lib.py` | **El mismo estilo** dentro de Streamlit + registro dinámico de variables desde el diccionario. |
| Catálogo de tipos | `Lineabase2026/tablero/bot.py` | `_fig_si_no`, `_fig_likert`, `_fig_multi`, `_fig_ordinal`, `_fig_frecuencia`, dispatcher `_pregunta`. |

Ambos repos tienen `CLAUDE.md` con el detalle de cada frente — **leelo primero** cuando trabajes sobre uno.

## La paleta fija (nunca hardcodear otro hex)

```python
COLORES = {
    "Hombre": "#6cd2ff",              # azul claro
    "Mujer": "#fc684f",               # coral
    "Persona no binaria": "#9b59b6",  # púrpura
    "Prefiero no decir": "#95a5a6",   # gris
}
ORDEN_SEXOS = ["Hombre", "Mujer", "Persona no binaria", "Prefiero no decir"]
```

El **azul `#6cd2ff`** (color de "Hombre") es también el acento AMA: el bot lo usa
como color de barra (`ACENTO`) en vez del teal del tablero. Ver `scripts/paleta.py`
para el dict + un helper `barh_por_genero(...)` reutilizable.

## Reglas de forma (no negociables — detalle en `references/estilo-y-paleta.md`)

- **Barras horizontales** (`ax.barh`) agrupadas por respuesta; una barra por género; `ax.invert_yaxis()` para que la 1ª respuesta quede arriba.
- **% dentro de cada género** (suma 100% por género), no sobre el total. En multi-respuesta el % es sobre el total de menciones de ese género.
- **Solo se dibujan los géneros con datos** en esa variable (`bar_height`/offsets se ajustan a 1/2/3/4 barras). En línea base 25/30 variables tienen No binaria; P31/P32 solo 2 barras.
- **Etiquetas truncadas** a ~45 chars con `"..."`; **% al lado** de cada barra (`f"{val:.1f}%"`, color `#333333`).
- Grid X punteado `alpha=0.3`, `set_axisbelow(True)`, `figsize=(10, altura_dinámica)`.
- **Export: PNG a 300 dpi** (`facecolor="white"`, `bbox_inches="tight"`) + **PDF consolidado** con `PdfPages`. En Streamlit: display 130 dpi, descarga 300 dpi.

## De dónde salen las variables

Las variables graficables se derivan **dinámicamente del `diccionario_datos.csv`**
(columna `codigo_variable`, `seccion`), excluyendo identificadores y texto libre —
esto lo hace `registro_variables()` en `lib.py` (el tablero, ~83 vars). Códigos por
sección: DEM, PHQ, GAD, INF, REL, SUS, ACT, COM, NOR, ALC. La distribución por sexo
se calcula con `groupby(['DEM_11', variable])` y `%` sobre el total por sexo
(`variables_encuesta_informe.py`).

⚠ **Ojo:** `generar_graficas_informe.py` (Preprocesamiento) **NO** deriva del
diccionario — lee CSVs P31-P46 ya pre-computados vía un dict `ARCHIVOS_CONFIG`
hardcodeado. La derivación dinámica es del **tablero**. Para el endline, seguí el
patrón del tablero (`registro_variables`).

## Multi-respuesta (dos dialectos según la fuente)

Algunas variables traen varias opciones en una celda y hay que **descomponerlas antes
de contar** (% sobre menciones):
- **Iquitos/Lago Agrio** (`generar_graficas_informe.py`): separadas por **coma** → P31, P32, P36, P39.
- **Cobija/Leticia** (`lib.py`): concatenadas por **espacios** desde Kobo → segmentación greedy por coincidencia más larga contra las etiquetas del form XML (ACT_04, REL_09, REL_10, COM_02, INF_01/02/04, NOR_08/09).

La lógica de parseo (comas vs espacios, greedy longest-match, de dónde vienen los
datos de Kobo) vive en la skill hermana **`ama-kobo`** — no la repitas acá, enlazala.

## Cómo trabajar

- **Replicar el estilo en un frente nuevo (endline):** copiá `crear_grafica()` de `lib.py` (la versión más general: soporta 1-4 géneros y nota al pie) o usá `scripts/paleta.py`. Derivá las variables con `registro_variables()`. Exportá con `figura_a_png(fig, dpi=300)`.
- **Extender el tablero Streamlit:** leé `references/tipos-de-grafica.md` para elegir el `_fig_*` correcto y `references/embed-streamlit.md` para el embebido base64 (gotcha crítico de `st.pyplot`).
- **Antes de graficar:** repasá `references/estilo-y-paleta.md`. Casi toda decisión de forma está ahí.

## Reglas no negociables

- **Colores desde el dict `COLORES`**, nunca un hex suelto. `COLORES.get(sexo, "#888888")` como fallback.
- **NaN de pandas es truthy** → chequear strings con `isinstance(v, str)` / `pd.notna`, nunca `if v`.
- **PII:** nunca graficar filas individuales de menores — **solo agregados por género**. Ver skill hermana **`ama-pii`**.
- **`python3`**; comentarios en español, código en inglés.

## References y scripts

- `references/estilo-y-paleta.md` — paleta exacta, forma de barras, truncado, %, géneros dinámicos, altura dinámica, export 300 dpi + PDF, diferencias exactas entre el generador y el tablero.
- `references/tipos-de-grafica.md` — catálogo de `_fig_*` del bot (si/no, likert apilado 100%, likert único, multi, ordinal, frecuencia) con cuándo usar cada uno + las excepciones demográficas (verticales, gradiente).
- `references/embed-streamlit.md` — el gotcha de `st.pyplot` + patrón PNG base64 en `.chart-card` + display 130 / descarga 300 dpi.
- `scripts/paleta.py` — `COLORES` + `barh_por_genero(dist, titulo)` mínimo reutilizable + `figura_a_png`.

## Skills hermanas

- **`ama-kobo`** — de dónde vienen los datos y cómo se parsean (multi-respuesta por espacios / greedy, formularios Kobo).
- **`ama-pii`** — nunca graficar filas individuales de menores; solo agregados; anonimizar antes de deploy.
- **`ama-dashboard-encuesta`** — el tablero Streamlit completo (auth, tabs, UI) que envuelve estas gráficas.
- **`ama-excel`** — tablas/Excel consolidados que acompañan a las gráficas del informe.
