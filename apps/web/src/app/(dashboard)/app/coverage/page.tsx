"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/shell/app-shell";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { DEMO_WHITE_BOX_MATRIX, DEMO_MCDC_PROOF } from "@/lib/fixtures";
import { Plus, Info, ArrowRight, X, CheckCircle2 } from "lucide-react";

export default function WhiteBoxCoveragePage() {
  const [evidenceModalOpen, setEvidenceModalOpen] = useState(false);
  const [generateModalOpen, setGenerateModalOpen] = useState(false);

  return (
    <AppShell breadcrumbs={["White-Box Coverage"]}>
      {/* Eyebrow & Header matching whitebox-coverage-reference.png */}
      <div className="pt-2 pb-6">
        <div className="text-[11px] font-bold tracking-widest uppercase text-muted">
          AUTONOMOUS TESTING INTELLIGENCE PLATFORM
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mt-2">
          <div>
            <h1 className="font-serif text-3xl sm:text-4xl font-normal tracking-tight text-text">
              White-Box Coverage
            </h1>
            <p className="mt-1 text-xs sm:text-sm text-muted">
              Measured objectives, condition independence, mutation and coverage
              gaps.
            </p>
          </div>

          <div>
            <button
              onClick={() => setGenerateModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-lg bg-text text-surface font-medium text-xs hover:opacity-90 transition-opacity shadow-sm cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Generate gap tests</span>
            </button>
          </div>
        </div>
      </div>

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard
          topLabel
          label="Statement coverage"
          value="81%"
          sublabel="Example only"
        />
        <StatCard
          topLabel
          label="Decision / branch"
          value="74%"
          sublabel="Example only"
        />
        <StatCard
          topLabel
          label="MC/DC"
          value="Unknown"
          sublabel="Needs condition tracing"
        />
        <StatCard
          topLabel
          label="Mutation score"
          value="62%"
          sublabel="Example only"
        />
      </div>

      {/* Main Split: Matrix + Evidence and gaps */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left: Objectives Matrix */}
        <div className="lg:col-span-7 rounded-xl border border-border bg-surface overflow-hidden shadow-sm">
          <div className="p-4 border-b border-border">
            <h2 className="text-sm font-semibold text-text">
              White-box objective matrix
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border bg-soft/50 text-muted font-medium">
                  <th className="py-2.5 px-4">Technique</th>
                  <th className="py-2.5 px-4 text-center">Objectives</th>
                  <th className="py-2.5 px-4 text-center">Covered</th>
                  <th className="py-2.5 px-4 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {DEMO_WHITE_BOX_MATRIX.map((row) => (
                  <tr key={row.kind} className="hover:bg-soft transition-colors">
                    <td className="py-3 px-4 font-medium text-text">
                      {row.technique}
                    </td>
                    <td className="py-3 px-4 text-center font-mono text-muted">
                      {row.totalObjectives}
                    </td>
                    <td className="py-3 px-4 text-center font-mono text-muted">
                      {row.coveredCount}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <Badge variant={row.statusVariant}>{row.status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: Evidence and coverage gaps */}
        <div className="lg:col-span-5 rounded-xl border border-border bg-surface p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-text">
                Evidence and coverage gaps
              </h2>
            </div>

            <div className="mt-4">
              <div className="text-[10px] font-bold tracking-wider text-muted uppercase">
                CONDITION INDEPENDENCE
              </div>
              <h3 className="text-base font-semibold text-text mt-1">
                MC/DC proof required
              </h3>
              <p className="text-xs text-muted leading-relaxed mt-2">
                Each condition must independently change the enclosing decision,
                demonstrated by executed test pairs.
              </p>
            </div>

            {/* Code Box matching screenshot */}
            <div className="mt-4 p-4 rounded-lg bg-soft border border-border font-mono text-xs text-text leading-relaxed">
              <div>A &amp;&amp; B</div>
              <div>T1: A=1, B=1 =&gt; 1</div>
              <div>T2: A=0, B=1 =&gt; 0</div>
              <div>T3: A=1, B=0 =&gt; 0</div>
            </div>

            <div className="text-[11px] text-muted mt-3">
              Illustration only — no executed proof attached
            </div>

            <div className="flex items-center gap-2 mt-4">
              <Badge variant="neutral">3 unknown</Badge>
              <Badge variant="neutral">2 unsupported</Badge>
              <Badge variant="warning">11 uncovered</Badge>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-border">
            <button
              onClick={() => setEvidenceModalOpen(true)}
              className="w-full sm:w-auto px-4 py-2 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft transition-colors shadow-xs cursor-pointer"
            >
              Inspect evidence
            </button>
          </div>
        </div>
      </div>

      {/* Gap-driven Verification Loop Flow Panel */}
      <div className="mt-8 rounded-xl border border-border bg-surface p-6 shadow-sm">
        <h3 className="text-xs font-semibold text-muted uppercase tracking-wider mb-4">
          Gap-driven verification loop
        </h3>
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
          {[
            "Discover objectives",
            "Generate candidates",
            "Sandbox execution",
            "Measure evidence",
            "Rerun gaps",
          ].map((step, idx) => (
            <React.Fragment key={step}>
              <div className="px-4 py-3 rounded-lg border border-border bg-soft font-medium text-text flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-surface border border-border text-[10px] flex items-center justify-center font-bold">
                  {idx + 1}
                </span>
                <span>{step}</span>
              </div>
              {idx < 4 && <span className="text-muted hidden sm:inline">→</span>}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Footer hint */}
      <div className="mt-8 text-center text-xs text-muted">
        UI reference · demo data only · white-box coverage is not yet implemented
      </div>

      {/* Inspect Evidence Modal */}
      {evidenceModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
          <div className="w-full max-w-lg rounded-xl border border-border bg-surface p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h3 className="text-sm font-semibold text-text">
                MC/DC Independence Pair Verification
              </h3>
              <button
                onClick={() => setEvidenceModalOpen(false)}
                className="text-muted hover:text-text p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="py-4 space-y-4 text-xs">
              <div>
                <span className="text-muted block text-[11px]">
                  Enclosing Decision Expression
                </span>
                <div className="font-mono p-2 rounded bg-soft border border-border text-text mt-1">
                  {DEMO_MCDC_PROOF.decisionExpr}
                </div>
              </div>

              <div>
                <span className="text-muted block text-[11px]">
                  Target Atomic Condition
                </span>
                <div className="font-semibold text-text">
                  {DEMO_MCDC_PROOF.atomicCondition} (at {DEMO_MCDC_PROOF.sourceSpan})
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg border border-border bg-soft">
                  <div className="font-semibold text-text">Test 1</div>
                  <div className="text-muted font-mono text-[11px] mt-1">
                    {DEMO_MCDC_PROOF.test1Id}
                  </div>
                  <div className="mt-2 text-emerald-600 dark:text-emerald-400 font-mono text-[11px]">
                    Outcome: {DEMO_MCDC_PROOF.outcomeT1}
                  </div>
                </div>

                <div className="p-3 rounded-lg border border-border bg-soft">
                  <div className="font-semibold text-text">Test 2</div>
                  <div className="text-muted font-mono text-[11px] mt-1">
                    {DEMO_MCDC_PROOF.test2Id}
                  </div>
                  <div className="mt-2 text-rose-600 dark:text-rose-400 font-mono text-[11px]">
                    Outcome: {DEMO_MCDC_PROOF.outcomeT2}
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-soft border border-border text-[11px] text-muted">
                Independence Method:{" "}
                <span className="font-mono text-text">
                  {DEMO_MCDC_PROOF.method}
                </span>{" "}
                (all other conditions held fixed).
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-border">
              <button
                onClick={() => setEvidenceModalOpen(false)}
                className="px-4 py-2 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Generate Gap Tests Notice */}
      {generateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-xl border border-border bg-surface p-6 shadow-2xl">
            <h3 className="text-sm font-semibold text-text pb-2">
              Generate Gap Tests
            </h3>
            <p className="text-xs text-muted leading-relaxed pb-4">
              Automated constraint-based and AI-assisted candidate test
              generation will execute in Phase M6 under verified sandbox
              execution policy.
            </p>
            <div className="flex justify-end">
              <button
                onClick={() => setGenerateModalOpen(false)}
                className="px-3 py-1.5 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
