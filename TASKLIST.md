# ATIP — single authoritative 13-phase tasklist

**Rule:** The agent checks a box only after implementation **and** verification. Record proof in `CURRENT_STATUS.md`. Phases run automatically in order. SETUP must establish the local environment, then M0 must build and show UI first. External blockers do not justify fake completion.

## SETUP — prerequisite gate (before M0; not an additional development phase)

- [x] **SETUP-01** Inspect repository, installed Node/Python/Git/Docker tooling, permissions, and available ports; report actual versions and missing dependencies.
- [x] **SETUP-02** Initialize Git repository if needed, create `.gitignore`, workspace folders, reproducible package management, `.env.example` with no secrets, and documented local startup commands.
- [x] **SETUP-03** Check whether Node/npm or pnpm, Python/uv, and Docker are available; install safe local dependencies when permitted. If administrator rights, Docker Desktop initialization, account authorization, or credentials are needed, give exact Windows steps and continue unblocked work.
- [x] **SETUP-04** Verify the frontend can start locally; run initial lint/type/build smoke checks. Record evidence in `CURRENT_STATUS.md`. Proceed directly to M0 without asking permission.

**SETUP exit gate:** Workspace is reproducible, initial UI dev server starts, missing human-only dependencies are recorded with actionable instructions.

## M0 — UI FIRST: full usable frontend (including white-box coverage)

- [x] **M0-01** Bootstrap Next.js App Router, TS, Tailwind, shadcn/ui, Lucide, Figtree/Source Serif 4, formatting/typecheck/Playwright.
- [x] **M0-02** Implement exact monochrome light/dark tokens, responsive collapsible sidebar/topbar and reusable tables/forms/dialogs/toasts.
- [x] **M0-03** Build `/app` overview with demo-tagged stats, recent activity, CTA, loading/empty/error states.
- [x] **M0-04** Build `/app/repositories` and `/app/repositories/[id]` with working search/filter/sort, branch/tabs, dependency graph/list.
- [x] **M0-05** Build `/app/risk` with sortable scores, evidence detail drawer, filters and uncertainty states.
- [x] **M0-06** Build `/app/test-plans`, `/app/runs`, `/app/runs/[id]` with approval modal, execution status, logs and artifacts views (demo-tagged).
- [x] **M0-07** Build `/app/analysis`, `/app/reports`, `/app/settings` and `/sign-in` including all settings tabs and permission states.
- [x] **M0-08** Implement realistic local fixture adapter isolated from typed API client; no fake connected status; all controls have meaningful behavior.
- [x] **M0-09** Run UI dev server; visually inspect all routes at desktop/mobile and light/dark; fix defects; save screenshot evidence where tooling permits; report verified preview URL and continue autonomously.

- [x] **M0-WB-01** Add `/app/coverage` White-Box Coverage screen with objectives matrix, MC/DC proof pairs, mutation results, evidence/gaps and supported/unknown states, responsive light/dark and a screenshot matching the approved visual style.
- [x] **M0-WB-02** Add repository Coverage Objectives tab, Test Plans coverage-goals panel, Run Details instrumentation/mutation evidence, Reports coverage history; meaningful demo states and navigation.
- [x] **M0-WB-03** Verify updated `design/ui-reference.html`, new `design/whitebox-coverage-reference.png`, and all original six approved images as visual authority; inspect every route in both themes, desktop/mobile, without treating the demo as live functionality.

**Exit gate:** all checkboxes in this phase are verified; tests/build and security review pass; relevant UI works; status/commit updated.

---

## M1 — backend and local foundation

- [x] **M1-01** Scaffold FastAPI modular monolith, OpenAPI schemas, Python uv lock, lint/type/test.
- [x] **M1-02** Add Docker Compose PostgreSQL, Redis, RabbitMQ, MinIO-compatible store, health checks, .env.example.
- [x] **M1-03** Implement Alembic migrations and core organizations/users/memberships/repository/job entities.
- [x] **M1-04** Create versioned REST API envelopes, pagination, request IDs, validation, structured errors and SSE contract.
- [x] **M1-05** Add typed frontend API client and switch first Overview/Repositories views from demo fixtures to backend-backed empty states.
- [x] **M1-06** Add CI checks, API unit/integration tests, Compose smoke test and reproducible dev commands.

**Exit gate:** all checkboxes in this phase are verified; tests/build and security review pass; relevant UI works; status/commit updated.

---

## M2 — identity, organizations and GitHub

- [x] **M2-01** Implement OIDC login/session/logout/callback, protected routes and session expiry.
- [x] **M2-02** Implement org creation/selection, invitations/membership and Owner/Admin/Maintainer/Developer/Viewer RBAC.
- [x] **M2-03** Implement GitHub App install/callback, installation-scoped credentials and secure token storage.
- [x] **M2-04** Implement signed GitHub webhook verification, replay protection, delivery deduplication and durable ingestion.
- [x] **M2-05** Implement repository discovery/sync/branch/PR selectors with pagination and error handling.
- [x] **M2-06** Wire Repositories/Settings screens to real APIs; run permission/tenant and webhook tests.

