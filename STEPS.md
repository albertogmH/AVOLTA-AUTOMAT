# Empezar Un Proyecto

1. Copia `AGENTS.md`, `agent-system/` y el adaptador elegido a la raiz.
    Para Claude Code, incluye `CLAUDE.md`. Conserva las rutas e integra
    las instrucciones existentes sin sobrescribirlas.
2. Aporta o completa el contexto en
   [agent-system/templates/project-context.md](agent-system/templates/project-context.md) con hechos confirmados.
   No tienes que rellenar task.md.
3. Abre la raiz del proyecto y arranca el coordinador:

- **Copilot / VS Code:** elige el harness Copilot y el agente `orchestrator`.
- **Claude Code:** ejecuta `claude --agent orchestrator` desde la raiz del proyecto.
- **Cursor:** pide al Agent principal que lea
  [agent-system/roles/orchestrator.md](agent-system/roles/orchestrator.md) y coordine los especialistas.

## Peticion

```text
Implementa [X] usando el contexto del proyecto y agent-system/workflows/feature-delivery.md;
coordina los especialistas necesarios y reporta resultados/bloqueos.
```

## Rutas

- **Direct:** preguntas, sin proceso de entrega ni archivos de tareas.
- **Minimal:** mecanica/documentacion sin comportamiento, riesgo ni dudas:
  Developer, comprobacion concreta e inspeccion del coordinador.
- **Light:** comportamiento acotado de bajo riesgo: plan breve, Developer,
  QA independiente (Tester) y Reviewer.
- **Standard:** complejidad o dudas de diseno: anade Planner a Light.
- **Sensitive:** Developer, Tester, Security Auditor y Reviewer, tambien ante
  dudas de seguridad. Planner solo si la complejidad o incertidumbre lo requiere.

Politicas, seguridad, permisos, seleccion de agentes y configuracion ejecutable
no son Minimal por ser Markdown o cambios pequenos. Consulta las condiciones del
[flujo completo](agent-system/workflows/feature-delivery.md). Prevalecen los controles del proyecto
y del usuario. Si falta un control obligatorio: BLOCKED, no N/A.
Prueba la invocacion nativa real, lectura, ejecucion y delegacion en tu cliente;
no se garantiza soporte nativo ni se instala nada globalmente.