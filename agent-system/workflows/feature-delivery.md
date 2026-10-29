# General Delivery Workflow

This is a portable behavioral workflow, not executable automation. Native host
tools perform delegation and execution. There is no database, scheduler, polling,
custom runtime or dependency installation in this template.

## 1. Choose The Route

| Route | When | Specialists |
| --- | --- | --- |
| Direct | Questions or read-only analysis | Main-session answer; no pipeline or task files |
| Minimal | Demonstrably non-behavioral, mechanical/docs work meeting all conditions below | One Developer assignment, focused validation, coordinator final inspection |
| Light | Scoped, low-risk behavioral change with clear criteria | Developer, Tester, Reviewer; inline plan |
| Standard | Complex work or design uncertainty | Planner, Developer, Tester, Reviewer |
| Sensitive | Auth, permissions, sessions, personal data, payments, trust boundaries, dependencies or infrastructure; uncertain security relevance | Developer, Tester, Security Auditor, Reviewer; Planner only for complexity/uncertainty that warrants planning |

Minimal requires no change to behavior, public contracts, data, dependencies,
CI/deployment or sensitive configuration, and no unresolved uncertainty. Security,
policy, permission, agent-routing and executable configuration changes are not
Minimal merely because they are Markdown or few lines. Risk and scope, not file
count, determine the route. Minimal has no independent Planner, QA, auditor or
Reviewer by default; the coordinator's inspection is not independent approval.

Record one brief coordinator line: route and reason; required checks; required
specialists and justified N/A for optional specialists. User/project mandatory
validation and reviews override route minima. A blanket QA waiver cannot exempt
behavioral tasks. Missing execution or delegation for a required gate is BLOCKED,
never N/A or fabricated success. Never downgrade a route to escape a failed gate
or skip required security review when security relevance is uncertain.

## 2. Establish Context

The user supplies the goal and available project context, not completed task
forms. Read applicable instructions and relevant context once. For a new project,
the coordinator records confirmed facts using
[the context template](../templates/project-context.md) when useful. Do not assume
Node, Python, commands, services or CI. Ask only about blocking decisions.

Inspect the working tree and identify user changes; disclose a missing Git baseline
without initializing Git. Define a concise goal, non-goals, acceptance criteria,
risks and actual validation commands before implementation. Stop and reassess
before expanding an assigned interface, module or dependency. The coordinator may
adjust the task breakdown within user scope; expanding user scope needs permission.
Avoid adjacent cleanup, refactors and gold-plating. Reassess the route on new facts
without automatically restarting the whole pipeline.

## 3. Prepare And Assign Tasks

The coordinator alone maintains an authoritative list for implementation. Use a
tiny inline context packet; [the task contract](../templates/task.md) is a coordinator
aid, not a user prerequisite or mandatory form. Persist Markdown only when a longer
job needs resumption. Direct answers require neither tasks nor a pipeline.
No task database or special CLI is required.

Track: ready -> active -> review -> done; blocked can interrupt any unfinished stage.
Each task has one owner, explicit files, dependencies and acceptance checks.
Assign active before invoking its worker. Reassignment requires checking the
previous worker stopped and inspecting partial changes. Never silently steal work.

Define shared contracts first. Do not dispatch dependent tasks until prerequisites
are implemented and verified sufficiently for that dependency. Implementation
readiness is not a final delivery approval. Keep one coherent assignment when
splitting costs more than it helps; do not fragment work into artificial tiny tasks.

## 4. Delegate Efficiently

- Default to sequential work; at most two concurrent bounded, independent workers,
  with one writer per checkout.
- Parallelize independent read-only work when it reduces elapsed time. Do not
  launch multiple agents to answer the same question or repeat the same search.
- Any separately authorized parallel writers need isolation and an integration order.
  Separate worktrees do not automatically share task state. Do not create branches
  or commits without authorization just to enable parallelism.
- Send task ID, goal, criteria, file ownership, dependencies/interfaces, relevant
  anchors, baseline user changes, check commands and expected output.
- Send applicable safety/project instructions when they are not inherited. Avoid
  forwarding entire conversations, unrelated files or full previous reports.
