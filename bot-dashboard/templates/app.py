"""Bot dashboard — entry point.  Correr:  python3 -m streamlit run app.py"""

import streamlit as st
from dotenv import load_dotenv

from utils.styles import inject as inject_styles
from components.filters import render_sidebar

load_dotenv()

st.set_page_config(
    page_title="Bot Monitor",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()  # CSS global, una sola vez, antes de renderizar nada

# Multipágina: agregá una st.Page por vista. La nav nativa aparece en el sidebar.
pages = [
    st.Page("pages/overview.py", title="Inicio", icon="📊"),
    # st.Page("pages/usuarios.py", title="Usuarios", icon="👥"),
    # st.Page("pages/alertas.py", title="Alertas", icon="🚨"),
]

pg = st.navigation(pages)
render_sidebar()  # logo + filtros, en todas las páginas
pg.run()
