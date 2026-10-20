#!/usr/bin/env node
/**
 * Antes de activar AVIF (o de bajar la calidad), mirá si se nota.
 *
 *   node comparar-formatos.mjs public/banner.jpg --ancho 828 --recorte 100,330,640,60
 *
 * Codifica la imagen como lo hace el optimizador de Next —WebP a la calidad
 * dada (75 por defecto) y AVIF a calidad × 50/80 con effort 3—, imprime los
 * pesos y arma dos PNG: las dos versiones completas una encima de la otra, y
 * el mismo recorte de cada una ampliado ×2. Arriba WebP, abajo AVIF.
 *
 * La equivalencia de calidad está en node_modules/next/dist/server/
 * image-optimizer.js; si una versión nueva de Next la cambia, cambiala acá.
 *
 * Usa el `sharp` del proyecto (Next lo trae): correlo desde la raíz del repo.
 */
import { createRequire } from "node:module";
import { statSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";

const require = createRequire(path.join(process.cwd(), "x.js"));
let sharp;
try {
  sharp = require("sharp");
} catch {
  console.error(
    `No encuentro sharp desde ${process.cwd()}. Corré esto desde la raíz de un ` +
      "proyecto con Next, o instalalo con `npm i -D sharp`.",
  );
  process.exit(1);
}

const args = process.argv.slice(2);
const opcion = (n, d) => {
  const i = args.indexOf(`--${n}`);
  return i >= 0 ? args[i + 1] : d;
};
const imagen = args.find((a, i) => !a.startsWith("--") && !args[i - 1]?.startsWith("--"));
if (!imagen) {
  console.error("Uso: comparar-formatos.mjs <imagen> [--ancho 828] [--calidad 75] [--recorte x,y,w,h] [--salida dir]");
  process.exit(1);
}
const ancho = Number(opcion("ancho", 828));
const calidad = Number(opcion("calidad", 75));
const recorte = opcion("recorte")?.split(",").map(Number);
const salida = opcion("salida", path.join(tmpdir(), "comparar-formatos"));
mkdirSync(salida, { recursive: true });

const base = sharp(imagen).resize(ancho, undefined, { withoutEnlargement: true });
const webp = await base.clone().webp({ quality: calidad }).toBuffer();
const avif = await base
  .clone()
  .avif({ quality: Math.max(Math.round(calidad * (50 / 80)), 1), effort: 3 })
  .toBuffer();

const k = (n) => `${(n / 1024).toFixed(1)} KB`;
console.log(`original  ${k(statSync(imagen).size)}  (${path.basename(imagen)})`);
console.log(`webp q${calidad}  ${k(webp.length)}`);
console.log(
  `avif      ${k(avif.length)}  ${Math.round(100 - (avif.length / webp.length) * 100)}% menos que webp`,
);

const separador = 10;
const apilar = async (a, b, archivo) => {
  const [ma, mb] = await Promise.all([sharp(a).metadata(), sharp(b).metadata()]);
  await sharp({
    create: {
      width: Math.max(ma.width, mb.width),
      height: ma.height + separador + mb.height,
      channels: 3,
      background: "#ff0000",
    },
  })
    .composite([
      { input: await sharp(a).png().toBuffer(), top: 0, left: 0 },
      { input: await sharp(b).png().toBuffer(), top: ma.height + separador, left: 0 },
    ])
    .png()
    .toFile(archivo);
  return archivo;
};

console.log(`\ncompleto: ${await apilar(webp, avif, path.join(salida, "completo.png"))}`);

if (recorte) {
  const [left, top, width, height] = recorte;
  const ampliar = (buf) =>
    sharp(buf).extract({ left, top, width, height }).resize(width * 2).png().toBuffer();
  const archivo = path.join(salida, "recorte.png");
  await apilar(await ampliar(webp), await ampliar(avif), archivo);
  console.log(`recorte:  ${archivo}`);
} else {
  console.log("Sin --recorte: si la imagen trae texto, recortá esa zona y ampliala.");
}
console.log("Arriba WebP, abajo AVIF. Leé los PNG para mirarlos.");