- Workers return changed files, results, findings and blockers, ideally in 300
  words or fewer. Important evidence takes precedence over that soft target.
- Do not allow recursive worker delegation. Reuse an existing worker session for
  small follow-ups when supported; otherwise send the delta and necessary context.

## 5. Integrate And Freeze

Inspect actual changes and untracked files. Check criteria, scope, user changes,
secrets and integration contracts. Address conflicts carefully without destructive
Git operations. Stop writers before validation; do not review a moving target.

Record which content was checked: commit plus working-tree diff when available,
or the relevant files and validation time when no Git baseline exists. This is
traceability, not cryptographic attestation.

## 6. Validate Independently

Apply the selected route and any mandatory project/user gates:

1. Run required checks after the final relevant changes and final integration checks
  when applicable. Minimal still needs an actual focused check appropriate to the
  mechanical/docs change and coordinator final inspection, not an irrelevant app
  test suite. Missing scripts/tools are not passes.
2. For Light, Standard and Sensitive, Tester independently maps criteria to behavior
  and evidence, including negative paths, using targeted probes as needed. QA can
  request coordinator execution if its permissions prevent a command. Do not rerun
  identical checks on unchanged content/environment just because another role starts.
3. Security Auditor is required for Sensitive and whenever mandated by the project
  or user. Report scope and limitations. QA/security may inspect stable code in
  parallel, not compete for mutable resources.
4. For Light, Standard and Sensitive, Reviewer examines final changes, requirements
  and observed validation independently. For Minimal, the coordinator inspects the
  final changes and evidence; add independent specialists only if required.

Use the native delegation mechanism available in each host. If a REQUIRED gate
lacks delegation or execution, report BLOCKED. Optional specialists may be N/A
with the route-based reason. Sequentially simulating roles is not independent
approval. Do not claim a specialist ran unless its invocation actually occurred.

## 7. Remediate Without Loops

Return actionable defects to Developer with evidence and acceptance criteria.
Move the task back to active, invalidate affected approvals, then rerun the
affected required checks after the final correction. For behavioral routes,
refresh affected QA and final review; repeat required security review if its
content or assumptions changed. Minimal needs a fresh affected focused check and
coordinator inspection, plus any mandated gates. Preserve unaffected valid evidence.

Limit to two remediation cycles per task. Stop and escalate unresolved blockers,
uncertainty or missing tools instead of repeatedly exploring or weakening gates.
Resume interrupted work from task state and actual changes, not a fresh full plan.

## 8. Definition Of Done

- Acceptance criteria are met and all route/project/user required checks have
  actual successful results after final relevant changes.
- Minimal: focused validation passed and coordinator final inspection completed;
  any additionally mandated specialist gates are satisfied.
- Light, Standard, Sensitive: independent QA: PASS and Reviewer: APPROVE.
  Required Security Auditor: PASS WITH NOTES. Required Planner work is delivered.
- No unresolved blocking findings. REVIEW REQUIRED is not security approval.
- Required integration/regression checks ran after final integrated changes when
  applicable; valid unchanged evidence is reused, not mechanically rerun per role.
- Actual diff/new files were inspected and unexecuted checks are disclosed.

Only optional gates may be N/A with a reason; missing or failed required gates
remain BLOCKED. Documented exceptions do not turn unsatisfied gates into success.
Report partial or blocked delivery honestly. No automatic merge/deploy.

## Token And Model Policy

- Default to the selected host model; this template pins no provider or model ID.
- Use cheaper available models for routine bounded work only when configured and
  permitted by the user. Escalate reasoning for genuine uncertainty, not every task.
- Keep shared instructions short. Load a role's details when it is assigned.
- Plan once, investigate locally and avoid duplicated repository surveys.
- Run narrow checks while editing; reserve required full checks for integration.
- Reuse valid results and worker sessions when supported; send delta follow-ups.
  Refresh only affected evidence when content, environment or assumptions change.
- No blind retries of failed tool calls, endless polling or repeated summaries.
  A targeted retry is appropriate after its cause is resolved; otherwise report
  the blocker and specific missing capability. Two remediation cycles maximum.
- These are behavioral limits, not enforced token quotas. Every subagent consumes
  its own usage; model/billing controls remain in the host application.