**Exit gate:** all checkboxes in this phase are verified; tests/build and security review pass; relevant UI works; status/commit updated.

---

## M3 — repository mining and analysis

- [x] **M3-01** Create immutable commit-specific repository snapshots and safe repository fetch without executing repo scripts.
- [x] **M3-02** Extract commits, diffs, file changes, ownership and change-frequency evidence.
- [x] **M3-03** Implement Python + JS/TS import/dependency graph with parser fallback and provenance.
- [x] **M3-04** Compute basic complexity/static-analysis features; discover tests and ingest available coverage.
- [x] **M3-05** Implement analysis jobs, progress events, idempotency/retries and persisted results.
- [ ] **M3-06** Wire repository tabs/graph to real analysis data and validate against fixture repos.

**Exit gate:** all checkboxes in this phase are verified; tests/build and security review pass; relevant UI works; status/commit updated.

---

## M4 — risk and test intelligence

- [ ] **M4-01** Design and implement deterministic versioned risk model with explainable feature weights and missing-data handling.
- [ ] **M4-02** Implement change-impact and dependency propagation with bounded graph traversal.
- [ ] **M4-03** Implement risk ranking API, evidence drilldowns and confidence/provenance.
- [ ] **M4-04** Discover/select impacted regression tests; flag test gaps and possible flakiness based on evidence.
- [ ] **M4-05** Wire Risk screen and initial Test Plans to real results, with test cases for scores and edge conditions.
- [ ] **M4-06** Validate on known fixture commits, measure basic accuracy limitations and prevent fabricated claims.
- [ ] **M4-07** Specify supervised prediction target, labeling policy, permissible training sources, consent, prediction-time feature schema, and leakage threats; create reproducible dataset extraction with provenance, missing-label and class-imbalance handling.
- [ ] **M4-08** Assess actual labeled data quantity/quality and build time-based and repository-held-out train/validation/test splits; record immutable dataset manifest. If insufficient, mark ML training blocked/unvalidated while retaining functional deterministic risk scoring.
- [ ] **M4-09 — Multi-Model Benchmarking and Selection:** When sufficient trustworthy labeled data is available, train and compare **Logistic Regression, Random Forest, LightGBM, and XGBoost** as experimental defect-risk prediction candidates. Use the same validated prediction-time feature schema and leakage-resistant chronological/repository-held-out dataset splits for all candidates. Fit preprocessing and any imbalance handling exclusively on training data. Evaluate **PR-AUC (primary metric), precision, recall, F1-score, probability calibration, inference latency, and operational ranking metrics**. Compare all four models against the deterministic risk-scoring baseline. Tune hyperparameters and decision thresholds using training/validation data only; reserve held-out test data for final evaluation. Select a model based on demonstrated performance, calibration, reproducibility, and resource requirements—not algorithm popularity. Record comparative results, limitations, and selection rationale. Never fabricate metrics or deploy an unvalidated model.
- [ ] **M4-10** Version dataset/features/model artifacts and evaluation evidence; integrate optional inference with safe fallback, measured latency, and model-version provenance in risk API/UI.
- [ ] **M4-11 — Human Intervention Gate:** Automatically discover and evaluate suitable public software-defect datasets and repository sources. Before using any source requiring credentials, acceptance of licensing terms, payment, private repository access, or special permissions, provide the user with exact setup instructions. Never assume consent or fabricate access.
- [ ] **M4-12 — Training Environment Gate:** Automatically check CPU/GPU availability, memory, disk space, dependencies, and estimated training requirements. Use local resources when practical. If additional infrastructure or paid compute is genuinely necessary, explain the options and obtain approval before proceeding.
- [ ] **M4-13 — Dataset and Model Approval:** Record dataset sources, licensing, provenance, labeling confidence, evaluation results, and model limitations. Require explicit human approval before introducing private customer data into shared training or promoting a newly trained model to production. Do not require routine approval for permitted local experiments.
- [ ] **M4-14 — Blocker Handling:** If training cannot proceed because of unavailable datasets, missing permissions, insufficient labels, or resource limitations, record the exact blocker and actionable human instructions in `CURRENT_STATUS.md`. Continue independent work. Never mark training successful without actual evidence.


**Exit gate:** all checkboxes in this phase are verified; tests/build and security review pass; relevant UI works; status/commit updated.

---

## M5 — white-box static analysis and objective discovery

