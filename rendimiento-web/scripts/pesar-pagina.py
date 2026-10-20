#!/usr/bin/env python3
"""
Pesa lo que el HTML de una página manda a bajar: JS, CSS y fuentes, cada uno
con su peso crudo y comprimido (gzip), qué se PRECARGA, y los encabezados de
caché de cada tipo. Solo stdlib.

    python3 pesar-pagina.py https://el-sitio.com/
    python3 pesar-pagina.py http://localhost:3123/formulario

Lo que no cuenta, a propósito:
  · Imágenes: cuál variante se baja depende del ancho de pantalla y del
    `sizes`; eso se mide en el navegador (medir-pagina.js).
  · Chunks que el runtime pide después de cargar (navegación, prefetch).
  · Fuentes declaradas en el CSS pero no precargadas: se listan aparte,
    porque el navegador solo las baja si las usa.
"""
import gzip
import re
import sys
import urllib.request
from html import unescape
from urllib.parse import urljoin

CABECERAS = ("cache-control", "x-vercel-cache", "x-vercel-id", "age")


def pedir(url):
    req = urllib.request.Request(
        url,
        headers={
            # Sin compresión: el peso crudo se mide acá y el gzip se calcula.
            "Accept-Encoding": "identity",
            "User-Agent": "Mozilla/5.0 (rendimiento-web)",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        cab = {k.lower(): v for k, v in r.headers.items()}
        # Puede venir más de un Link; el dict de arriba se quedaría con uno.
        cab["link"] = ", ".join(r.headers.get_all("link") or [])
        return r.read(), cab


def atributos(etiqueta):
    return {k.lower(): unescape(v) for k, v in re.findall(r'([\w:-]+)="([^"]*)"', etiqueta)}


def kb(n):
    return f"{n / 1024:7.1f}"


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    pagina = sys.argv[1]
    cuerpo, cab = pedir(pagina)
    html = cuerpo.decode("utf-8", "replace")

    scripts, estilos, precargas = [], [], []
    for t in re.findall(r"<script\b[^>]*>", html):
        a = atributos(t)
        if a.get("src"):
            scripts.append(urljoin(pagina, a["src"]))
    for t in re.findall(r"<link\b[^>]*>", html):
        a = atributos(t)
        rel, href = a.get("rel", ""), a.get("href")
        if not href:
            continue
        if rel == "stylesheet":
            estilos.append(urljoin(pagina, href))
        elif rel == "preload":
            precargas.append((a.get("as", "?"), urljoin(pagina, href)))

    # Una página dinámica de Next no escribe sus precargas en el HTML: las
    # manda en el encabezado `Link` (y en el payload de RSC). Sin leerlo,
    # parecería que la página no precarga nada.
    for href, resto in re.findall(r"<([^>]+)>\s*;([^<]*)", cab.get("link", "")):
        if re.search(r"rel=\"?preload", resto):
            como = re.search(r"as=\"?(\w+)", resto)
            par = (como.group(1) if como else "?", urljoin(pagina, href))
            if par not in precargas:
                precargas.append(par)

    print(f"\n{pagina}")
    print(f"HTML {kb(len(cuerpo))} KB crudo {kb(len(gzip.compress(cuerpo)))} KB gzip")
    print("  " + " · ".join(f"{k}: {cab[k]}" for k in CABECERAS if k in cab))

    def tabla(titulo, urls):
        if not urls:
            return 0, 0
        print(f"\n{titulo}")
        crudo_total = gz_total = 0
        cabeceras = None
        for u in dict.fromkeys(urls):
            datos, c = pedir(u)
            crudo, gz = len(datos), len(gzip.compress(datos))
            crudo_total += crudo
            gz_total += gz
            cabeceras = cabeceras or c
            marca = " (precarga)" if any(u == p for _, p in precargas) else ""
            print(f"  {kb(crudo)} KB  {kb(gz)} KB gz  {u.rsplit('/', 1)[-1][:48]}{marca}")
        print(f"  {kb(crudo_total)} KB  {kb(gz_total)} KB gz  TOTAL")
        if cabeceras:
            print("  " + " · ".join(f"{k}: {cabeceras[k]}" for k in CABECERAS if k in cabeceras))
        return crudo_total, gz_total

    js = tabla("JS", scripts)
    css = tabla("CSS", estilos)
    fuentes_pre = [u for como, u in precargas if como == "font"]
    fu = tabla("Fuentes precargadas", fuentes_pre)

    # Las que el CSS declara: cuántas hay y cuánto pesarían todas. No se
    # bajan todas: solo las de los rangos y estilos que la página use.
    declaradas = []
    for e in estilos:
        texto = pedir(e)[0].decode("utf-8", "replace")
        declaradas += [urljoin(e, u) for u in re.findall(r"url\(([^)]+\.woff2)\)", texto)]
    declaradas = [u.strip("'\"") for u in dict.fromkeys(declaradas)]
    sobran = [u for u in declaradas if u not in fuentes_pre]
    if declaradas:
        print(f"\nFuentes declaradas en el CSS: {len(declaradas)} archivos, "
              f"{len(fuentes_pre)} precargados, {len(sobran)} solo si se usan")

    otras = [(como, u) for como, u in precargas if como != "font"]
    if otras:
        print("\nOtras precargas: " + ", ".join(f"{como}:{u.rsplit('/', 1)[-1][:30]}" for como, u in otras))

    total_gz = js[1] + css[1] + fu[1] + len(gzip.compress(cuerpo))
    print(f"\nHTML + JS + CSS + fuentes precargadas: {kb(total_gz).strip()} KB gzip\n")


if __name__ == "__main__":
    main()
