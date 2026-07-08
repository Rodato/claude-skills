"""Sidebar con filtros de fecha globales + presets. get_filters() para las páginas.
Estado global en st.session_state (filter_from / filter_to)."""

from datetime import timedelta

import streamlit as st

from utils.db import today_bogota


def _init_state():
    if "filter_to" not in st.session_state:
        st.session_state.filter_to = today_bogota()
    if "filter_from" not in st.session_state:
        st.session_state.filter_from = today_bogota() - timedelta(days=29)


def _preset(days: int):
    # Presets que mutan widget keys: SIEMPRE via on_click callback. Asignar a
    # st.session_state[key] después de renderizar el widget se ignora en silencio.
    def _cb():
        st.session_state.filter_to = today_bogota()
        st.session_state.filter_from = today_bogota() - timedelta(days=days - 1)
    return _cb


def render_sidebar():
    _init_state()
    with st.sidebar:
        st.markdown("### 🤖 Bot Monitor")
        st.caption("Panel de seguimiento")
        st.divider()
        st.markdown("**Período**")
        c1, c2 = st.columns(2)
        c1.button("7d", on_click=_preset(7), use_container_width=True)
        c2.button("30d", on_click=_preset(30), use_container_width=True)
        # key= sin value=: el valor inicial vive en session_state (evita el warning de Streamlit).
        st.date_input("Desde", key="filter_from")
        st.date_input("Hasta", key="filter_to")


def get_filters() -> dict:
    """date_to es EXCLUSIVO (para SQL); date_to_incl es el día elegido (para el eje X)."""
    _init_state()
    return {
        "date_from": st.session_state.filter_from,
        "date_to": st.session_state.filter_to + timedelta(days=1),
        "date_to_incl": st.session_state.filter_to,
    }
