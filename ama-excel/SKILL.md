---
name: ama-excel
description: >-
  Convenciones de los informes Excel (openpyxl) del programa AMA: libros
  multi-hoja con semáforo de colores, hoja-leyenda "Cómo leer este reporte",
  una hoja por ciudad/colegio/salón, teléfonos y documentos como texto, y reglas
  de PII (datos de menores → local, gitignored, nunca commitear). Usar al
  generar o editar cualquier informe .xlsx de AMA (seguimiento Kobo, cobertura
  base↔salida, reporte semanal del bot, datos técnicos por colegio) para copiar
  el informe existente más parecido en vez de reinventar estilo y reglas.
---

# AMA Excel — informes openpyxl del programa AMA

Todo informe .xlsx de AMA sale de openpyxl con el mismo ADN: **libro multi-hoja**,
**semáforo de colores** con significado fijo, una **hoja-leyenda** que explica cómo leerlo,
**una hoja por dimensión** (ciudad / colegio / salón) y **PII bajo control** (datos de
menores nunca salen del disco local). Hay 14 scripts con esta huella en el proyecto — antes
de escribir uno nuevo, **copiá el informe existente más parecido** (catálogo en
`references/patrones-informe.md`) en vez de reinventar.

## Antes de empezar

1. ¿Qué informe se parece más al que pide el usuario? Buscalo en `references/patrones-informe.md`
   y abrí ese script como plantilla — reusá su estilo, sus hojas y su bloque de notas.
2. ¿Lleva **PII** (nombre/documento/teléfono de menores)? Entonces va a carpeta gitignored
   (`data/reports/` o `outputs/`), **no se commitea**, se comparte por canal privado. Ver
   la skill hermana `ama-pii`. Si es solo conteos agregados, puede ir sin restricción.
3. ¿De dónde salen los datos? Kobo/Typeform/Supabase — ver `ama-kobo`. Estilo y reglas de
   estilo detalladas en `references/estilo-openpyxl.md`.

## El semáforo (la convención que se repite)

Dos semáforos distintos según el informe — **no los confundas**:

**a) Diferencia asistencia vs Kobo** (seguimiento de levantamiento, `make_excel.py`):
la celda de la columna `Diferencia` (= Kobo − Asistencia) se colorea por signo, y una fila
entera se pinta naranja si hubo match por nombre (posible ID mal digitado).

| Color | Hex | Significado |
|---|---|---|
| Amarillo | `FFEB9C` | Diferencia negativa: asistencia > Kobo → **faltantes de encuesta** |
| Verde | `C6EFCE` | Diferencia positiva: Kobo > asistencia → **excedentes** |
| Naranja claro | `FCE4D6` | Fila con match por nombre → **posible ID incorrecto, revisar** |

**b) Semáforo por % de cobertura** (informe de cobertura, `informe_cobertura_excel.py`):
la celda `% Cobertura` de la hoja Resumen se pinta por umbral.

| Color | Hex | Umbral |
|---|---|---|
| Verde | `C6EFCE` | `% ≥ 70` |
| Amarillo | `FFEB9C` | `40 ≤ % < 70` |
| Rojo | `FFC7CE` | `% < 40` |

El trío verde/amarillo/rojo (`C6EFCE`/`FFEB9C`/`FFC7CE`) es constante entre informes. El
naranja de "revisar" varía: `FCE4D6` (match por nombre) vs `FFF2CC` (fila de baja confianza a
verificar a mano, hoja "Revisar match"). Hex completos y helper reutilizable en
`references/estilo-openpyxl.md` y `scripts/excel_helpers.py`.

## Hoja-leyenda "Cómo leer este reporte"

Todo informe que va a manos del equipo lleva una explicación de columnas, colores y qué
significa "Diferencia" / "Cobertura". Dos formas en el código:

