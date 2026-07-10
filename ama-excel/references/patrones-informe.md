# Catálogo de informes AMA — copiá el más parecido

14 scripts generan .xlsx en el proyecto. Buscá el que más se parezca a lo pedido y usalo de
plantilla: reusá sus hojas, su estilo y su bloque de notas. Rutas relativas a
`~/Documents/Dev/AMA/`.

## Línea base — Leticia / Cobija (`Lineabase2026/src/`)

| Script | Salida | Hojas | PII | Notas |
|---|---|---|---|---|
| `make_excel.py` | `data/reports/seguimiento_FECHAS.xlsx` | IDs incorrectos · Tiempos sospechosos · Diferencias Leticia · Diferencias Cobija | **Sí** | Semáforo **a)** (diferencia por signo + naranja name-match). Secciones Conteos + Faltantes con leyenda por emoji 🟡🟢🟠. |
| `diagnostico.py` | `data/reports/diagnostico_FECHA[_DESDE_HASTA].xlsx` | Totales ciudad · Totales colegio · Monitoreo | No | Volcado `df.to_excel`. `--report` añade `.md` LLM con el párrafo fijo "Cómo leer la columna Diferencia". |
| `datos_tecnicos.py` | `data/reports/datos_tecnicos_FECHA.xlsx` | Una hoja por ciudad (Cobija / Leticia) | **Sí** | Nombre, ID, Colegio, Grupo (Tratamiento/Control), Grado, Teléfono. Autoancho. |
| `listado_salones.py` | `data/reports/listado_salones_{ciudad}.xlsx` | Una hoja **por colegio** | **Sí** | Salón, Nombre, ID, Fecha. Nombres de hoja ≤ 31 y únicos (IE/ENS). |
| `consolidado_genero.py` | `data/reports/consolidado_genero_FECHA.xlsx` | Una hoja por ciudad | No | Colegio × género con subtotales por grupo y total ciudad; colores por grupo. |
| `build_excel.py` | `data/outputs/AMA_encuesta_unificada_4_ciudades.xlsx` | Diccionario · Datos | No | Volcado grande `df.to_excel`; autofit solo en Diccionario, freeze A2. |

## Línea de salida — Iquitos / Lago Agrio (`Lineasalida2026/lago-agrio/scripts/`)

Todos reusan el motor `lib/coverage.py` (mismo cruce que el dashboard) y escriben en
`outputs/` (gitignored). Estilo teal `1F4E5F`.

| Script | Salida | Hojas | PII | Notas |
|---|---|---|---|---|
| `informe_cobertura_excel.py` | `informe_cobertura_AMA_<fecha>.xlsx` | Resumen · Cobertura x grado · Faltan · Revisar match · De más | **Sí** | Semáforo **b)** (% por umbral 70/40) en Resumen; leyenda "Cómo leer" al pie; `auto_filter`; cohorte Escolar/Egresado en Iquitos. La plantilla más completa. |
| `informe_salida_excel.py` | `informe_salida_AMA_<fecha>.xlsx` | Salida por colegio (Resumen ciudad + detalle) | No (agregado) | Únicos por ciudad/colegio con desglose Kobo/Typeform; subtotales por ciudad + total. |
| `informe_base_vs_salida_excel.py` | `informe_base_vs_salida_AMA_<fecha>.xlsx` | Base vs salida (ciudad · grupo · colegio) | No (agregado) | Volumen, **no** cobertura; Δ y Salida/Base %. |
| `informe_entrada_salida_excel.py` | `entrada_salida_AMA_<fecha>.xlsx` | Entrada · Salida | **Sí** | Nivel persona, dos pestañas; documento en Salida se deja **crudo** (placeholders visibles). |

## Bot WhatsApp — Supabase (`Bot_monitoring/src/`)

| Script | Salida | Hojas | Notas |
|---|---|---|---|
| `report_bot.py` | `data/reports/reporte_bot_{from}_{to}.xlsx` | **Cómo leer este reporte** (leyenda, primera) · Por Ciudad · Por Colegio · Por Salón | Pivots `(fecha × dimensión)` con columnas por género + Total. Leyenda con grilla apagada. `agent_report.py` lo envuelve y añade narrativa LLM. |
| `user_report.py` | `data/reports/reporte_usuarios_{from}_{to}.xlsx` | Una hoja por ciudad activa | Nombre, Colegio, Salón, Sesiones Usadas (`S1 · S2 · S4`), # Sesiones. Expone `generate_user_report_bytes()`. |

> El código de `report_bot.py`/`user_report.py`/`db.py` vive **duplicado** en el repo gemelo
> `ama-weekly-report` (Estudio-Plural) para el cron de correo. Cambios al Excel o al prompt se
> sincronizan a mano entre ambos repos.

## Patrón `generate_*_bytes()` — descarga en Streamlit sin tocar disco

El dashboard no escribe el .xlsx a disco: lo arma en memoria con `io.BytesIO` y lo pasa al
`st.download_button`. Es la forma de reusar la misma función de armado para CLI (guarda archivo)
y para la app (devuelve bytes).

```python
# user_report.py
def generate_user_report_bytes(date_from: str, date_to: str) -> bytes:
    """Genera el Excel en memoria y retorna los bytes (para descarga en Streamlit)."""
    import io
    wb = _build_workbook(date_from, date_to)     # misma función que usa el CLI
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
```

En la app: envolver en `@st.cache_data` y cablear el botón con el mime de xlsx.

```python
excel_bytes = generate_user_report_bytes(str(r_from), str(r_to))
st.download_button(
    label="⬇  DESCARGAR EXCEL",
    data=excel_bytes,
    file_name=f"reporte_usuarios_{r_from}_{r_to}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    key="lb_download",
)
```

También sirve un DataFrame directo (`app.py` tab Leaderboard):

```python
buf = BytesIO()
with pd.ExcelWriter(buf, engine="openpyxl") as writer:
    df.rename(columns={...}).to_excel(writer, index=False, sheet_name="Ranking")
lb_xlsx_bytes = buf.getvalue()
```

## Elegí el semáforo correcto

- Comparás **asistencia vs Kobo** (levantamiento) → semáforo **a)** de `make_excel.py`
  (amarillo faltantes / verde excedentes / naranja ID a revisar).
- Reportás **% de cobertura o de avance** → semáforo **b)** de `informe_cobertura_excel.py`
  (verde ≥70 / amarillo 40–70 / rojo <40).
- Volcado técnico o solo conteos sin alertas → `df.to_excel` sin semáforo (`diagnostico.py`,
  `build_excel.py`).
