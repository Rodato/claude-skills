---
name: plan-validate
description: Cross-vendor design-validation loop. Before writing any code for a non-trivial change, invoke external coding-agent CLIs (Codex + Kimi) headless as independent design reviewers to critique a PROPOSED PLAN — not to hunt bugs in existing code, but to stress-test the approach itself (soundness, hidden risks, missed edge cases, simpler alternatives) before it becomes code. Use when the user wants a plan validated by models OUTSIDE the Claude family before implementation starts. Sibling to the `adversarial` skill (same cross-vendor infrastructure), applied one phase earlier — to the design, not the diff. Requires the `codex` and `kimi` CLIs installed and authenticated.
---

# Loop de validación de planes (cross-vendor)

**Claude Code redacta un plan → agentes externos (Codex + Kimi) lo cuestionan → arbitro → refino el plan → (si cambió mucho) re-valido → vos aprobás → recién ahí se escribe código.**

Es el mismo valor que `adversarial` (diversidad de proveedor: menos puntos ciegos compartidos con Claude) pero aplicado UNA FASE ANTES — al **diseño**, no al código. El objetivo no es "romper la implementación" (todavía no existe): es contestar "¿este es un buen enfoque, o hay un riesgo, un caso no contemplado, o una forma más simple de lograr lo mismo que se nos está escapando?".

## Cuándo usarla
Cuando el usuario pide explícitamente validar un plan/diseño antes de implementar — típicamente para cambios no triviales, arquitectónicamente sensibles, o donde ya se descartó una solución más simple (parche) a favor de "algo robusto" y se quiere confirmar que el reemplazo elegido realmente lo es. NO es para revisar código ya escrito — para eso está `adversarial`.

## Prerrequisitos
Mismos que `adversarial`:
- `codex` (OpenAI Codex CLI) — chequear: `command -v codex && codex --version`
- `kimi` (Moonshot Kimi Code CLI) — chequear: `command -v kimi && kimi --version`

Si falta uno, decirlo y correr con el que haya.

## El loop
1. **Redactar el plan** en un archivo aparte (no solo en la conversación) — objetivo, diseño propuesto, alternativas descartadas y por qué, riesgos ya identificados. Un plan que no se puede escribir claro tampoco se puede validar bien.
2. **Correr ambos validadores en paralelo, headless, solo-lectura** (ver Invocación). Se les da el plan + acceso de lectura al repo (para que puedan chequear contra el código real qué tan factible/consistente es el plan con lo que ya existe). Solo CRITICAN — no escriben plan ni código.
3. **Arbitrar** (igual de importante que en `adversarial` — no relayear críticas a ciegas):
   - Verificar cada crítica contra el código/arquitectura real — un validador puede asumir que algo no existe cuando sí existe, o al revés.
   - Deduplicar entre los dos. Una crítica que ambos marcan de forma independiente pesa más (acuerdo cross-vendor).
   - Separar: riesgos reales del enfoque / alternativas mejores genuinas / decisiones de producto que le tocan al usuario / ruido.
4. **Refinar el plan** incorporando lo que sobrevive el arbitraje. Si el plan cambió sustancialmente (no un ajuste menor), repetir el paso 2 una vez más sobre la versión nueva — igual que `adversarial` reitera hasta que un ciclo no trae nada nuevo.
5. **Presentar** el plan ya validado al usuario, agrupado igual que en `adversarial`: ajustes ya incorporados / decisiones que le tocan a él / riesgos residuales aceptados a sabiendas. Recién con su aprobación se pasa a implementar (ahí sí, potencialmente seguido de `adversarial` sobre el código resultante).

## Invocación (en background y en paralelo)
Igual mecánica que `adversarial`. Escribir el prompt del validador a un archivo primero (ver `templates/validator_prompt.md`), pegándole el plan completo y el contexto de dominio necesario para que puedan juzgar factibilidad real, no solo la prosa del plan.

**Codex**:
```bash
codex exec -C "<DIR>" -s read-only "$(cat validator_prompt.txt)" -o codex_validation.json
```

**Kimi**:
```bash
kimi -p "$(cat validator_prompt.txt)" --add-dir "<DIR>" --output-format text > kimi_validation.json
```

Lanzar los dos con `run_in_background: true`. **NO** usar `codex apply` ni `kimi --yolo` — no hay nada que aplicar todavía, son solo críticas de diseño.

## Esquema de hallazgos
Pedirles que devuelvan SOLO un array JSON, sin prosa ni fences de código. A diferencia de `adversarial` (que reporta bugs), acá cada item es una CRÍTICA DE DISEÑO:
```json
[{"category": "riesgo|alternativa|caso-no-contemplado|supuesto-invalido|decision-de-producto", "severity": "alta|media|baja", "claim": "qué parte del plan es cuestionable y por qué", "suggestion": "qué harían distinto, si algo"}]
```

## Principios
- **Un solo escritor**: los validadores critican; Claude Code redacta y ajusta el plan. Nunca dejar que un CLI externo reescriba el plan directamente.
- **Gate humano**: presentar el plan ya arbitrado, después preguntar — igual que en `adversarial`. Para decisiones de producto (tradeoffs, alcance), que decida el usuario.
- **Respetar el contexto ya decidido**: si el usuario ya descartó explícitamente una alternativa (p. ej. "no quiero parches"), decírselo a los validadores para que no la reproduzcan como sugerencia — están para validar el rumbo elegido, no para reabrir decisiones ya tomadas, salvo que encuentren un riesgo concreto que la vuelva insostenible (en ese caso, sí escalarlo).
- **No implementar todavía**: esta skill termina en un plan aprobado por el usuario, no en código. La implementación es un paso aparte, posterior.
- **Loop hasta que el plan deje de cambiar sustancialmente**: si una ronda de validación solo trae ajustes menores o nada nuevo, el plan está listo para presentar.
