# Gráficas, KPIs y estilo

## Regla de oro: `go.*`, nunca `px.*` bajo cache

Con `@st.cache_data`, `px.pie` / `px.bar` leen el **índice** del DataFrame en vez de los valores
reales y muestran datos equivocados. Usar siempre `plotly.graph_objects` con `.tolist()` explícito:
```python
import plotly.graph_objects as go
fig = go.Figure(go.Bar(x=df["label"].tolist(), y=df["value"].tolist()))
```
(aly-dashboard usa `px` dentro de la fábrica pero **sin cache en la fábrica**; si cacheás datos
aguas arriba, `go.*` es lo seguro. Ante la duda, `go.*`.)

## Fábrica de gráficas centralizada

Todas las gráficas salen de una fábrica (`components/charts.py` o helpers en `app.py`) que aplica
un layout base común. Ninguna página estiliza a mano.

```python
from utils.styles import COLORS

_BASE = dict(
    paper_bgcolor=COLORS["bg_card"], plot_bgcolor=COLORS["bg_card"],
    font=dict(family="Open Sans, sans-serif", size=11, color=COLORS["text"]),
    margin=dict(l=8, r=8, t=14, b=8),
    hoverlabel=dict(bgcolor=COLORS["bg_card"], bordercolor=COLORS["border"]),
)

def _layout(title="", **kw):
    base = {**_BASE, "xaxis": {...}, "yaxis": {...}}
    if title: base["title"] = dict(text=title, x=0.01, xanchor="left")
    base.update(kw)
    return base

def bar_h(df, x, y, title="", color=None, height=280) -> go.Figure: ...
def donut(df, names, values, title="", height=280) -> go.Figure: ...
def choropleth_colombia(df, ...) -> go.Figure: ...   # geojson local en data/
```

**Gotcha del layout base (AMA):** no incluir `title_x=0` si no hay título — Plotly renderiza
el texto literal `"undefined"`.

## Series temporales — rellenar días faltantes

Las queries devuelven solo días **con** datos. Si el usuario filtra un rango y hay huecos, el
gráfico parece un filtro roto. Patrón obligatorio:
```python
idx = pd.date_range(date_from, date_to)
df = df.set_index("day").reindex(idx, fill_value=0).rename_axis("day").reset_index()
fig.update_xaxes(range=[date_from, date_to], fixedrange=True)   # fija eje + desactiva zoom
# y renderizar con config={"displayModeBar": False}
```
Si hay muchos menos días con datos que el span, mostrar una nota tipo "datos escasos".

## KPI cards

Cards HTML custom (no `st.metric` salvo en la piel dark de AMA). Cada card = accent bar + icono
line + valor + sparkline SVG inline + delta pill. `render(metrics: list[dict])`, cada dict:
- `label`, `value`, `delta` (fracción vs período anterior o `None`), `prefix`/`suffix`
- `accent`: key de `COLORS` (`accent|navy|positive|yellow|red`) — pinta barra y dots
- `icon`: key de un dict `ICONS` de SVGs (`users`, `message`, `send`, `chart`, `alert-*`, `flag`, `activity`)
- `spark`: lista de valores para el sparkline (opcional)
- `caption`: oración corta autoexplicativa bajo el valor (opcional)

Los deltas vienen de una query dedicada (`get_kpi_deltas`) que compara contra el período anterior
del mismo tamaño.

## Estilo: dict COLORS + CSS inyectado

- **Nunca hex hardcodeado.** Todo color sale de un dict `COLORS` en `styles.py`
  (`accent`, `navy`, `bg_app`, `bg_card`, `text`, `text_secondary`, `border`, `positive`, `red`, `yellow`).
- CSS global se inyecta **una vez** con `st.html(css)` en `inject()`. El HTML de los componentes
  usa `st.markdown(..., unsafe_allow_html=True)`.
- Fuentes vía Google Fonts (`@import` en el CSS).

### Las dos pieles (elegí una al arrancar)

**A. Claro premium (aly-dashboard)** — dashboards "de producto", para mostrar a clientes/CEOs:
- Fondo app `#F7F8FA`, cards blancas, sidebar claro con logo.
- Oswald (títulos/valores/KPI) · Open Sans (body) · Material Symbols (nav).
- Accent `#0273e5`, navy `#110079`, amarillo `#FFCF24`, naranja `#F15B22`, verde `#22C55E`.
- Heatmap tipo GitHub contributions (`xgap=3, ygap=3`), choropleth con silueta plana.

**B. Bloomberg dark terminal (AMA)** — dashboards operativos internos, sensación "financial terminal":
- Fondo `#080808`, paneles `#0D0D0D`, todo `UPPERCASE` con `letter-spacing`.
- IBM Plex Mono en todo. Amber `#FFB300` (KPI/títulos/barras), cyan `#00D4FF` (series secundarias),
  texto `#C8C8C8` / secundario `#888`.
- `st.metric` restyleado por CSS (`border-left: 3px solid #FFB300`), tablas HTML con medallas
  gold/silver/bronze en el top 3 y cabecera sticky para leaderboards con scroll.

Mantené la piel elegida en cualquier ajuste futuro — no mezclar.
