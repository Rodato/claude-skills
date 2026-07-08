"""KPI cards HTML custom: accent bar + valor + sparkline SVG + delta pill.
render(metrics: list[dict]). Cada dict: label, value, accent, delta, caption, spark, prefix, suffix."""

import html

import streamlit as st

from utils.styles import COLORS


def _sparkline(values, color, w: int = 120, h: int = 26) -> str:
    if not values or len(values) < 2:
        return ""
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1
    pts = []
    for i, v in enumerate(values):
        x = i / (len(values) - 1) * w
        y = h - (v - lo) / span * h
        pts.append(f"{x:.1f},{y:.1f}")
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" style="margin-top:6px;">'
            f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{" ".join(pts)}"/></svg>')


def _delta_pill(delta) -> str:
    if delta is None:
        return ""
    up = delta >= 0
    color = COLORS["positive"] if up else COLORS["red"]
    arrow = "▲" if up else "▼"
    return (f'<span style="color:{color};font-size:.75rem;font-weight:600;">'
            f'{arrow} {abs(delta) * 100:.0f}%</span>')


def render(metrics: list):
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        accent = COLORS.get(m.get("accent", "accent"), COLORS["accent"])
        value = f'{m.get("prefix", "")}{m["value"]}{m.get("suffix", "")}'
        caption = (
            f'<div style="color:{COLORS["text_secondary"]};font-size:.72rem;margin-top:2px;">'
            f'{html.escape(str(m["caption"]))}</div>' if m.get("caption") else ""
        )
        with col:
            st.markdown(
                f'''<div style="background:{COLORS['bg_card']};border:1px solid {COLORS['border']};
                    border-left:4px solid {accent};border-radius:8px;padding:14px 16px;">
                    <div style="color:{COLORS['text_secondary']};font-size:.72rem;text-transform:uppercase;
                        letter-spacing:.05em;">{html.escape(str(m["label"]))}</div>
                    <div style="display:flex;align-items:baseline;justify-content:space-between;gap:8px;">
                        <span style="font-family:'Oswald',sans-serif;font-size:1.9rem;font-weight:700;">{value}</span>
                        {_delta_pill(m.get("delta"))}
                    </div>
                    {_sparkline(m.get("spark"), accent)}
                    {caption}
                </div>''',
                unsafe_allow_html=True,
            )
