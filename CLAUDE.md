# Claude Code Instructions

@AGENTS.md

Read the shared instructions above. For full delivery coordination, start the
main session with `claude --agent orchestrator`. Do not launch the coordinator as
a nested worker when main-session delegation is required. Specialists live in
.claude/agents/ and load their canonical roles from agent-system/roles/.

For direct questions, answer without launching an implementation pipeline.
Do not invent project context, a stack or test commands from this template.