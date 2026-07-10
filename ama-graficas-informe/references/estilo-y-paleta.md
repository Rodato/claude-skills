# Estilo y paleta — gráfica canónica por género

Todo lo que define visualmente una gráfica del informe AMA. La implementación madre
es `crear_grafica()` en `Preprocesamiento/src/generar_graficas_informe.py`; la
versión más general (soporta 1-4 géneros + nota al pie) es `crear_grafica()` en
`Lineabase2026/tablero/lib.py`. Para el endline, cloná la del tablero.

## Paleta fija por género

```python
COLORES = {
    "Hombre": "#6cd2ff",              # azul claro
    "Mujer": "#fc684f",               # coral
    "Persona no binaria": "#9b59b6",  # púrpura
    "Prefiero no decir": "#95a5a6",   # gris
}
ORDEN_SEXOS = ["Hombre", "Mujer", "Persona no binaria", "Prefiero no decir"]
```

- El orden de dibujo/leyenda es siempre `ORDEN_SEXOS` (no alfabético).
- Fallback para un valor de sexo inesperado: `COLORES.get(sexo, "#888888")` (así lo hace `lib.py`).
- `edgecolor="white"` en todas las barras (separa las barras agrupadas).
- El azul `#6cd2ff` de "Hombre" es el **acento AMA**: el bot lo usa como color de
  barra genérico (`ACENTO = "#6cd2ff"`) en vez del teal `#0d9488` del tablero.

## Forma de la barra

- **Horizontal** (`ax.barh`), agrupada por respuesta. Una barra por género.
- `y_pos = np.arange(n_respuestas)`; cada género se dibuja en `y_pos + offset`.
- `ax.invert_yaxis()` → la primera respuesta queda **arriba**.
- Grid solo en X, punteado, sutil: `ax.xaxis.grid(True, linestyle="--", alpha=0.3)` + `ax.set_axisbelow(True)`.
- `figsize=(10, altura)` con **altura dinámica**: `altura = max(4, n_respuestas * 0.5 + 1.8)` (el tablero usa `+1.8`; el generador `+1.5`).

## Géneros dinámicos → grosor y offsets de barra

Solo se dibujan los géneros **con datos en esa variable**. El grosor y los offsets se
ajustan al número de géneros presentes. Versión del tablero (`lib.py`, generaliza a 1 y 4):

```python
sexos_con_datos = [s for s in ORDEN_SEXOS if s in dist["sexo"].values]
n_sexos = len(sexos_con_datos)
if n_sexos == 1:   bar_h, offsets = 0.5,  [0]
elif n_sexos == 2: bar_h, offsets = 0.38, [-0.19, 0.19]
elif n_sexos == 3: bar_h, offsets = 0.26, [-0.26, 0, 0.26]
else:              bar_h, offsets = 0.20, [-0.30, -0.10, 0.10, 0.30]
```

(El generador original solo contempla 2 y 3 géneros: `0.35 / [-0.175, 0.175]` y
`0.25 / [-0.25, 0, 0.25]`.) En línea base, 25 de 30 variables tienen "Persona no
binaria" (3 barras); **P31 y P32 solo tienen 2 barras** (Hombre/Mujer).

## Porcentaje: dentro de cada género

**Regla central:** el % se calcula **dentro de cada género** (suma 100% por género),
nunca sobre el total de la muestra. En `variables_encuesta_informe.py`:

```python
tabla = df_hm.groupby(['DEM_11', variable]).size().reset_index(name='n')
totales = df_hm.groupby(['DEM_11']).size().reset_index(name='total')
tabla = tabla.merge(totales, on=['DEM_11'])
tabla['porcentaje'] = (tabla['n'] / tabla['total'] * 100).round(1)
```

En **multi-respuesta** el denominador es el **total de menciones** de ese género
(no el nº de personas), para que la barra siga sumando 100% por género.

El xlabel lo dice explícito en el tablero: `"Porcentaje dentro de cada género (%)"`
(el generador usa `"Porcentaje (%)"`).

## Etiqueta de % al lado de cada barra

