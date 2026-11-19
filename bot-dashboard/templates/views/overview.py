"""Página Inicio — KPIs + actividad diaria. Ejemplo de cableado página↔db↔componentes."""

import streamlit as st

from utils import db
from utils.styles import page_header
from components.filters import get_filters
from components import kpi_row, charts

page_header("Inicio", "Actividad general del bot")

f = get_filters()


# El param 'cache_day' (fecha de hoy en Bogotá) hace que el cache se invalide al
# cambiar de día. Sin guion bajo: los args con guion bajo Streamlit NO los hashea.
@st.cache_data(ttl=600)
def _kpis(date_from, date_to, cache_day):
    return db.get_kpis(date_from, date_to)


@st.cache_data(ttl=600)
def _daily(date_from, date_to, cache_day):
    return db.get_daily_activity(date_from, date_to)


today = db.today_bogota()
k = _kpis(f["date_from"], f["date_to"], today)
daily = _daily(f["date_from"], f["date_to"], today)

kpi_row.render([
    {"label": "Usuarios", "value": int(k["n_users"]), "accent": "accent",
     "caption": "Personas que interactuaron con el bot"},
    {"label": "Sesiones", "value": int(k["n_sessions"]), "accent": "navy"},
    {"label": "Mensajes", "value": int(k["n_messages"]), "accent": "yellow"},
])

st.markdown("#### Actividad diaria")
if daily.empty:
    st.info("Sin datos en el período seleccionado.")
else:
    fig = charts.line_timeseries(daily, "day", "messages", f["date_from"], f["date_to_incl"])
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
