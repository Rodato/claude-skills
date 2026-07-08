---
name: adversarial
description: Cross-vendor adversarial review loop. After building a change, invoke external coding-agent CLIs (Codex + Kimi) headless as adversarial reviewers, arbitrate their findings against the real code (verify, dedupe, drop false positives), present them for approval, then fix and re-test. Use when the user wants an independent "try to break it" review of a diff or a codebase from models OUTSIDE the Claude family. Requires the `codex` and `kimi` CLIs installed and authenticated.
---

# Loop de revisión adversarial (cross-vendor)

**Claude Code construye → agentes externos (Codex + Kimi) lo rompen → arbitro → vos aprobás → arreglo → re-testeo.**

El valor está en la **diversidad de proveedor**: modelos de labs distintos (OpenAI Codex, Moonshot Kimi) comparten menos puntos ciegos con Claude que una revisión Claude-sobre-Claude, así que cazan bugs que una revisión de la misma familia se pierde. El arbitraje + el gate humano mantienen afuera los hallazgos plausibles-pero-falsos.

## Cuándo usarla
Cuando se quiere una revisión independiente "rompé esto" de un diff o un repo, hecha por modelos fuera de la familia Claude: antes de publicar, tras un cambio no-trivial, o para chequear una zona riesgosa.

## Prerrequisitos
Dos CLIs de agentes de coding, instalados y autenticados (loguean por su propio flow; no hacen falta API keys en el env):
- `codex` (OpenAI Codex CLI) — chequear: `command -v codex && codex --version`
- `kimi` (Moonshot Kimi Code CLI) — chequear: `command -v kimi && kimi --version`

Si falta uno, decirlo y correr con el que haya.

## El loop
1. **Elegir el objetivo**: el `git diff` pendiente; si está limpio, los archivos núcleo donde vive la correctitud (métricas, pipeline de datos, storage), no todo el repo a lo bruto.
2. **Correr ambos revisores en paralelo, headless, solo-lectura** (ver Invocación). Solo REPORTAN — no editan.
3. **Arbitrar** (este es el paso que sostiene todo — NO relayear hallazgos a ciegas):
   - Verificar cada hallazgo contra el código real. Descartar los plausibles-pero-falsos (los revisores adversariales inventan; ese es el trabajo del árbitro).
   - Deduplicar entre los dos. Un hallazgo que ambos marcan de forma independiente es de **mayor confianza** (acuerdo cross-vendor).
   - Ordenar por severidad + reproducibilidad.
4. **Presentar** el set arbitrado, agrupado: bugs claros / decisión de dominio / baja prioridad. **Siempre preguntar cuáles arreglar** — nunca auto-aplicar.
5. **Aplicar** los aprobados (Claude Code es el ÚNICO que escribe).
6. **Re-testear**: re-correr los revisores sobre el código arreglado. Si nada nuevo sobrevive el arbitraje, listo.

## Invocación (en background y en paralelo — una review real tarda minutos)
Completar `<DIR>` (ruta absoluta del repo) y escribir el prompt del revisor a un archivo primero (ver `templates/reviewer_prompt.md`; agregarle el contexto de dominio del proyecto para que no marque decisiones de diseño intencionales como bugs).

**Codex** — subcomando no-interactivo, sandbox de solo-lectura, captura el mensaje final:
```bash
codex exec -C "<DIR>" -s read-only "$(cat reviewer_prompt.txt)" -o codex_findings.json
```

**Kimi** — un prompt no-interactivo:
```bash
kimi -p "$(cat reviewer_prompt.txt)" --add-dir "<DIR>" --output-format text > kimi_findings.json
```

Lanzar los dos con `run_in_background: true`. **NO** usar `codex apply` ni `kimi --yolo`: esos los dejan editar, y todo el punto es que **el único que escribe sea Claude Code**.

## Esquema de hallazgos
Pedirles que devuelvan SOLO un array JSON, sin prosa ni fences de código:
```json
[{"file": "ruta", "line": 0, "severity": "alta|media|baja", "claim": "qué está mal y por qué", "repro": "cómo se dispara"}]
```

## Principios
- **Un solo escritor**: los revisores reportan; Claude Code arregla. Nunca tres agentes editando el mismo árbol.
- **Gate humano**: presentar, después preguntar. Para decisiones de dominio, que decida el usuario; para llamadas técnicas difíciles, escalar a un árbitro más fuerte (p. ej. Opus → Fable).
- **Respetar el diseño intencional**: los revisores leen el `CLAUDE.md`/`AGENTS.md` del repo solos — decirles en el prompt que respeten lo documentado como intencional para no reportarlo como bug.
- **Loop hasta seco**: no se "avanza" hasta que un ciclo de re-test no produce nada nuevo que sobreviva el arbitraje.