- [ ] **M5-01** Implement Python and JS/TS AST/CFG parser adapters with source spans, language version, diagnostics, bounded parsing and test fixture repositories.
- [ ] **M5-02** Build control-flow graph, bounded call graph, decision/atomic-condition decomposition, cyclomatic complexity and reachability inventory.
- [ ] **M5-03** Implement data-flow definition/use and kill/redefinition chains; loop nesting/entry/exit and exception-edge modeling.
- [ ] **M5-04** Discover statement, decision/branch, condition, MC/DC, basis-path, selected feasible path, loop, def-use, exception, boundary, mutation and regression objectives with stable SHA/source IDs.
- [ ] **M5-05** Build language/tool capability matrix, `UNKNOWN`/`UNSUPPORTED`/`PROVEN_INFEASIBLE` statuses, honest reachability proofs and evidence contracts; never equate static discovery with coverage.
- [ ] **M5-06** Persist objective records and expose tenant-scoped analysis/objective/gap APIs; validate Python and JS/TS nested Boolean/short-circuit, loop, exception, def-use fixtures.

**Exit gate:** All tasks verified with runnable fixture/integration evidence; unsupported capabilities disclosed and never misreported as covered; tests/build/security pass; status and Git commit updated.

---

## M6 — coverage-driven test planning and generation

- [ ] **M6-01** Implement plan lifecycle draft/review/approved/rejected, RBAC and explicit coverage goals per objective kind, with reviewable impacted-regression selection.
- [ ] **M6-02** Build deterministic boundary, decision, loop, exception, def-use and feasible path test candidate generation; constraint solving with bounded timeouts and infeasibility/unknown outcomes.
- [ ] **M6-03** Implement MC/DC unique-cause pairing logic and optional documented masking logic; plan true/false independence evidence, short-circuit semantics and instrumentation needs.
- [ ] **M6-04** Implement multi-provider LLM gateway (Gemini initial), typed contracts, optional AI-assisted test candidate generation, token/cost budgets and provider opt-in.
- [ ] **M6-05** Validate generated tests for syntax, assertions/oracles, relevant target, fixture isolation, duplicate elimination and prohibited side effects; no generated test counts as passed.
- [ ] **M6-06** Implement provider credential human gate: exact local secret/env setup instructions and connection checks; no API key in chat or Git; continue deterministic planning without provider.
- [ ] **M6-07** Wire Test Plans, repository Coverage Objectives and Coverage screen to real objectives/candidate evidence; fixture acceptance tests for every technique.

**Exit gate:** All tasks verified with runnable fixture/integration evidence; unsupported capabilities disclosed and never misreported as covered; tests/build/security pass; status and Git commit updated.

---

## M7 — secure execution and measured instrumentation

- [ ] **M7-01** Implement durable execution job lifecycle, transactional outbox, RabbitMQ retry/DLQ, cancellation, quotas and persisted events.
- [ ] **M7-02** Implement hardened isolated sandbox adapter; prohibit running repo/generated code on control-plane host; disable real execution if isolation unavailable and provide exact human steps.
- [ ] **M7-03** Implement Python and JS/TS statement and decision/branch instrumentation with source/test mapping and verified actual run observations.
- [ ] **M7-04** Implement condition-level instrumentation and MC/DC verifier requiring executed test pairs, observed atomic-condition vectors and decision outcomes; report short-circuit limitations.
- [ ] **M7-05** Implement bounded path/CFG edge traces, def-use observations, loop iteration evidence and exception-path coverage where feasible; mark unsupported capabilities explicitly.
- [ ] **M7-06** Collect logs, per-test outcomes, coverage artifacts, immutable provenance, timestamps, tool versions, source SHA, retries and timeouts.
- [ ] **M7-07** Wire Run Details and Coverage UI to real instrumentation and enforce tenant/approval/policy bypass tests; verify both Python and JS/TS fixtures.

**Exit gate:** All tasks verified with runnable fixture/integration evidence; unsupported capabilities disclosed and never misreported as covered; tests/build/security pass; status and Git commit updated.

---

## M8 — mutation, regression and iterative gap closure

- [ ] **M8-01** Implement reproducible mutation operator sets for supported Python and JS/TS code, isolated mutant runs and killed/survived/no-coverage/invalid/timeout/suspected-equivalent classification.
- [ ] **M8-02** Calculate defensible mutation score and disclose excluded/unknown mutants and equivalent-mutant limitations; preserve per-mutant evidence.
- [ ] **M8-03** Implement impact-based regression selection using diffs, dependency graph and existing suite, with baseline comparison and flakiness signals.
- [ ] **M8-04** Implement objective coverage aggregation with per-technique covered/uncovered/unknown/unsupported/proven-infeasible counts and denominators.
- [ ] **M8-05** Implement gap-driven deterministic and optional LLM test regeneration, sandbox re-execution, budget limits, fixed-point termination and traceable attempt history.
- [ ] **M8-06** Create automated acceptance fixtures for statement, branch, condition, MC/DC, basis/selected path, loop, def-use, exception, boundary, mutation and regression; validate genuine evidence rather than labels.
- [ ] **M8-07** Wire coverage matrix, gaps and mutation results into UI, reports and authorized export; performance and abuse tests.

