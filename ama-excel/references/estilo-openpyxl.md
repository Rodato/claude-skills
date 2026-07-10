# Estilo openpyxl — AMA

Detalle de estilo extraído del código real. Hex, fonts y helpers para que un informe nuevo
se vea como los existentes. Snippets cortos; el código completo está en cada script (ver
`patrones-informe.md`) y los helpers reutilizables en `../scripts/excel_helpers.py`.

## Imports canónicos

```python
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
```

## Semáforo — hex exactos

El trío verde/amarillo/rojo es **constante entre informes**; son los mismos colores del
conditional-formatting estándar de Excel.

```python
GREEN  = PatternFill("solid", fgColor="C6EFCE")   # bien / positivo / % ≥ 70
YELLOW = PatternFill("solid", fgColor="FFEB9C")   # atención / negativo / 40 ≤ % < 70
RED    = PatternFill("solid", fgColor="FFC7CE")   # crítico / % < 40
```

Naranjas de "revisar" (según el informe):

```python
NAME_MATCH   = PatternFill("solid", fgColor="FCE4D6")  # fila con match por nombre → ID a corregir
REVISAR_FILL = PatternFill("solid", fgColor="FFF2CC")  # fila de baja confianza a verificar a mano
```

### Regla a) Diferencia por signo (`make_excel.py`)

`Diferencia = Kobo − Asistencia`. Negativo (amarillo) = faltan encuestas; positivo (verde) =
excedentes. Solo la celda de esa columna se pinta (más negrita); el resto de la fila lleva
zebra o el naranja de name-match.

```python
try:
    v = float(val)
    color = COL_NEG if v < 0 else (COL_POS if v > 0 else base_color)   # FFEB9C / C6EFCE
except (TypeError, ValueError):
    color = base_color
cell.fill = PatternFill("solid", fgColor=color)
cell.font = Font(bold=True)
```

### Regla b) Semáforo por % (`informe_cobertura_excel.py`)

```python
def pct_fill(p):
    if p is None:
        return None
    if p >= 70:
        return GREEN
    if p >= 40:
        return YELLOW
    return RED
```

## Paletas de encabezado (NO están unificadas)

Cada familia de informes usa su propio azul/teal para el header. Reusá el del informe que
copiás, no mezcles.

| Familia | Header fill | Ejemplos |
|---|---|---|
| Lineabase — seguimiento | `1F497D` (azul oscuro) + sección `D9E1F2` | `make_excel.py` |
| Lineabase — listados | `2E74B5` / `2E75B6` | `listado_salones.py` |
| Lineabase — consolidado | `2F4F8F` header, grupos `DDEEFF`/`DDFFDD` | `consolidado_genero.py` |
| Bot (Supabase) | `1F4E79` header, `2E75B6` subheader, `D6E4F0` zebra, `BDD7EE` total | `report_bot.py`, `user_report.py` |
| Lago Agrio — cobertura/salida | `1F4E5F` (teal oscuro), subtotal `DCE6EB` | los `informe_*_excel.py` |

Header estándar (texto blanco, centrado, borde):

```python
HDR_FILL = PatternFill("solid", fgColor="1F4E5F")
HDR_FONT = Font(bold=True, color="FFFFFF", size=11)
cell.fill = HDR_FILL; cell.font = HDR_FONT
cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
```

Fuentes de título / subtítulo / total que se repiten:

```python
TITLE_FONT = Font(bold=True, size=15, color="1F4E5F")
SUB_FONT   = Font(italic=True, size=10, color="555555")
TOTAL_FONT = Font(bold=True)
```

## Bordes

```python
THIN   = Side(style="thin", color="D0D0D0")   # o "BFBFBF" / "AAAAAA" según el informe
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
```

## Freeze panes

Dos formas válidas en el código, ambas fijan la fila de encabezado:

```python
ws.freeze_panes = "A2"                              # string A1-style
ws.freeze_panes = ws.cell(row=hdr_row + 1, column=1)  # objeto celda (header no en fila 1)
```

## Ancho de columnas

Manual (lista de anchos, control fino del layout):

```python
for c, w in enumerate([12, 10, 28, 40, 22], 1):
    ws.column_dimensions[get_column_letter(c)].width = w
```

Autoancho por contenido (con tope, para libros salidos de `df.to_excel`):

```python
for col_cells in ws.columns:
    max_len = max((len(str(c.value)) if c.value is not None else 0) for c in col_cells)
    ws.column_dimensions[col_cells[0].column_letter].width = min(max_len + 2, 50)
```

## Teléfono / documento como TEXTO

La regla que evita perder dígitos: leer el CSV con `dtype=str` (Kobo además `sep=";"`). Así el
valor llega como string y openpyxl lo guarda como texto.

```python
df = pd.read_csv(path, sep=";", dtype=str, low_memory=False)   # Kobo
df["Teléfono"] = df[phone_col].str.strip()
```

Para forzar que Excel nunca lo interprete como número (documento largo → notación científica),
además fijá el formato de celda:

```python
cell = ws.cell(row=r, column=c, value=str(phone))
cell.number_format = "@"   # texto explícito
```

## Zebra (filas alternadas)

```python
base_color = "FFFFFF" if r_idx % 2 == 0 else "EBF1F8"     # Lineabase
# o, en el bot:  if row_idx % 2 == 1: cell.fill = ALT_FILL  # D6E4F0
```

## Fila total / subtotal

Negrita + fill propio; en cobertura la fila TOTAL se recorre entera poniendo `TOTAL_FONT`;
en salida el subtotal por ciudad lleva `SUBTOTAL_FILL = DCE6EB`.

## Hoja-leyenda: apagar la grilla

```python
ws.sheet_view.showGridLines = False   # solo en la hoja "Cómo leer este reporte"
ws.column_dimensions["A"].width = 90  # una sola columna ancha para el texto corrido
```

## Dos maneras de volcar un DataFrame

- **Celda por celda** (`make_excel`, `report_bot`, los `informe_*`): permite semáforo, zebra,
  merges, subtotales, filas de notas. Es la vía cuando el libro va al equipo.
- **`df.to_excel(writer, engine="openpyxl")`** (`datos_tecnicos`, `build_excel`, `diagnostico`):
  rápido para volcados grandes o técnicos; después se ajusta ancho y freeze sobre
  `writer.sheets[nombre]`. Sin semáforo.

```python
with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
    df.to_excel(writer, sheet_name="Cobija", index=False)
    ws = writer.sheets["Cobija"]
    ws.freeze_panes = "A2"
```

## Nombres de hoja ≤ 31 chars y únicos (`listado_salones.py`)

Excel corta a 31 y exige unicidad. Abreviar y desambiguar:

```python
_ABBREVS = [("Institución Educativa ", "IE "), ("Escuela Normal Superior ", "ENS ")]
# ... aplicar prefijo, recortar a [:31], y si colisiona añadir "(2)", "(3)"...
```
