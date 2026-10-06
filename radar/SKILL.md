---
name: radar
description: >-
  Corre el radar de contenido de Daniel: captura los timelines de X de la
  watchlist vía Apify, descarta lo ya visto y lo ya publicado, rankea los
  ángulos con un LLM y escribe el post del ángulo elegido usando la skill
  `posts`. Úsala cuando el pedido sea "corré el radar", "qué hay para postear",
  "buscame tema para un post", "armemos el post de hoy", o cuando Daniel pase un
  link de newsletter o artículo y quiera un post de ahí. El proyecto vive en
  ~/Dev/linkedin-radar.
---

# radar — de la fuente al borrador

Dos vías. Las dos terminan en un borrador escrito con la skill **`posts`**, que
es la que tiene la voz. Esta skill solo consigue y filtra la materia prima.

## Vía A — el radar de X

```bash
cd ~/Dev/linkedin-radar && .venv/bin/python -m radar
```

Ventana de 4 días por defecto. Si no sale nada nuevo, `--dias 7`. Si cambiaste
el criterio o `publicados.yaml`, `--rerank` re-puntúa sin volver a gastar Apify.

Sale una nota en `salidas/YYYY-MM-DD-radar.md` con los mejores ángulos, cada uno
con su score, el texto del tweet, el ángulo, y —esto es lo importante— una lista
de **qué verificar**.

Después:

1. Mostrale a Daniel los 3 o 4 mejores ángulos en una línea cada uno. No le
   pegues la nota entera.
2. Él escoge. Si no contesta y el contexto pide avanzar, tomá el de score más
   alto y decí cuál tomaste.
3. **Verificá contra la fuente primaria antes de escribir.** El tweet es materia
   prima, no fuente. Buscá el paper, el writeup, el post oficial. Esto no es
   opcional: la regla de evidencia de Daniel es que nunca se afirma algo que no
   esté medido, y un hilo de X resumiendo a otro no es una medición.
4. Escribí el post con `/posts`. **La cuenta de la watchlist nunca se menciona
   en el post.** Es el radar de Daniel, no la fuente: el crédito va a quien hizo
   el trabajo (el writeup, el paper, la empresa). La historia la cuenta él.
5. Cuando lo publique, agregá una línea a `publicados.yaml` para que el radar
   no se lo vuelva a ofrecer.

## Vía B — un link suelto

Daniel pasa un link de newsletter o de artículo. No hace falta correr nada:
leelo completo, sacá el detalle no obvio, y escribí con `/posts`. Igual aplica
el paso de verificación si el link es a su vez un resumen de otra cosa.

## Cadencia

La meta son 3 posts por semana. El radar aguanta correrse a diario, pero con una
sola cuenta en la watchlist la ventana de 4 días es lo que da material sin
repetir. Si empieza a salir vacío, el problema no es el radar: es que la
watchlist tiene una sola fuente.

## Lo que NO hace esta skill

- No publica en LinkedIn. El borrador se lo lleva Daniel.
- No decide sola qué se publica cuando hay alguien a quien preguntarle.
- No inventa cifras para rellenar. Si la verificación no cuadra, se dice y se
  pasa al siguiente ángulo.
