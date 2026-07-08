# Reportes complementarios (Excel + narrativa LLM + envío por cron)

Patrón opcional pero recurrente: además del dashboard interactivo, generar **reportes periódicos**
(típicamente semanales) para stakeholders que no entran al dashboard. Referencia viva:
`AMA/Bot_monitoring/src/*_report.py` + repo gemelo `ama-weekly-report`.

## Piezas

```
report_bot.py     # arma el Excel: pivots (fecha × dimensión) por hoja
agent_report.py   # orquestador: report_bot + narrativa en Markdown vía LLM (OpenRouter)
user_report.py    # listado por ciudad/segmento (Excel), también expuesto en un tab del dashboard
send_report.py    # envío por correo (usado desde el repo gemelo con cron)
```

## Excel (`report_bot.py`)

- Una hoja inicial **"Cómo leer este reporte"** + una hoja por dimensión (Por Ciudad, Por Colegio, Por Salón).
- Cada hoja: pivot `(fecha × dimensión)` con columnas por segmento (ej. género) + Total (únicos/día).
- Reutiliza `db.py` — mismas queries, mismo filtro de test, misma timezone.
- Para exponer el mismo reporte como **descarga en el dashboard** sin tocar disco:
  `generate_..._bytes() -> bytes` que devuelve el Excel en memoria (`BytesIO`) para `st.download_button`.

## Narrativa LLM (`agent_report.py`)

```bash
python3 src/agent_report.py --from YYYY-MM-DD --to YYYY-MM-DD
python3 src/agent_report.py --from … --to … --no-llm       # solo Excel
python3 src/agent_report.py --from … --to … --model anthropic/claude-sonnet-4-6
```
- LLM vía **OpenRouter** (`OPENROUTER_API_KEY`), cliente `openai` apuntando al endpoint de OpenRouter.
- **Estilo de la narrativa (reglas duras):** prosa continua, **sin** headers/bullets/markdown.
  5–7 párrafos cortos. Orden: resumen general → segmento principal → sub-segmentos → evolución
  semanal desde el lanzamiento. **Puramente descriptivo** — sin "puntos de atención", sin
  interpretaciones, sin párrafo genérico de cierre.
- Salida: `data/reports/reporte_..._{from}_{to}.{xlsx,md}` (carpeta gitignored).

## Envío automático (repo gemelo + cron)

- El envío por correo vive en un **repo gemelo liviano** (ej. `ama-weekly-report`) con solo los
  archivos de reporte + workflow + requirements (sin streamlit/plotly).
- **GitHub Actions cron** (ej. lunes 8 AM Bogotá) corre el reporte y lo manda por correo.
- **Gotcha de duplicación:** `report_bot.py`, `agent_report.py`, `db.py` y `send_report.py` viven
  **duplicados** entre el repo del dashboard y el repo gemelo. Cambios al prompt o al Excel deben
  **sincronizarse a mano** en ambos. (Si vas a tocar el reporte, revisá los dos repos.)

## Reportes one-off (cruces de datos)

Para pedidos puntuales del equipo (ej. "denme los celulares de los ganadores del concurso"),
el patrón es un script temporal que cruza tablas del bot con una fuente externa (encuesta):
- El teléfono **sale del bot** (`client_number`); la fuente externa solo recupera el nombre real.
- Match por teléfono (fiable) antes que por nombre (sucio).
- **PII de menores:** Excel solo local, borrar el script al terminar, no commitear, canal privado.
  (Ver `convenciones-gotchas.md` → PII.)
