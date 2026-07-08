# Convenciones obligatorias y gotchas

Lista de chequeo. La mayoría de bugs futuros de estos dashboards está acá. Repasala antes de
dar por terminado un cambio.

## SQL y datos

- **Siempre parametrizado** (`%s` psycopg2 / `:param` SQLAlchemy). Nunca f-strings con datos externos.
- **Timezone `America/Bogota` en toda query de tiempo** (`DATE(col AT TIME ZONE 'America/Bogota')`).
  La DB guarda UTC. El "hoy" del sidebar también en esa zona (`ZoneInfo`), no `date.today()`.
- **Toda query nueva pasa por `_date_filter()`** para heredar el filtro de cuentas de test/eval.
  No hacer `fetch_df` directo sin pensar qué datos traés.
- `date_to` de los filtros es **exclusivo** (fecha + 1 día).
- Casts: `text`→`::int` para ordenar; DATE de pg8000 →`::text` si Plotly muestra hora de más.

## Streamlit

- **`key=` vs `value=`:** si un widget usa `key=`, **no** pasar también `value=` (Streamlit lanza
  warning). Poner el valor inicial en `st.session_state` antes de crear el widget.
- **Presets que mutan widgets** (botones 7d/30d que cambian los date pickers): usar `on_click`
  callbacks. Asignar a `st.session_state[key]` **después** de renderizar el widget se ignora silenciosamente.
- **`@st.cache_data` necesita params hasheables** → pasar listas como `tuple()`.
- **Invalidación diaria del cache:** los wrappers cacheados aceptan un param centinela `_TODAY`
  (fecha de hoy en Bogotá) para forzar refresco al cambiar de día.
- **Estado compartido entre usuarios va a la DB, no a `st.session_state`** (que es por sesión de
  browser). Ej.: "marcar alerta revisada" persiste en una columna `reviewed_at`, no en memoria.
- **Filtros globales** viven en `st.session_state` (`filter_from`, `filter_to`, `selected_bot`),
  inicializados en `filters.py`, leídos con un `get_filters()`.

## Gráficas

- `go.*` + `.tolist()`, **nunca `px.*`** bajo `@st.cache_data` (px lee el índice, no los valores).
- Series temporales: rellenar días sin datos con 0, fijar el eje X al rango (`fixedrange=True`),
  ocultar el modebar. Si no, un rango con datos escasos parece un filtro roto.
- No `title_x=0` sin título (Plotly renderiza `"undefined"`).
- Colores desde `COLORS`, nunca hex hardcodeado.

## Python / entorno

- **Driver Postgres:** `pg8000` (no `psycopg2`) para **Python 3.12+** / Streamlit Cloud —
  psycopg2 no tiene wheels para 3.12+ y rompe el build. Forzar con `make_url(...).set(drivername=...)`,
  no con `.replace()`.
- **Python 3.9 (si el runtime es viejo):** no usar `X | None` (PEP 604) en anotaciones de módulos
  compartidos — falla al importar con `TypeError`. Usar `Optional[X]` de `typing`, o
  `from __future__ import annotations` al inicio del módulo. **Ojo:** `py_compile` NO atrapa esto
  (es eval en runtime al definir la función), y un HTTP 200 de Streamlit es solo el shell estático.
  Verificar con `python3 -c "import módulo"` o `streamlit.testing.v1.AppTest`.

## PII y datos sensibles

- **Enmascarar teléfonos en la UI** (primeros 4 dígitos + `****` + últimos 2). Los exports para el
  equipo de respuesta pueden llevar el número completo, **intencionalmente y solo en ese caso**.
- **Datos de menores:** generar Excel/CSV solo en local (raíz o `data/reports/` que está gitignored),
  **borrar scripts temporales** al terminar, **no commitear** ni subir a nada público, compartir
  solo por canal privado.
- `client_number` **ES el celular** del usuario (número de WhatsApp con prefijo de país):
  Colombia `57` + 10 dígitos, Bolivia `591` + 8. Tratar como PII.

## Contrato con el bot (acoplamiento a vigilar)

El dashboard **lee** lo que el bot **escribe**. Cambios en el formato del bot rompen el dashboard:
- `keywords` / `flags`: strings CSV. `flags` con prefijos de severidad (`HIGH-`/`MEDIUM-`/`LOW-`).
  La lógica de clasificación suele estar **duplicada** en varias páginas → si el bot cambia el
  formato, actualizar `_classify_flag()` en **todos** los archivos que lo repliquen.
- Campos i18n (`summary_i18n`, `keywords_i18n` JSONB) pueden no existir aún → detectar con
  `information_schema` (cacheado) y hacer fallback a la columna original; nada debe romperse si la
  migración del bot todavía no corrió.
- Nombres de usuario vienen **sucios** ("Me llamo Roset hshs", "Esq últimamente me siento…") →
  para cruces por nombre, match difuso por tokens; para identidad fiable, cruzar por teléfono.

## Documentación

Cada repo tiene su `CLAUDE.md`. Actualizarlo cuando cambie: arquitectura, stack, esquema de la DB,
páginas/componentes, flujo de datos bot→dashboard. **No** por bugfixes menores, ajustes de UI o copy.