```python
for bar, val in zip(bars, datos):
    if val > 0:  # OJO: > 0, no `if val` (NaN es truthy)
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=fontsize_val, color="#333333")
```

- `fontsize_val = 8 if n_sexos <= 2 else 7`.
- El límite X deja aire para el texto: `ax.set_xlim(0, max_val * 1.25 if max_val > 0 else 10)`.

## Truncado de etiquetas de respuesta

Máximo ~45 chars, con `"..."`. El tablero además **colapsa espacios dobles** que trae
Kobo antes de truncar:

```python
def truncar(texto: str, n: int = 45) -> str:
    texto = re.sub(r"\s+", " ", str(texto)).strip()   # solo en lib.py
    return texto if len(texto) <= n else texto[: n - 3] + "..."
```

Las respuestas se ordenan: el generador **alfabético** (`sorted(...)`); el tablero por
**escala canónica** (`_ESCALA_ORDEN`: de acuerdo→en desacuerdo, nunca→todos los días,
etc.) y manda al final las residuales ("No sabría decir", "No tengo pareja").

## Título, leyenda, nota al pie

- Título: `ax.set_title(titulo, fontsize=12, fontweight="bold", pad=12)`.
- Leyenda solo si hay >1 género: `ax.legend(loc="lower right", fontsize=8)`.
- El tablero agrega una **nota de contexto al pie** (filtros aplicados) con `fig.text(0.5, 0.012, subtitulo, ha="center", ..., style="italic", color="#666666")` sin colisionar con el título.
- `fig.tight_layout()` siempre.

## Export: 300 dpi + PDF consolidado

PNG individual a 300 dpi, fondo blanco:

```python
fig.savefig(archivo_salida, dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)   # cerrar siempre para no acumular figuras
```

Helper del tablero (para Streamlit, devuelve bytes):

```python
def figura_a_png(fig, dpi: int = 300) -> bytes:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    return buf.getvalue()
```

**PDF consolidado** con `matplotlib.backends.backend_pdf.PdfPages`: cada PNG se re-lee
y se pega en una página propia (patrón en `main()` del generador):

```python
with PdfPages(ruta_pdf) as pdf:
    for ruta_png, titulo in figuras:
        img = plt.imread(ruta_png)
        fig, ax = plt.subplots(figsize=(10, img.shape[0]/img.shape[1]*10))
        ax.imshow(img); ax.axis("off")
        pdf.savefig(fig, bbox_inches="tight", facecolor="white")
        plt.close(fig)
```

En Streamlit: **display a 130 dpi, descarga a 300 dpi** (ver `references/embed-streamlit.md`).

## Backend en Streamlit

`lib.py` fuerza el backend sin GUI **antes** de importar pyplot:

```python
import matplotlib
matplotlib.use("Agg")   # apto para Streamlit / servidores
import matplotlib.pyplot as plt
```

## Diferencias generador ↔ tablero (resumen)

| Aspecto | `generar_graficas_informe.py` | `tablero/lib.py` |
|---|---|---|
| Fuente de variables | dict `ARCHIVOS_CONFIG` hardcodeado (CSVs pre-computados) | dinámico desde `diccionario_datos.csv` (`registro_variables`) |
| Géneros soportados | 2 o 3 | 1, 2, 3 o 4 |
| Orden de respuestas | alfabético | escala canónica `_ESCALA_ORDEN` |
| Multi-respuesta | split por **coma** | split por **espacio** (greedy vs form XML) |
| Truncado | sin colapsar espacios | colapsa espacios dobles de Kobo |
| xlabel | `"Porcentaje (%)"` | `"Porcentaje dentro de cada género (%)"` |
| Nota al pie | no | sí (`subtitulo` con filtros) |
| altura | `n*0.5 + 1.5` | `n*0.5 + 1.8` |
| Export | `fig.savefig` a disco + PdfPages | `figura_a_png` a bytes (base64) |

Ambos comparten la paleta, la orientación horizontal, el % por género, el truncado a
45, la etiqueta `{val:.1f}%` y los 300 dpi. **Eso es lo que hace que se vean iguales.**
