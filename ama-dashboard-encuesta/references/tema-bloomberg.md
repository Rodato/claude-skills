# Tema Bloomberg — `theme.py`

Estilo visual **Bloomberg Terminal**: fondo negro `#080808`, acento amber `#FFB300`, IBM Plex
Mono. `theme.py` es el canon — viene de `~/Documents/Dev/AMA/Bot_monitoring/src/app.py`. Si toca
expandir el theme, **reusar de ahí**, no reinventar. Es la misma piel que puede usar `bot-dashboard`.

Expone tres cosas: `inject_css()`, `base_layout(**kwargs)` y `html_table(...)`, más las constantes
de color.

## Paleta

```python
AMBER = "#FFB300"   # acento principal (títulos, KPIs, top-3)
CYAN  = "#00D4FF"   # series secundarias (ritmo diario)
GREEN = "#00C853"   # completitud alta / sí
RED   = "#FF1744"   # completitud baja / no
ORANGE = "#FF6D00"
PURPLE = "#AA00FF"
CHART_COLORS = [AMBER, CYAN, GREEN, RED, ORANGE, PURPLE]
FONT = dict(family="IBM Plex Mono, Courier New, monospace", color="#888888", size=11)
```

Umbrales de color usados en las vistas (mantener consistentes):
- **Completitud por pregunta**: `RED <50%`, `AMBER <90%`, `GREEN ≥90%`.
- **Cobertura por colegio**: `RED <30%`, `AMBER 30–70%`, `GREEN ≥70%`.

## `inject_css()` — se llama una vez, arriba de `app.py`

Inyecta `_CSS` (un `<style>` grande) con `st.markdown(..., unsafe_allow_html=True)`. Fuerza IBM
Plex Mono global, fondo negro, y estiliza sidebar, `h1/h2/h3`, `[data-testid="metric-container"]`
(con borde-izquierdo amber), tabs, progress bar y scrollbar fino.

## `base_layout(**kwargs)` — layout base de Plotly

**Toda** figura arranca de acá; los `kwargs` sobrescriben lo que haga falta. Fija paper/plot
bg `#0D0D0D`, la fuente, grids `#151515`, ejes con `linecolor #1E1E1E`, leyenda transparente y
hoverlabel oscuro con texto amber:

```python
def base_layout(**kwargs) -> dict:
    base = dict(
        paper_bgcolor="#0D0D0D", plot_bgcolor="#0D0D0D", font=FONT,
        xaxis=dict(showgrid=True, gridcolor="#151515", zeroline=False,
                   tickfont=FONT, linecolor="#1E1E1E", linewidth=1),
        yaxis=dict(showgrid=True, gridcolor="#151515", zeroline=False,
                   tickfont=FONT, linecolor="#1E1E1E", linewidth=1),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1E1E1E", borderwidth=1, ...),
        margin=dict(l=0, r=0, t=30, b=0),
        hoverlabel=dict(bgcolor="#111111", bordercolor="#333333",
                        font=dict(family="IBM Plex Mono, monospace", color="#FFB300", size=11)),
    )
    base.update(kwargs)
    return base
```

Uso típico (barras h con la altura calculada según el nº de filas):

```python
fig.update_layout(**base_layout(
    yaxis=dict(categoryorder="total ascending", showgrid=False, ...),
    xaxis=dict(showgrid=False, ...),
    height=max(220, 40 * len(by_col) + 60),
    margin=dict(l=0, r=40, t=10, b=0),
))
st.plotly_chart(fig, use_container_width=True)
```

## `html_table(df, col_defs, medal_col=None, max_height=None)` — tablas estilo terminal

Renderiza un DataFrame como tabla HTML Bloomberg. `col_defs` es una lista de `(attr, header, align)`.
`medal_col` tinta amber la columna dada para el top-3; `max_height` la mete en un contenedor
scrolleable con header **sticky** en vez de estirar la página.

```python
st.markdown(
    html_table(
        rank_df,
        col_defs=[("dim", "COLEGIO", "left"), ("respuestas", "RESPUESTAS", "right"),
                  ("hoy", "HOY", "right"), ("primera", "PRIMERA", "right"),
                  ("ultima", "ÚLTIMA", "right")],
        medal_col=1, max_height=360,
    ),
    unsafe_allow_html=True,
)
```

El `#` de ranking sale con medalla: `1→AMBER`, `2→gris`, `3→#5A4000`; del 4 en adelante `#444`.

## Gotcha 1 — iconos Material salen como texto

El override monospace global (`html, body, [class*="css"] { font-family: ... !important }`) **pisa
la fuente de los iconos Material Symbols de Streamlit** y los muestra como texto (p. ej. la flecha
de colapsar el sidebar aparecía como `keyboard_double_arrow_left`). Hay una regla **al final** de
`_CSS` que restaura la fuente de los iconos:

```css
.stApp [data-testid="stIconMaterial"],
span.material-symbols-rounded,
span.material-symbols-outlined {
    font-family: 'Material Symbols Rounded', 'Material Symbols Outlined' !important;
}
```

Si agregás widgets nuevos cuyos iconos salgan como texto, **amplía ese selector** (no toques el
override global).

## Gotcha 2 — tablas/charts largos van en contenedores scrolleables

Nunca dejar que una tabla o un chart de altura variable estire la página. Dos herramientas:

- **Tablas**: `html_table(..., max_height=360)` → div scrolleable con header sticky.
- **Charts Plotly altos** (p. ej. completitud con ~108 preguntas): envolver en
  `with st.container(height=520): st.plotly_chart(fig, use_container_width=True)`.

Mantené este patrón si agregás tablas/charts que crezcan con los datos.

## Gotcha 3 — `use_container_width` deprecado

Streamlit (≥1.57) avisa que `use_container_width=True` se reemplaza por `width='stretch'`
(deadline ya pasó: 2025-12-31). Hoy son solo warnings, no rompe. Migrar los
`st.plotly_chart(..., use_container_width=True)` cuando toque limpiar.
