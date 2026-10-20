// Pegar en `javascript_tool` de Claude in Chrome anteponiendo `await `, o
// pasar con `--eval "$(cat medir-pagina.js)"` a browser-automation.
//
// Devuelve lo que la página bajó de verdad en ESTE navegador: fuentes,
// imágenes (con el ancho que eligió el srcset), JS, CSS y total, más el LCP
// y las precargas. Baja la página entera antes de contar, para que se pidan
// las imágenes diferidas.
//
// Se cuenta `encodedBodySize` y no `transferSize`: el segundo es 0 cuando el
// recurso sale de la caché del navegador, y entonces antes/después no se
// podrían comparar. Un 0 en `encodedBodySize` es un recurso de otro dominio
// sin Timing-Allow-Origin (YouTube, Google Maps): no se puede pesar desde acá.
//
// Nada de lo que devuelve lleva query string: la extensión de Chrome tapa con
// "[BLOCKED: Cookie/query string data]" cualquier texto que la tenga, así que
// el archivo y el ancho de cada imagen van en campos separados.
(async () => {
  if (document.readyState !== "complete")
    await new Promise((r) => addEventListener("load", r, { once: true }));
  await new Promise((r) => setTimeout(r, 1500));

  const lcp = await new Promise((r) => {
    new PerformanceObserver((l) => {
      const e = l.getEntries();
      r(e[e.length - 1]);
    }).observe({ type: "largest-contentful-paint", buffered: true });
    setTimeout(() => r(null), 800);
  });

  for (let y = 0; y < document.body.scrollHeight; y += 600) {
    scrollTo(0, y);
    await new Promise((r) => setTimeout(r, 150));
  }
  await new Promise((r) => setTimeout(r, 2500));
  scrollTo(0, 0);

  const res = performance.getEntriesByType("resource");
  const kb = (n) => Math.round(n / 102.4) / 10;
  const suma = (a) => kb(a.reduce((s, x) => s + (x.encodedBodySize || 0), 0));
  const archivo = (u) => {
    try {
      const url = new URL(u);
      const original = url.searchParams.get("url");
      return (original ? decodeURIComponent(original) : url.pathname).split("/").pop();
    } catch {
      return "?";
    }
  };
  const ancho = (u) => {
    try {
      return new URL(u).searchParams.get("w");
    } catch {
      return null;
    }
  };
  const esImagen = (x) =>
    x.initiatorType === "img" ||
    /_next\/image|\.(jpe?g|png|webp|avif|gif|svg)(\?|$)/.test(x.name);

  return {
    pantalla: `${innerWidth}px · dpr ${devicePixelRatio}`,
    lcp: lcp && {
      ms: Math.round(lcp.startTime),
      elemento: lcp.element && (lcp.element.className || lcp.element.tagName),
      archivo: lcp.url ? archivo(lcp.url) : null,
    },
    fuentes: res
      .filter((x) => /\.(woff2?|ttf|otf)(\?|$)/.test(x.name))
      .map((x) => ({ archivo: archivo(x.name).slice(0, 24), kb: kb(x.encodedBodySize) })),
    imagenes: res
      .filter(esImagen)
      .map((x) => ({ archivo: archivo(x.name), ancho: ancho(x.name), kb: kb(x.encodedBodySize) })),
    fuentesKB: suma(res.filter((x) => /\.(woff2?|ttf|otf)(\?|$)/.test(x.name))),
    imagenesKB: suma(res.filter(esImagen)),
    jsKB: suma(res.filter((x) => /\.m?js(\?|$)/.test(x.name))),
    cssKB: suma(res.filter((x) => /\.css(\?|$)/.test(x.name))),
    totalKB: suma(res),
    precargas: [...document.querySelectorAll("link[rel=preload]")].map(
      (l) => `${l.as}:${archivo(l.href).slice(0, 24)}`,
    ),
  };
})()
