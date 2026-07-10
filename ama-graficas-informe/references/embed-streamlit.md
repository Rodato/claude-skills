# Embeber la gráfica en Streamlit

Cómo se muestran estas gráficas matplotlib dentro del tablero
(`Lineabase2026/tablero/`) sin que se rompan, y cómo se ofrecen para descarga a
300 dpi. Aplica a las dos pestañas (Línea base y Encuesta del bot).

## Gotcha CRÍTICO: `st.pyplot` colapsa el ancho a ~16 px

`st.pyplot(fig)` usa `st.image` por dentro. **Dentro de un contenedor con borde**
(`st.container(border=True)`, o cualquier tarjeta con borde) el ancho de la imagen se
**colapsa a ~16 px** — la gráfica sale como una tira ilegible. No es un bug de tamaño de
figura; es la interacción `st.image` ↔ contenedor con borde.

**Solución (la que usa el tablero):** no usar `st.pyplot`. Renderizar la figura a **PNG
en memoria, codificarla en base64, e insertarla como `<img>`** dentro de una tarjeta
HTML propia (`.chart-card`) vía `st.markdown(..., unsafe_allow_html=True)`.

## Patrón: display base64 (130 dpi) + descarga (300 dpi)

De `bot.py` (idéntico en la pestaña de línea base):

```python
# Display embebido a 130 dpi (liviano para pantalla)
disp_b64 = base64.b64encode(lib.figura_a_png(fig, dpi=130)).decode()
st.markdown(
    f'<div class="chart-card"><img alt="{esc(sel)}" '
    f'src="data:image/png;base64,{disp_b64}"></div>',
    unsafe_allow_html=True,
)

# Descarga a 300 dpi (calidad informe)
png = lib.figura_a_png(fig, dpi=300)
plt.close(fig)   # cerrar SIEMPRE: evita acumular figuras entre reruns
st.download_button("⬇️  Gráfica PNG · 300 dpi", data=png,
                   file_name=f"{fname}.png", mime="image/png",
                   type="primary", width="stretch")
```

`figura_a_png` (en `lib.py`) es el único punto que serializa la figura:

```python
def figura_a_png(fig, dpi: int = 300) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    return buf.getvalue()
```

- **130 dpi** para la vista (rápida, suficiente en pantalla); **300 dpi** para el botón
  de descarga (misma calidad que los PNG del informe intermedio).
- Junto al PNG va un `download_button` con el **CSV** de esa pregunta (`csv_df.to_csv(index=False).encode("utf-8")`).
- `plt.close(fig)` es obligatorio: sin él, cada rerun de Streamlit deja figuras abiertas y se fuga memoria.

## Otros gotchas del tablero (heredados)

- **Backend Agg:** `matplotlib.use("Agg")` antes de importar `pyplot` (en `lib.py`), porque no hay GUI en el servidor.
- **NaN truthy:** `NaN` de pandas evalúa `True` en un `if`. Para chequear strings de celda usar `isinstance(v, str)` / `pd.notna`, nunca `if v`.
- **Likert sucio:** algunas columnas traen basura (`67`, `-7`); castear con `pd.to_numeric(...).where(lambda x: x.between(1, 5))`.
- **Orden de render de tabs:** el bloque `with tab_bot:` va **antes** que `with tab_base:` en el código, porque la pestaña de línea base hace `st.stop()` cuando no hay género/datos y `st.stop()` corta **todo** el script; renderizando el bot primero, ese stop no impide su dibujo. El orden visual lo fija la lista de `st.tabs`.

## PII

La app solo muestra **agregados por género/ciudad** — nunca filas individuales — y el
CSV de descarga también es agregado. Los datos versionados son solo los CSV
**anonimizados** (`encuesta_anon.csv`, `encuesta_bot.csv`). Ver skill hermana `ama-pii`
y el `CLAUDE.md` del tablero antes de tocar datos o desplegar.