- **Hoja dedicada, primera del libro** (`report_bot.py::write_instructions`): título +
  secciones "¿Qué es este reporte?", "Hojas del archivo", "Cómo leer cada tabla", "Notas
  importantes". Se le apaga la grilla: `ws.sheet_view.showGridLines = False`.
- **Bloque de notas al pie de la hoja Resumen** (informes de cobertura/salida): un encabezado
  "Cómo leer este informe" / "Notas" y viñetas `•` en `Font(size=10)`.

Snippet listo en `scripts/excel_helpers.py::write_legend_sheet`.

## Una hoja por dimensión

El eje de cada libro es una dimensión de negocio, una hoja por valor:

- **Por ciudad**: `datos_tecnicos.py` (Cobija / Leticia), `make_excel.py` (Diferencias Leticia
  / Diferencias Cobija), `user_report.py` (una hoja por ciudad activa).
- **Por colegio**: `listado_salones.py` (una pestaña por colegio — nombres ≤ 31 chars y únicos,
  abreviando "Institución Educativa"→"IE").
- **Por salón / curso**: pivots del reporte del bot.
- **Multi-hoja temática**: cobertura = 5 hojas (Resumen, Cobertura x grado, Faltan, Revisar
  match, De más); reporte bot = 4 hojas (leyenda + Ciudad + Colegio + Salón).

## Reglas no negociables

- **Teléfonos y documentos como TEXTO.** Leer siempre `pd.read_csv(..., dtype=str)` (Kobo va con
  `sep=";"`) para no perder ceros a la izquierda ni que Excel convierta un documento largo a
  notación científica. Para una columna que Excel jamás debe interpretar como número, además
  `cell.number_format = "@"` (convención del export de ganadores del bot).
- **PII de menores → local y gitignored.** `datos_tecnicos`, `faltantes`, `entrada_salida`,
  `matching` y cualquier libro con nombre/documento/teléfono se generan local, van en
  `data/reports/` u `outputs/` (gitignored), **no se commitean**, se comparten por canal
  privado. Ver `ama-pii`. Los informes de solo conteos agregados no tienen esta restricción.
- **openpyxl NO va en el `requirements.txt` de los dashboards.** Es herramienta de análisis, no
  del deploy de Streamlit (nota explícita en lago-agrio). Vive en el `.venv` local.
- **Nombre de archivo con fecha.** `seguimiento_FECHAS.xlsx`, `diagnostico_FECHA[_DESDE_HASTA].xlsx`,
  `informe_cobertura_AMA_<fecha>.xlsx`, `reporte_bot_{from}_{to}.xlsx`,
  `datos_tecnicos_FECHA.xlsx`. Fecha con `datetime.now().strftime("%Y-%m-%d")` o
  `"_".join(d.replace("-","") for d in dates)`.
- **Descarga en Streamlit = bytes en memoria, sin tocar disco.** Patrón `generate_*_bytes()`
  con `io.BytesIO()` para el `st.download_button`. Ver `references/patrones-informe.md`.
- **Código en inglés, comentarios y textos de usuario en español.** `python3`.

## References y scripts

- `references/estilo-openpyxl.md` — semáforo (hex exactos), Font/Alignment/PatternFill/Border,
  freeze panes, autoancho, teléfono como texto, escritura manual vs `df.to_excel`.
- `references/patrones-informe.md` — catálogo de los 14 informes (qué hojas tiene cada uno)
  para copiar el más parecido; y el patrón `generate_*_bytes()` para Streamlit.
- `scripts/excel_helpers.py` — helpers mínimos extraídos del código real (semáforo por regla,
  hoja-leyenda, header estilizado, autoancho, teléfono como texto).

## Skills hermanas

- `ama-pii` — reglas de PII de los Excel con datos personales de menores.
- `ama-kobo` — de dónde salen los datos (columnas Kobo, `sep=";"`, `dtype=str`, grado duplicado).
- `ama-dashboard-encuesta` — el botón de descarga (`generate_*_bytes`) en Streamlit.