**Exit gate:** All tasks verified with runnable fixture/integration evidence; unsupported capabilities disclosed and never misreported as covered; tests/build/security pass; status and Git commit updated.

---

## M9 — AI failure analysis and reviewable remediation

- [ ] **M9-01** Implement grounded failure triage from actual run logs, stack traces, code diffs, coverage gaps and mutant evidence; distinguish hypothesis from confirmed facts.
- [ ] **M9-02** Implement governed LLM workflows with typed tools, citations, model/provider/version and cost, timeouts, redaction, prompt-injection protections and consent boundaries.
- [ ] **M9-03** Generate optional reviewable test/patch/PR suggestions with strict human approval and no silent repository writes.
- [ ] **M9-04** Wire AI Analysis and Run Details to real agent state and audit history; no fabricated diagnoses or successful executions.
- [ ] **M9-05** Run curated failure fixtures, provider/model comparison and evaluation for groundedness, test usefulness, duplicate rate and security.

**Exit gate:** All tasks verified with runnable fixture/integration evidence; unsupported capabilities disclosed and never misreported as covered; tests/build/security pass; status and Git commit updated.

---

## M10 — quality reporting and GitHub integration

- [ ] **M10-01** Implement Reports with per-technique coverage history, MC/DC independence proof drilldowns, mutation score, regression outcomes, risk, trends and explicit unsupported/unknown metrics.
- [ ] **M10-02** Publish GitHub Checks/status and optionally approved PR comments tied to exact commit SHA, with idempotency/retry and clear partial coverage semantics.
- [ ] **M10-03** Implement organization-scoped CSV/JSON exports, audit, retention, usage, notifications and signed evidence access.
- [ ] **M10-04** Add cache invalidation, backpressure, dead-letter recovery, worker crash recovery, metrics, traces and dashboards from API through runner.
- [ ] **M10-05** Run end-to-end authorized fixture journey: GitHub branch/PR → mining → risk → objectives → generation → approval → execution → coverage/mutation → gap rerun → AI triage → report/check.
- [ ] **M10-06** Add optional ML inference monitoring, dataset/model lineage, drift alarms, fallback, controlled retraining and approval before promotion.

**Exit gate:** All tasks verified with runnable fixture/integration evidence; unsupported capabilities disclosed and never misreported as covered; tests/build/security pass; status and Git commit updated.

---

## M11 — delivery infrastructure

- [ ] **M11-01** Create optimized production Dockerfiles, Compose dev stack and hardened runtime config with no real secrets.
- [ ] **M11-02** Implement Kubernetes/Helm or Kustomize, network policies, quotas, secrets references and isolated runner worker classes.
- [ ] **M11-03** Implement CI/CD build, lint, types, tests, coverage-engine fixtures, security scans/SBOM and deployment rollback.
- [ ] **M11-04** Integrate observability, backups/restore, operational recovery steps in code/config without new planning Markdown.
- [ ] **M11-05** Perform staging smoke, load, failure/recovery, cost/resource and secure runner isolation tests; no insecure execution fallback.
- [ ] **M11-06** Package optional trained risk inference with artifact integrity, canary/rollback, model version pinning, resource limits and deterministic fallback.

**Exit gate:** All tasks verified with runnable fixture/integration evidence; unsupported capabilities disclosed and never misreported as covered; tests/build/security pass; status and Git commit updated.

---

## M12 — production hardening and final release

- [ ] **M12-01** Complete tenant, auth, webhook, SSRF, prompt-injection, artifact, generated-test, mutation and sandbox security tests.
- [ ] **M12-02** Complete browser accessibility, responsive, loading/empty/error, keyboard and global light/dark parity for every screen including Coverage.
- [ ] **M12-03** Complete cross-language white-box technique acceptance matrix; require real fixture evidence or explicit disclosed unsupported capability, never pretend complete coverage.
- [ ] **M12-04** Complete integration/load/queue/cancellation/recovery/observability tests and authorized staging GitHub install → coverage report journey.
- [ ] **M12-05** Validate deployment/env/secret scans, licenses and dataset permissions, training reproducibility, artifact integrity, ML calibration/fallback and drift plan.
- [ ] **M12-06** Produce evidence-backed release readiness with known limitations, exact human actions, final verified task checkboxes and truthful support matrix.

**Exit gate:** All tasks verified with runnable fixture/integration evidence; unsupported capabilities disclosed and never misreported as covered; tests/build/security pass; status and Git commit updated.

---

