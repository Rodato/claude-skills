---
name: rendimiento-web
description: >-
  Auditoría y optimización de rendimiento de un sitio web (sobre todo Next.js en
  Vercel, con Postgres detrás) que mide antes de tocar, compara bytes de
  producción contra el build local en el navegador real, revisa con los ojos
  antes de cambiar un formato de imagen o fuente, y entrega un informe que dice
  también qué se revisó y NO se tocó, y por qué. Úsala cuando el pedido sea
  optimizar, acelerar o "hacer más liviana" una página, o cuando llegue la lista
  típica: renders innecesarios, bundle y lazy loading, requests y caché, queries
  lentas o N+1, imágenes, fuentes y scripts — "la página carga lento",
  "optimizá el rendimiento", "bajale el peso", "pasale Lighthouse", "mejorá el
  LCP / Core Web Vitals". También cuando haya que decidir si vale la pena una
  optimización que alguien propuso. No es para pruebas de carga del backend ni
  para tunear Postgres por dentro.
---

# rendimiento-web — pesar, cambiar, volver a pesar

Salió de la auditoría de `revestidos` (Next 16 + Vercel + Neon, oct-2026), que
bajó la portada de 528 a 327 KB y el formulario de 400 a 240 KB sin cambiar
cómo se ven. Lo que la hizo útil no fue la lista de cinco puntos —esa la pide
cualquiera— sino la forma de trabajar:

1. **Se mide antes de tocar.** Lo que no se midió no se cambia.
2. **Se comparan bytes, no tiempos.** Misma página, producción contra build
   local, en el mismo navegador.
3. **Se mira antes de cambiar un formato.** AVIF, WebP, subsets de fuente:
   recorte ampliado, lado a lado.
4. **La mitad del informe es lo que no se tocó.** Un pedido de cinco puntos
   tienta a devolver cinco arreglos. Si un punto no tiene nada que ganar, se
   dice con el número que lo demuestra y se sigue. Inventar trabajo para
   llenar la lista es peor que no hacer nada: agrega riesgo sin ganancia.

## Antes de empezar

- **Next moderno no es el de tu entrenamiento.** Si el repo trae `AGENTS.md`
  pidiendo leer `node_modules/next/dist/docs/`, leé la guía de lo que vas a
  tocar (fuentes, imágenes, caché, lazy loading) antes de escribir código.
- **¿El `.env.local` apunta a producción?** Pasa: no hay base de desarrollo.
  Entonces `next build` y `next start` LEEN la base real (páginas
  prerenderizadas, consultas cacheadas). Leer está bien; **nunca envíes un
  formulario** ni dispares una ruta que escriba mientras medís.
- **¿Cada push a `main` despliega?** Casi siempre sí en Vercel. El commit y el
  push se preguntan, aunque la vez anterior hayan dicho que sí.

## 1. Inventario (cinco minutos)

```bash
cat package.json next.config.* vercel.json 2>/dev/null
grep -rln '"use client"' app components src 2>/dev/null   # qué baja al navegador
du -sh public/* | sort -h | tail                         # assets crudos
find app components lib src -name '*.ts*' 2>/dev/null | xargs wc -l | sort -n | tail -20
```

Leé las páginas principales y los componentes de cliente antes de opinar. En
un repo cuidado, los comentarios ya explican optimizaciones hechas (fachada de
YouTube, aforo cacheado para que la base duerma): no las "descubras" de nuevo.

## 2. Línea base — los números de antes

**El peso de cada página**, con `scripts/pesar-pagina.py` (solo stdlib):

```bash
python3 <skill>/scripts/pesar-pagina.py https://el-sitio.com/
python3 <skill>/scripts/pesar-pagina.py https://el-sitio.com/formulario
```

Lista JS, CSS y fuentes con su peso crudo y comprimido, marca qué se
**precarga**, y muestra los `cache-control` / `x-vercel-cache` / `x-vercel-id`
de cada tipo. Sirve igual contra `http://localhost:3000` con `next start`.

Ojo al buscar precargas a mano: una página **estática** las escribe como
`<link rel="preload">` en el HTML, pero una **dinámica** las manda en el
encabezado HTTP `Link` (`curl -sD - -o /dev/null <url> | grep -i ^link:`).
Un `grep` sobre el HTML de una página dinámica dice "no precarga nada" y es
falso. El script lee las dos cosas.

