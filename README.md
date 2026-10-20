# claude-skills

Skills personales para [Claude Code](https://claude.com/claude-code) — recetas y flujos que reuso en mis proyectos.

Cada carpeta es una skill: un `SKILL.md` (con frontmatter `name` + `description`) más archivos de apoyo (`templates/`, `references/`). Se instalan copiándolas a `~/.claude/skills/` y se invocan con `/<nombre>`.

## Skills

- **[`adversarial/`](./adversarial)** — Loop de revisión adversarial *cross-vendor*. Después de construir un cambio, dispara agentes de coding de otros labs (OpenAI **Codex** + Moonshot **Kimi**) en modo headless a "romperlo", arbitra sus hallazgos contra el código real (verifica, deduplica, descarta falsos positivos), los presenta para aprobación, y arregla + re-testea. La diversidad de proveedor caza bugs que una revisión de la misma familia se pierde. Requiere los CLIs `codex` y `kimi` instalados y autenticados.
- **[`bot-dashboard/`](./bot-dashboard)** — Receta y convenciones para dashboards de monitoreo de bots de WhatsApp sobre Supabase/Postgres con Streamlit: capa de datos, factory de charts, KPIs, estilo y gotchas.
- **[`rendimiento-web/`](./rendimiento-web)** — Auditoría de rendimiento web (sobre todo Next.js en Vercel) que mide antes de tocar, compara bytes de producción contra el build local en el navegador real, mira lado a lado antes de cambiar un formato de imagen o fuente, y entrega un informe que dice también qué se revisó y **no** se tocó, y por qué. Trae scripts para pesar una página (JS, CSS, fuentes, precargas y caché), medirla dentro de Chrome y comparar WebP contra AVIF como los codifica Next.

## Instalación

```bash
git clone https://github.com/Rodato/claude-skills.git
cp -r claude-skills/adversarial ~/.claude/skills/
# luego: /adversarial en Claude Code
```

---
Daniel Otero · [danielotero.dev](https://danielotero.dev)
