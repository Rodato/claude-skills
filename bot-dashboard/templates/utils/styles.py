"""Estilo global — dict COLORS + inyección de CSS. Piel: claro premium.
Nunca hardcodear hex en las páginas: todo color sale de COLORS."""

import streamlit as st

COLORS = {
    "accent": "#0273e5",
    "navy": "#110079",
    "yellow": "#FFCF24",
    "red": "#F15B22",
    "green": "#22C55E",
    "positive": "#22C55E",
    "bg_app": "#F7F8FA",
    "bg_card": "#FFFFFF",
    "text": "#111827",
    "text_secondary": "#6B7280",
    "border": "#E5E7EB",
}

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Open+Sans:wght@400;600&display=swap');

.stApp {{ background: {COLORS['bg_app']}; }}
html, body, [class*="css"] {{ font-family: 'Open Sans', sans-serif; color: {COLORS['text']}; }}
h1, h2, h3, h4 {{ font-family: 'Oswald', sans-serif; color: {COLORS['text']}; letter-spacing: .01em; }}
[data-testid="stSidebar"] {{ background: {COLORS['bg_card']}; border-right: 1px solid {COLORS['border']}; }}

.page-header {{ margin-bottom: 1rem; }}
.page-header h1 {{ margin: 0; font-size: 1.7rem; }}
.page-header .subtitle {{ color: {COLORS['text_secondary']}; font-size: .9rem; }}
</style>
"""


def inject():
    """Inyecta el CSS global. Llamar una sola vez, en app.py, antes de renderizar nada."""
    st.html(_CSS)


def page_header(title: str, subtitle: str = ""):
    sub = f'<div class="subtitle">{subtitle}</div>' if subtitle else ""
    st.markdown(
        f'<div class="page-header"><h1>{title}</h1>{sub}</div>',
        unsafe_allow_html=True,
    )