**Dónde está el código propio dentro del JS.** Turbopack ya no imprime tamaños
por ruta. Buscá un texto que solo exista en tu código:

```bash
cd .next/static/chunks && grep -l "Texto único de un componente" *.js
```

Si el chunk de una página trae textos de config que no usa (un versículo, la
lista de invitados), un componente de cliente está importando el módulo de
config entero.

**Regiones.** Antes de perseguir N+1, mirá si función y base están cerca:

```bash
curl -sI https://el-sitio.com/una-ruta-dinamica | grep -i x-vercel-id   # iad1::iad1::… → la 2.ª es la función
node --env-file=.env.local -p "new URL(process.env.DATABASE_URL).hostname.split('.').slice(1).join('.')"
```

Imprime solo la región del host, no la cadena: la cadena es un secreto. Si
función y base están en la misma región, cada consulta cuesta milisegundos y
juntar dos consultas en una no se va a notar.

## 3. Por área: qué buscar y cuándo NO tocar

### Renders innecesarios
- Un formulario que se redibuja entero con cada tecla está bien si la lista
  es corta (decenas de campos). `memo` y `useCallback` ahí agregan código sin
  ganancia medible.
- `setState(mismoValor)` en un listener de scroll no re-renderiza: React
  descarta el update si el valor no cambió.
- Sí vale: estado global que redibuja árboles grandes, listas de cientos de
  filas, contextos que cambian en cada render.

### Bundle y lazy loading
- Mirá cuánto es código PROPIO (el chunk que contiene tus textos) contra
  React + Next. Si lo propio son ~10 KB comprimidos, el lazy loading no tiene
  de dónde sacar.
- Cargar en diferido el componente principal de una página la hace MÁS lenta.
  El candidato real es lo pesado de terceros que no todos usan: reproductor de
  video (fachada con cartel + iframe al dar play), mapas (`loading="lazy"`),
  editores, gráficas.
- Un componente de cliente que importa un módulo de config grande para usar
  un campo: pasale el campo por prop desde el servidor.

### Requests y caché
- `/_next/static/*` debería salir `public, max-age=31536000, immutable`.
- Una página con `revalidate` sale `STALE`/`HIT` del CDN: bien.
- `force-dynamic` no es pecado si el TTFB se parece al de una estática
  (mediílo con `curl -w "%{time_starttransfer}"` tres veces).
- Lo que se espera dentro del render y podría ir después de responder (un
  correo, refrescar una hoja) es candidato a `after()`. Si toca pagos o
  correos de confirmación, proponelo, no lo cambies solo.

### Queries lentas y N+1
- Buscá `await` dentro de `for`/`map` contra la base:
  `grep -rn "for (const\|\.map(async" app lib`.
- Inserciones en lote (`unnest`) y lecturas en `Promise.all` ya están bien.
- Con cientos o miles de filas e índices en las columnas del `where`, ninguna
  consulta es lenta: lo que pesa es la latencia de red y el arranque en frío
  de la base, no el plan.
- Un camino crítico con varias consultas en serie (escanear un pase en la
  puerta: sesión → pase → historial) se puede juntar, pero si función y base
  están en la misma región la ganancia son milisegundos. Reescribir lógica
  transaccional semanas antes de un evento no lo vale.

### Imágenes
- `next/image` **sin `sizes`** arma el `srcset` con el ancho del ARCHIVO
  (`1x`/`2x`): un logo de 1772 px que se ve a 350 se baja a 1920. Si el CSS
  fija el alto, calculá `sizes` desde ahí y dejá escrito que va calcado del
  CSS.
- **AVIF** no viene activado (`images.formats` es `['image/webp']` por
  defecto). Suele bajar 35-45 % la imagen del LCP. Antes de activarlo, si el
  arte trae texto adentro, compará con `scripts/comparar-formatos.mjs`.
- Los fondos puestos en CSS (`background-image: url(/x.jpg)`) **no pasan por
  el optimizador**. Convertilos a mano (WebP q80 suele ser la mitad) y dejá el
  original como fuente en `public/`.

### Fuentes (`next/font`)
- `subsets` **no decide qué letras existen, decide qué se PRECARGA**. Las
  demás quedan declaradas y se bajan solas si aparece una letra de ese rango.
  Para español, `['latin']` alcanza: tildes, eñes, ¿ ¡ y ü están ahí.
