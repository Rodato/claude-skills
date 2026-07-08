"""Fábrica Plotly centralizada — todas las gráficas salen de acá.
Regla de oro: go.* con .tolist(), NUNCA px.* (px lee el índice del DataFrame bajo cache)."""

import pandas as pd
import plotly.graph_objects as go

from utils.styles import COLORS


def _base_layout(height: int = 280, **kw) -> dict:
    layout = dict(
        paper_bgcolor=COLORS["bg_card"],
        plot_bgcolor=COLORS["bg_card"],
        font=dict(family="Open Sans, sans-serif", size=11, color=COLORS["text"]),
        margin=dict(l=8, r=8, t=14, b=8),
        height=height,
        xaxis=dict(gridcolor="#F3F4F6", linecolor=COLORS["border"], title=None),
        yaxis=dict(gridcolor="#F3F4F6", linecolor=COLORS["border"], title=None),
    )
    layout.update(kw)
    return layout


def bar_h(df: pd.DataFrame, x: str, y: str, color: str = None, height: int = 280) -> go.Figure:
    color = color or COLORS["accent"]
    fig = go.Figure(go.Bar(x=df[x].tolist(), y=df[y].tolist(), orientation="h", marker_color=color))
    fig.update_layout(**_base_layout(height=height, yaxis_categoryorder="total ascending"))
    return fig


def donut(df: pd.DataFrame, names: str, values: str, height: int = 280) -> go.Figure:
    palette = [COLORS["accent"], COLORS["yellow"], COLORS["red"], COLORS["green"], COLORS["navy"]]
    fig = go.Figure(go.Pie(labels=df[names].tolist(), values=df[values].tolist(),
                           hole=0.6, marker=dict(colors=palette)))
    fig.update_layout(**_base_layout(height=height))
    return fig


def line_timeseries(df: pd.DataFrame, day_col: str, value_col: str,
                    date_from, date_to, color: str = None, height: int = 280) -> go.Figure:
    """Serie temporal robusta: rellena los días sin datos con 0 y fija el eje X al
    rango elegido (date_from..date_to, ambos inclusive). Así un rango con datos
    escasos no parece un filtro roto. Renderizar con config={'displayModeBar': False}."""
    color = color or COLORS["accent"]
    s = df.copy()
    s[day_col] = pd.to_datetime(s[day_col])
    idx = pd.date_range(date_from, date_to)
    s = s.set_index(day_col).reindex(idx, fill_value=0).rename_axis(day_col).reset_index()
    fig = go.Figure(go.Scatter(
        x=s[day_col].tolist(), y=s[value_col].tolist(),
        mode="lines", fill="tozeroy", line=dict(color=color, width=2),
    ))
    fig.update_layout(**_base_layout(height=height))
    fig.update_xaxes(range=[date_from, date_to], fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig
