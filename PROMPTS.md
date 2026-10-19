# ATIP — only prompts you need

## 1. START / RUN AUTONOMOUSLY (paste once into Antigravity)

You are the lead implementation engineer for **ATIP — Autonomous Testing Intelligence Platform**.

Your objective is to build the complete, working ATIP application by executing its existing implementation plan, not by generating another plan or documentation package.

### Project Repository

Official GitHub repository:

`https://github.com/Jaweria-Abdul-Hameed/ATIP.git`

During SETUP, inspect the existing Git configuration, connect the workspace to this repository if necessary, preserve existing files and history, and use `main` as the default branch.

Never force-push, overwrite remote history, or perform destructive Git operations without explicit approval. Request human assistance only if authentication or permissions genuinely require it.

### Mandatory Project Initialization

Before implementing anything, read and understand:

- `AGENTS.md`
- `SPEC.md`
- `ARCHITECTURE.md`
- `SECURITY.md`
- `TASKLIST.md`
- `PROMPTS.md`
- `CURRENT_STATUS.md`
- The approved design references under `design/`

Inspect the existing codebase, Git status, project configuration, and available verification evidence.

Treat these documents as authoritative for their respective responsibilities:

- **AGENTS.md:** Agent behavior and implementation rules.
- **SPEC.md:** Product requirements and acceptance criteria.
- **ARCHITECTURE.md:** Technical architecture and component contracts.
- **SECURITY.md:** Security constraints and human-intervention boundaries.
- **TASKLIST.md:** Phase order, implementation tasks, and completion tracking.
- **PROMPTS.md:** Detailed phase-specific implementation and verification instructions.
- **CURRENT_STATUS.md:** Actual progress, verification evidence, decisions, and blockers.
- **design/:** Approved visual references and UI behavior.

Do not duplicate, replace, or disregard the existing phase instructions.

### Mandatory Initial Status Report

Before making changes, report:

1. Current phase and its objective.
2. Tasks already completed, with available verification evidence.
3. The next eligible unchecked task.
4. Relevant phase-specific instructions and acceptance criteria.
5. Any genuine blockers or required human interventions.

If no intervention is required, explicitly state: **No human intervention required.**

After reporting, begin implementation immediately. Do not wait for routine approval.

### Implementation Rules

Execute the existing phases sequentially:

**SETUP → M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8 → M9 → M10 → M11 → M12**

For the active phase:

1. Read its tasks in `TASKLIST.md`.
2. Read all applicable implementation and acceptance instructions in `PROMPTS.md`, together with the relevant product, architecture, security, and design requirements.
3. Implement the next eligible incomplete task using actual working code.
4. Run appropriate tests, static checks, builds, browser verification, security checks, and other required acceptance checks.
5. Mark a task `[x]` only after its requirements have been implemented and successfully verified.
6. Record completed work, test evidence, decisions, limitations, and blockers in `CURRENT_STATUS.md`.
7. Commit and push verified work at the documented checkpoints.
8. Continue to the next eligible task in the current phase without requesting routine approval.

Do not claim success based on generated code alone. Do not fabricate test results, model metrics, screenshots, external access, or completed integrations.

Preserve the approved UI, comprehensive white-box testing requirements, ML benchmarking requirements, and security controls specified in the canonical project documents.

If a task requires genuine human intervention, explain exactly what is needed, record the blocker, and continue other independent eligible work where safe.

### Phase Completion and Manual Conversation Handoff

**This project uses one Antigravity conversation per phase, with the user manually creating the next conversation.**

Complete as much of the active phase as possible within the current conversation.

At the phase boundary:

1. Verify all applicable phase completion criteria.
2. Update `TASKLIST.md` and `CURRENT_STATUS.md`.
3. Commit and push verified changes.
4. Report completed, incomplete, blocked, and unverified tasks.
5. Identify the next phase and its first eligible task.
6. Stop and wait for the user to open a new Antigravity conversation.

**Do not automatically start the next phase in the same conversation.**

If the current phase cannot be completed because of a genuine blocker or context limit, save and checkpoint progress, clearly identify the remaining tasks, and provide a reproducible handoff.

The next conversation will use **Section 2 — CONTINUE** from this file to reconstruct project state and resume without restarting completed work.

### Final Rules

- Do not create additional planning Markdown files.
- Do not restart completed phases or overwrite verified work.
- Do not skip tasks or mark blocked work complete.
- Do not bypass security restrictions or human-only approval gates.
- Do not treat mock data or simulated functionality as production implementation.
- Do not wait for routine approvals within the active phase.
- Follow the existing phase-specific instructions instead of inventing a new implementation process.

**Begin with SETUP if it is incomplete. Otherwise resume the current verified phase. Start implementation now.**

## Phase M0 — Frontend / UI Implementation

### Objective
Build and verify the complete ATIP frontend before
proceeding to backend development.

### Visual References
- design/ATIP_Six_Screens_Exact_Crops
- design/ui-reference.html

- (the first one that i gave is a folder that has six images and one main image that contains all of them mentioned below as well)
- design/ATIP_Six_Screens_Exact_Crops/ATIP_APPROVED_SIX_SCREEN_REFERENCE.png
### UI Visual Fidelity — Mandatory

Treat the six approved ATIP UI screenshots as the **primary visual design authority**. Use `design/ui-reference.html` as the secondary reference for layout structure and interactions.

Reproduce the screenshots' typography, visual hierarchy, compact commit cards, fine borders, subtle backgrounds, spacing, tables, and small metadata labels as closely as possible.

**Color rules:**
- Use predominantly white, off-white, black, and neutral gray.
- Use muted green for successful or healthy states.
- Use muted amber/yellow for warnings and medium risk.
- Use muted red for failures, critical risk, and destructive states.
- Keep status badges small, with subtle tinted backgrounds.
- Avoid large colored panels, bright accents, gradients, neon, glassmorphism, and unnecessary decoration.

**Typography rules:**
- Match the screenshots' heading style and proportions.
- Use refined serif headings where shown.
- Use clean sans-serif typography for navigation, tables, buttons, and body text.
- Keep commit hashes, timestamps, and technical metadata compact and legible.

**Implementation rules:**
- Build reusable commit cards, risk badges, status tags, table rows, and sidebar components.
- Preserve consistent styling across every screen.
- Do not replace the approved visual language with generic shadcn/ui defaults.
- After implementing the frontend, run it, capture screenshots, and compare them against the approved references.
- Fix visible differences before marking the UI phase complete.
- Continue autonomously unless genuine human intervention is required.

### Global Light/Dark Theme — Mandatory

Implement the functional theme toggle demonstrated in `design/ui-reference.html`.

**Light theme (default):**
- White or near-white application background.
- Black/charcoal primary text.
- White cards with subtle neutral borders.
- Light-gray secondary surfaces.

**Dark theme:**
- Black or near-black application background.
- White/off-white primary text.
- Dark charcoal cards and secondary surfaces.
- Subtle dark-gray borders.

**Non-negotiable requirements:**
1. The theme must apply consistently across every page and component.
2. No hardcoded black or white backgrounds that create mismatched patches when switching themes.
3. Use centralized semantic design tokens/CSS variables for backgrounds, text, borders, cards, charts, and status indicators.
4. Preserve the tiny muted red, amber, and green status tags from the approved screenshots in both themes.
5. Keep the approved typography, compact commit cards, spacing, and layout unchanged between themes.
6. Persist the user's theme preference across reloads.
7. Test every screen in both themes, including hover states, menus, dialogs, tables, and charts.
8. Do not mark the UI phase complete until both themes are visually consistent and verified against screenshots.

### Implementation Tasks

Execute all tasks autonomously. Follow the approved six-screen images as the primary visual authority and `design/ui-reference.html` for interactive behavior.

**1. Initialize the frontend**
- Create the Next.js application using App Router, TypeScript, and Tailwind CSS v4.
- Configure shadcn/ui, Lucide React, next-themes, TanStack Query, and TanStack Table.
- Establish reusable components, layouts, and centralized semantic theme tokens.
- Configure fonts to closely match the approved reference images.

**2. Build the application shell**
- Implement the sidebar, top navigation, page headers, breadcrumbs, and responsive layouts.
- Implement the functional light/dark theme toggle from `ui-reference.html`.
- Persist theme preferences across reloads.
- Ensure all surfaces, text, borders, and components switch consistently between themes.

**3. Implement every application screen**
- `/app` — Overview dashboard with summary metrics, recent activity, repository health, and compact commit cards.
- `/app/repositories` — Repository listing, search, filters, and status indicators.
- `/app/repositories/[id]` — Repository workspace with commits, changed files, dependency information, and coverage summaries.
- `/app/risk` — Risk intelligence, explainable risk scores, severity tags, and prioritization.
- `/app/test-plans` — Test plans, recommended tests, approval states, and test-generation actions.
- `/app/runs` — Test-run history, execution status, durations, and filters.
- `/app/runs/[id]` — Individual test-run details, results, logs, and failure information.
- `/app/analysis` — Failure analysis and quality insights.
- `/app/reports` — Reports and quality summaries.
- `/app/settings` — Application preferences, integrations, and configuration.
- Implement necessary authentication and GitHub connection screens.
- `/app/coverage` — White-Box Coverage dashboard showing statement, branch/decision, condition, MC/DC, path, loop, data-flow, exception, boundary, mutation and regression objectives, measured evidence, coverage gaps, and unsupported/unknown statuses. Follow `design/whitebox-coverage-reference.png` as the supplemental visual reference while preserving the approved application design and global light/dark themes.

**4. Reproduce the approved visual language**
- Match screenshot typography, spacing, layout proportions, and visual hierarchy.
- Implement compact commit cards with hashes, authors, timestamps, and metadata.
- Implement small muted green, amber, and red status badges.
- Use thin borders, neutral backgrounds, refined headings, and compact tables.
- Avoid gradients, glassmorphism, neon colors, oversized components, and unnecessary decoration.
- Do not accept generic shadcn/ui defaults as the finished design.

**5. Implement functional frontend interactions**
- Make navigation, theme switching, tabs, menus, dialogs, filters, sorting, and search functional.
- Implement realistic loading, empty, success, and error states.
- Use clearly labeled demo data wherever backend APIs are not yet available.
- Organize data access so demo providers can later be replaced with real FastAPI integrations.
- Do not simulate successful backend operations as though they actually occurred.

**6. Run and inspect the frontend**
- Start the Next.js development server.
- Open and inspect every implemented screen using available browser/testing tools.
- Capture screenshots in both light and dark modes.
- Compare screenshots against the approved visual references.
- Correct visual inconsistencies, broken interactions, layout issues, and console errors.
- Continue iterating autonomously until verification passes.

**7. Complete the phase**
- Update the corresponding checkboxes in `TASKLIST.md` only after verifying each implementation.
- Record implementation details, tests, screenshots, limitations, and remaining work in `CURRENT_STATUS.md`.
- Commit and push verified changes to the GitHub `ATIP` repository.
- Report verified M0 completion and stop at the phase boundary without starting M1.

### Verification and Completion Criteria

Phase M0 is complete only when ALL applicable criteria below pass.

**Application functionality**
- [ ] Next.js application starts successfully.
- [ ] All specified application routes exist and render.
- [ ] Sidebar and navigation work correctly.
- [ ] Search, filters, sorting, tabs, dialogs, and relevant UI controls function.
- [ ] Demo data is clearly distinguished from real backend data.
- [ ] No broken navigation or nonfunctional controls are presented as complete.

**Visual fidelity**
- [ ] All six primary screens closely match the approved reference images.
- [ ] Typography and heading hierarchy match the intended design.
- [ ] Compact commit cards and metadata components are implemented.
- [ ] Muted red, amber, and green status badges are consistent.
- [ ] Layout spacing, card proportions, borders, and tables are visually polished.
- [ ] No unnecessary gradients, glassmorphism, neon accents, or oversized UI elements.

**Light/dark theme**
- [ ] Theme toggle works throughout the application.
- [ ] Light mode consistently uses light surfaces and dark text.
- [ ] Dark mode consistently uses dark surfaces and light text.
- [ ] No mismatched black or white sections appear after switching themes.
- [ ] Status colors remain readable in both modes.
- [ ] Theme preference persists after refreshing.
- [ ] Dialogs, menus, tables, charts, and hover states work in both modes.

**Technical verification**
- [ ] TypeScript type checking passes.
- [ ] ESLint checks pass.
- [ ] Production frontend build succeeds.
- [ ] Relevant component and interaction tests pass.
- [ ] Automated browser smoke tests cover all primary routes.
- [ ] No significant browser console errors occur during tested flows.
- [ ] Responsive layouts are checked at desktop, tablet, and mobile widths.
- [ ] Basic keyboard navigation and accessibility checks pass.

**Visual verification evidence**
- [ ] Light-mode screenshots captured for every primary screen.
- [ ] Dark-mode screenshots captured for every primary screen.
- [ ] Screenshots reviewed against approved references.
- [ ] Identified visual defects corrected or explicitly documented.
- [ ] Remaining deviations are recorded in `CURRENT_STATUS.md`.

**Phase handoff**
- [ ] Verified tasks checked off in `TASKLIST.md`.
- [ ] `CURRENT_STATUS.md` updated with actual implementation and verification results.
- [ ] Changes committed and pushed to GitHub.
- [ ] Next phase identified and ready for autonomous execution.

**Completion rule:** Do not declare Phase M0 complete simply because the application compiles or pages render. It must be functional, visually verified, consistently themed, and tested. If a criterion cannot be verified, record it as unverified rather than marking it complete.

Once all applicable M0 completion criteria pass, update `TASKLIST.md` and `CURRENT_STATUS.md`, commit and push verified work, report the phase completion and verification evidence, and stop. Do not begin the next phase in the same conversation.

## Predictive ML and model lifecycle requirements (M4, M6, M7–M9)

Execute M4-07 through M4-10 as actual engineering tasks: establish permissioned dataset and defensible defect labels; prevent temporal/repository leakage; train and evaluate Logistic Regression, Random Forest, LightGBM, and XGBoost as reproducible experimental candidates when data quality permits; select a production candidate only through the mandatory M4 benchmarking and human-approval process; benchmark against deterministic scoring; version and deploy optional inference with fallback. Never fabricate dataset size, model performance or a trained artifact. If adequate labels are unavailable, keep the deterministic product operational, leave training tasks unchecked, and record a precise blocker in `CURRENT_STATUS.md`. In M6 evaluate pretrained LLM workflows on fixtures, not by training a new foundation model. In M7–M9 implement drift/quality monitoring, promotion/retraining governance, secure artifact handling and release checks. Keep all work within existing canonical Markdown files and actual source/config artifacts.

### Multi-Source Dataset Acquisition and Training

Do not train ATIP's risk prediction model on a single arbitrary dataset.

Research and evaluate multiple established software-defect datasets and suitable public GitHub repositories. Assess each source for availability, licensing, label quality, granularity, language coverage, and relevance to ATIP's commit-level risk prediction task.

Build reproducible ingestion adapters for selected compatible sources. Normalize features and labels, retain source provenance, detect duplicates, and prevent temporal and cross-repository leakage.

### Mandatory M4 Model Benchmarking and Selection

Implement a reproducible experiment comparing **Logistic Regression, Random Forest, LightGBM, and XGBoost** against the existing deterministic risk-scoring baseline.

Use identical eligible training, validation, and held-out test splits and consistent feature definitions for all candidates. Prevent temporal, repository, duplicate, and label leakage. Fit preprocessing and perform any class-imbalance handling using training data only.

Evaluate **PR-AUC (primary metric), precision, recall, F1-score, probability calibration, operational ranking quality, and inference latency**. Use training and validation data for hyperparameter tuning and model selection. Tune decision thresholds on validation data, and evaluate the selected approach once on untouched held-out test data.

Document every candidate's results, dataset provenance, experiment configuration, preprocessing pipeline, random seeds, and model-selection rationale. Select the production candidate based on validated performance, calibration, reproducibility, and resource requirements. **Do not assume LightGBM or XGBoost will win.**

If trustworthy labeled data is insufficient, preserve the deterministic risk-scoring fallback, record the blocker in `CURRENT_STATUS.md`, and do not claim successful training or deploy an unvalidated model.

Follow all existing M4 human-intervention gates for datasets, infrastructure, permissions, and production model promotion.

Version datasets, model artifacts, training configurations, and evaluation reports. Integrate a trained model only when its performance is demonstrated on appropriate held-out data. Otherwise, retain the explainable rules-based engine and report the limitation.

Never silently use private customer repositories for shared model training without explicit authorization.

## 2. CONTINUE (use only when a fresh agent/session is necessary)

Resume ATIP autonomously from the latest verified project state.

Read all seven canonical Markdown files (`AGENTS.md`, `SPEC.md`, `ARCHITECTURE.md`, `SECURITY.md`, `TASKLIST.md`, `PROMPTS.md`, and `CURRENT_STATUS.md`), along with the approved design references relevant to the current phase.

Inspect the existing codebase, Git status, commit history, and available verification evidence. Do not assume that checked tasks are complete without supporting evidence.

### Mandatory Phase Status Report — Before Implementation

Before making changes, clearly report:

1. **Current phase:** Identify the earliest incomplete phase (SETUP or M0–M12) based on actual verification evidence.
2. **Completed tasks:** List the task IDs already completed in that phase, with their verification status.
3. **Next task:** Identify the next eligible unchecked task ID and describe what you will implement.
4. **Blocked tasks:** Identify tasks that cannot currently be completed, explain the exact blocker, and distinguish blocked work from unverified work.
5. **Human intervention:** Specify exactly what you need from me, if anything, including actionable instructions. If no intervention is required, explicitly state "No human intervention required."
6. **Relevant requirements:** Confirm which sections of `TASKLIST.md`, `PROMPTS.md`, and other canonical documents apply to the current phase.

### Autonomous Execution

After providing the status report, **begin implementation immediately without waiting for my approval**, unless a genuine human-only intervention is required.

Execute the active phase according to `TASKLIST.md` and its applicable instructions in `PROMPTS.md`.

For each eligible task:

1. Implement the required functionality.
2. Run relevant tests, reviews, and verification checks.
3. Mark the task `[x]` only after successful verification.
4. Update `CURRENT_STATUS.md` with actual evidence, decisions, limitations, and blockers.
5. Commit and push verified work according to the project's existing instructions.
6. Continue to the next eligible task **within the same phase**.

Follow all applicable phase-specific requirements, including UI visual fidelity, M4 multi-model benchmarking, comprehensive white-box testing, and security requirements.

Do not restart completed phases, recreate existing work, overwrite verified functionality, or fabricate implementation or testing evidence.

If a task is blocked, record the exact blocker and required human action in `CURRENT_STATUS.md`. Continue other independent eligible tasks when safe, but do not silently mark the blocked task or phase complete.

### Phase Completion and Manual Conversation Handoff

**This project uses one Antigravity conversation per phase. The user manually creates the next conversation.**

When the active phase reaches its verified completion boundary:

1. Report completed task IDs and supporting verification evidence.
2. Identify any remaining incomplete, blocked, or unverified tasks.
3. Update `TASKLIST.md` and `CURRENT_STATUS.md`.
4. Commit and push verified changes.
5. Identify the next phase and its first eligible task.
6. Provide a concise handoff summarizing the verified project state.
7. **Stop. Do not begin the next phase in this conversation.**

If the phase cannot be completed because of a genuine blocker, context limit, or execution interruption, checkpoint all progress and clearly identify what remains. The next conversation must resume the incomplete phase rather than skipping it.

Never claim a phase is complete unless its required acceptance criteria have been verified.

The user will open a new conversation and paste this CONTINUE prompt to resume implementation.

## 3. OPTIONAL AUDIT (use only when you want an independent quality pass)

Audit ATIP against every checkbox and acceptance gate. Run actual lint/type/test/build and relevant browser/integration/security tests. Identify false completions, missing screens, broken controls, mocked successes, unsafe runner shortcuts, and cross-tenant authorization gaps. Fix defects when feasible; uncheck tasks lacking evidence; update `CURRENT_STATUS.md`; continue implementing remaining work. Do not produce a separate documentation pack.

## Autonomy limits
The prompt can direct continuous work within Antigravity's permissions/context/tool limits but cannot bypass approval popups, rate limits, external account setup, or guarantee unattended completion. The agent must checkpoint before interruption and never conceal blockers.

## Canonical white-box phase execution and acceptance (M5–M12)
The complete workflow to implement is: **GitHub repository → authorized branch/PR snapshot → repository mining (commits, diffs, dependencies, existing tests) → versioned explainable risk scoring (optional validated ML) → static white-box analysis (AST, CFG, call graph, data-flow/def-use, complexity, reachability) → coverage objective inventory (statement, decision/branch, condition, MC/DC, basis/selected feasible paths, loops, def-use, exceptions, boundaries, mutation, impacted regression) → constraint/fixture/LLM-assisted candidate test generation → validation and review → authorized hardened sandbox execution with instrumentation → measured coverage and mutation analysis → gap-driven regeneration and re-execution with bounded retries → evidence-grounded AI failure analysis → auditable dashboard/GitHub Checks and exports.**

**Phase mapping:** M5 static AST/CFG/data-flow and objective inventory; M6 coverage-driven planning, constraint/LLM-assisted candidate tests and API-key gate; M7 hardened execution and instrumented proof; M8 mutation, regression and bounded gap-driven regeneration; M9 grounded AI failure investigation; M10 coverage reporting and GitHub Checks; M11 infrastructure; M12 security, evidence and release. `TASKLIST.md` is the authoritative task order; no additional Markdown files.

**Mandatory per-technique acceptance:** Build runnable Python and JS/TS fixtures and prove or honestly mark unsupported each of: statement, decision/branch, atomic condition, MC/DC independent condition effect, basis path, selected feasible path, zero/one/multiple/boundary loops, def-use pairs, exception propagation/handling, input boundaries, mutation effectiveness, impacted regression. Record test IDs, code SHA, source spans, observed instrumentation, evidence artifacts, tool version and supported/unknown/infeasible statuses. A coverage tool's branch result is not MC/DC. Do not mark the entire technique complete based on a prompt, a generated test, a static graph, or a mock screenshot. Handle short-circuit Boolean evaluation honestly.

**Human-only gates:** provider API keys via environment/secret manager (never pasted in chat), GitHub App permissions, legal dataset access/consent, hardened runner provisioning, paid cloud infrastructure, production model promotion, external repository writes. Ask exact steps only at dependency boundary and continue independent tasks.

**UI visual authority:** Keep six original PNGs as locked primary references for existing screens. Update `design/ui-reference.html` with White-Box Coverage and added coverage panels; use `design/whitebox-coverage-reference.png` as a supplemental screenshot for the new route. All screens, including Coverage, must use the approved Figtree/Source Serif 4 typography, thin borders, compact metadata, muted semantic accents and complete light/dark themes. Do not replace the originals or introduce neon, gradients or a new layout.

**Verification and finish:** For each phase implement actual code, run automated unit/fixture/contract/integration tests, browser checks for UI, inspect security, log command/output and paths in `CURRENT_STATUS.md`, check only verified tasks, commit/push. If a genuinely required technique cannot be instrumented in a supported language, record the limitation and keep the corresponding acceptance gate open; do not claim final complete white-box coverage. Exhaustive paths are not guaranteed for arbitrary programs.