- `style: ['normal','italic']` precarga también la cursiva, en todas las
  páginas. Si la cursiva se usa en un solo lugar, sacala a una segunda
  llamada con `preload: false` y su propia `variable`, y que ese selector la
  pida por la variable. No confíes en que el navegador junte las dos
  declaraciones bajo un mismo nombre de familia: depende de cómo Next nombre
  cada una.
- **Cada peso del CSS tiene que estar en `weight`**, incluido el 700 que
  piden por defecto `<b>` y `<strong>`. Un peso que falta no da error: el
  navegador toma el más cercano hacia arriba y el 700 se ve en 800. En una
  fuente variable todos salen del mismo archivo, así que agregarlo no suma
  bytes, pero **sí cambia cómo se ve**: preguntá antes.

### Scripts de terceros
- Analítica, chat, pixel: `next/script` con `strategy="lazyOnload"` o
  `afterInteractive`, nunca en el `<head>` bloqueando.
- Si no hay ninguno, decilo y seguí.

## 4. Cambiar

- Un cambio por área, con su comentario de POR QUÉ en el código (el que
  venga después tiene que poder no deshacerlo).
- Después de cada build, verificá lo que cambiaste mirando el resultado, no
  el código: el HTML de `.next/server/app/*.html` (precargas, `sizes`), el CSS
  de `.next/static/chunks/*.css` (`@font-face`, `background-image`).
- **El CSS se reescribe en el build.** Ejemplo real: `image-set()` con un JPEG
  de respaldo salió como `-webkit-image-set(... type(...))`, que Safari 16 no
  entiende, y el `url()` de respaldo desapareció. Leé lo que salió.

## 5. Después — los números de ahora, en el navegador real

Levantá el build (`npx next start -p 3123`, en segundo plano) y cargá cada
página dos veces en Chrome: producción (antes) y local (después). En cada una
corré `scripts/medir-pagina.js` con `javascript_tool` (anteponé `await `):

```
navigate https://el-sitio.com/       → javascript_tool: await <contenido de medir-pagina.js>
navigate http://localhost:3123/      → javascript_tool: await <…>
```

- Compará **`encodedBodySize`** (lo que pesa cada recurso aunque venga de
  caché), no tiempos: local contra producción no se compara en milisegundos.
  El LCP local puede salir en un texto porque todo carga instantáneo.
- Sacá una captura o un zoom de lo que cambió de aspecto.
- La extensión de Chrome bloquea en la respuesta cualquier texto con query
  string (`[BLOCKED: Cookie/query string data]`): por eso el script devuelve
  el archivo y el ancho por separado.
- Si la extensión no está conectada, decilo una vez y seguí con
  `pesar-pagina.py` + la skill `browser-automation` (headless). No reintentes
  en bucle; si el usuario la conecta después, repetí la comparación ahí.
- Cerrá la pestaña y apagá el servidor local al terminar.

## 6. Informe

Corto, y en este orden:

1. **Antes / después por página**, en tabla, con KB. Solo números medidos.
2. **Qué cambió**, una línea por cambio con su número.
3. **Qué revisé y no toqué, y por qué** — con el dato que lo justifica
   ("función y base en la misma región", "código propio: 10 KB de 180").
4. **Lo que encontré que cambia el diseño** y no hice sin preguntar.
5. Commit y push: preguntar. El mensaje del commit lleva la misma tabla y el
   mismo "qué no se tocó", para que quien vuelva a buscar no repita la
   auditoría.

## Scripts

| archivo | para qué |
|---|---|
| `scripts/pesar-pagina.py <url>` | JS/CSS/fuentes de una página con peso crudo y gzip, precargas y encabezados de caché. Solo stdlib. |
| `scripts/medir-pagina.js` | Pegar en `javascript_tool` (con `await`): LCP, fuentes, imágenes (archivo, ancho pedido, KB), JS, CSS, total y precargas. Baja toda la página para que carguen las imágenes diferidas. |
| `scripts/comparar-formatos.mjs <imagen> [--ancho 828] [--recorte x,y,w,h]` | Codifica como lo hace Next (WebP q75, AVIF q47 effort 3), imprime los pesos y arma dos PNG lado a lado: completo y recorte ampliado. Usa el `sharp` del proyecto: correrlo desde la raíz del repo. |
