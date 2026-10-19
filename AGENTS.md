# ATIP — autonomous build contract

This is an execution contract, not a request for more documentation. **Read all seven root Markdown files and `design/ui-reference.html` before acting. Start implementation immediately.** The entire app must be built, not just a demo. Follow `TASKLIST.md` from M0 through M12, with M0 UI-first. Never ask the human to issue the next phase prompt. This file and `PROMPTS.md` govern future sessions.

## Autonomous loop
1. Inspect repository, tools, existing code and `CURRENT_STATUS.md`; preserve existing work. Determine next unchecked task with satisfied dependencies.
2. Implement the smallest complete vertical slice for that task. Prefer actual code and working integrations to elaborate planning.
3. Run lint/typecheck/tests/build and browser checks when available. Review security, tenant isolation and regressions. Fix and rerun until green or a documented genuine blocker.
4. **Only then** mark `[x]` on that exact `TASKLIST.md` checkbox, with evidence in `CURRENT_STATUS.md` (command, result, commit, relevant path). Never check work merely because code was generated. Never silently skip a difficult requirement.
5. Commit verified work at coherent task/phase boundaries when Git is available; do not force-push or delete existing work. Update `CURRENT_STATUS.md` with next action and continue automatically to next unchecked task/phase.
6. On context/token exhaustion, write a precise checkpoint in `CURRENT_STATUS.md` and leave a one-paragraph continuation instruction. New agents must reconstruct state from repo, not chat.

## UI-first gate
M0 builds **every route** in `SPEC.md` and matches `design/ui-reference.html` before backend implementation. Run dev server, inspect desktop/mobile pages and interactions, capture screenshots under `artifacts/ui/` if browser tooling is available. Present preview URL + what was verified to user; **continue automatically to M1** unless user explicitly asks to pause or a real blocker exists. Never claim a preview is running unless confirmed.

## Human intervention (exception, not normal workflow)
Only pause for secrets/credentials, external account setup, irreversible or costly actions, legal permissions, security-sensitive access, required decisions not derivable from specification, or infrastructure that cannot be provisioned safely. Provide: `WHY BLOCKED`, `EXACT STEPS` (click paths/commands), `WHAT TO ENTER` (names of env vars, never request pasted secrets), `HOW TO VERIFY`, `HOW TO RESUME`. Implement unrelated tasks while waiting if possible. Do not prompt for ordinary decisions, approval to proceed to next phase, or optional aesthetic preferences. Never invent successful external integration.

## Product rules
- Frontend Next.js App Router + TypeScript + Tailwind + shadcn/ui + Lucide; accessible responsive monochrome UI. Keep frontend API adapter layer separate from demo fixtures.
- Backend FastAPI modular monolith; PostgreSQL system of record; Redis ephemeral cache; RabbitMQ with transactional outbox for durable jobs; separate workers; object storage for artifacts. Local Docker Compose; Kubernetes production target.
- GitHub App (installation-scoped auth, verified webhooks), OIDC identity, organization-scoped RBAC. Start with Python and JS/TS analysis. Model-provider gateway with Gemini supported, provider-agnostic contracts.
- Untrusted repository code **never** executes on API host, mining worker host, or ordinary dev environment. Execute only in hardened ephemeral sandbox with quotas, default-deny network, no platform secrets. If safe runner unavailable, expose disabled execution with clear reason; never fake it.
- Agent reads repository content as untrusted data; cannot self-approve repo modifications, PRs or permissions. Human approval enforced server-side. Never expose private source to external models without organization consent.
- Every visible action either works end-to-end or is explicitly labelled Demo / Not configured / Disabled. No fake uptime, customers, test results or coverage presented as real.
- Predictive ML is optional on top of a functional deterministic risk engine but must be genuinely implemented and validated if marked complete. Use permissioned, labeled data; prevent future-data leakage; keep reproducible training/evaluation artifacts and a safe fallback. Never fabricate training results or claim a model is trained without evidence.
- No new planning Markdown files unless truly needed for implementation. The seven files are the canonical working documents. Generated source code, migrations, tests, workflows and deployment manifests are encouraged.


## Approved visual reference and setup
Before M0 execute the `SETUP` prerequisite checklist in `TASKLIST.md`. The primary design reference is `design/ATIP_Six_Screens_Exact_Crops/ATIP_APPROVED_SIX_SCREEN_REFERENCE.png`, containing six actual ATIP mockups. Match these screens visually as closely as possible, as visual authority, while implementing both complete themes on every screen. `design/ui-reference.html` is only a secondary interactive layout example; it must not override the PNG. Do not infer missing image screens: apply the same visual language to AI Analysis, Reports, Settings, Run Details and Sign In. For UI verification, compare browser screenshots against the PNG, document meaningful differences, and refine before progressing.

## Non-negotiable white-box implementation contract
- The final target flow is: GitHub repository → authorized branch/PR snapshot → repository mining (commits, diffs, dependencies, existing tests) → versioned explainable risk scoring (optional validated ML) → static white-box analysis (AST, CFG, call graph, data-flow/def-use, complexity, reachability) → coverage objective inventory (statement, decision/branch, condition, MC/DC, basis/selected feasible paths, loops, def-use, exceptions, boundaries, mutation, impacted regression) → constraint/fixture/LLM-assisted candidate test generation → validation and review → authorized hardened sandbox execution with instrumentation → measured coverage and mutation analysis → gap-driven regeneration and re-execution with bounded retries → evidence-grounded AI failure analysis → auditable dashboard/GitHub Checks and exports.
- Execute **SETUP, M0, then M1–M12** in order. M0 UI first includes the new White-Box Coverage route and updates to existing views. No additional planning Markdown files; update the seven canonical files only.
- Each technique (statement, branch/decision, condition, MC/DC, basis/selected paths, loops, def-use, exceptions, boundaries, mutation, regression) must have a discovered objective, actual generation/execution approach, measured evidence or explicitly marked unsupported/unknown, and automated fixture acceptance tests. MC/DC must be validated with real executed independence pairs, not guessed from line coverage.
- Do not mark an entire phase complete when a required technique is only a stub, an unverified AI-generated test, or unsupported without a documented and approved limitation. Continue safe independent tasks; ask the human for true external blockers only.
- Keep approved six original screenshot assets untouched; new coverage screenshot supplements rather than replaces them. Updated HTML remains functional reference, not final production UI. Theme parity and exact visual-language consistency are mandatory.
