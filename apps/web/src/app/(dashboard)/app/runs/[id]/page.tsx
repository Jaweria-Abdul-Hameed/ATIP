"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { DEMO_TEST_RUNS } from "@/lib/fixtures";
import {
  RotateCw,
  Ban,
  CheckCircle2,
  XCircle,
  Clock,
  Terminal,
  FileCode,
  Download,
  AlertOctagon,
  ArrowLeft,
} from "lucide-react";

export default function RunDetailsPage() {
  const params = useParams();
  const runId = (params?.id as string) || "run-1042";
  const run =
    DEMO_TEST_RUNS.find((r) => r.id === runId) || DEMO_TEST_RUNS[0];

  const [activeTab, setActiveTab] = useState<
    "tests" | "logs" | "artifacts" | "instrumentation"
  >("tests");
  const [isRetrying, setIsRetrying] = useState(false);

  const steps = [
    { name: "Queued", status: "completed" },
    { name: "Provisioned", status: "completed" },
    { name: "Running", status: "completed" },
    {
      name: run.status === "Failed" ? "Failed" : "Completed",
      status: run.status === "Failed" ? "failed" : "completed",
    },
  ];

  return (
    <AppShell breadcrumbs={["Test Runs", run.runNumber]}>
      {/* Back button and Header */}
      <div className="pt-2 pb-6 border-b border-border">
        <Link
          href="/app/runs"
          className="inline-flex items-center gap-1.5 text-xs text-muted hover:text-text mb-3 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Test Runs</span>
        </Link>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <h1 className="font-serif text-2xl sm:text-3xl font-normal tracking-tight text-text">
              {run.runNumber}
            </h1>
            <Badge
              variant={
                run.status === "Passed"
                  ? "success"
                  : run.status === "Failed"
                  ? "error"
                  : "neutral"
              }
            >
              {run.status}
            </Badge>
            <span className="text-xs text-muted">
              {run.repoName} · {run.branch}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setIsRetrying(true);
                setTimeout(() => setIsRetrying(false), 1500);
              }}
              disabled={isRetrying}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft transition-colors shadow-xs cursor-pointer"
            >
              <RotateCw className={`w-3.5 h-3.5 ${isRetrying ? "animate-spin" : ""}`} />
              <span>{isRetrying ? "Rerunning..." : "Rerun in Sandbox"}</span>
            </button>

            <button
              onClick={() => alert("Run cancelled (or already completed in demo).")}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-surface text-xs font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-500/10 transition-colors shadow-xs cursor-pointer"
            >
              <Ban className="w-3.5 h-3.5" />
              <span>Cancel</span>
            </button>
          </div>
        </div>
      </div>

      {/* Execution Stepper */}
      <div className="my-6 p-5 rounded-xl border border-border bg-surface shadow-xs">
        <div className="text-[11px] font-semibold text-muted uppercase tracking-wider mb-4">
          Execution Lifecycle
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
          {steps.map((step, idx) => (
            <React.Fragment key={step.name}>
              <div className="flex items-center gap-2">
                {step.status === "completed" ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                ) : step.status === "failed" ? (
                  <XCircle className="w-4 h-4 text-rose-500 shrink-0" />
                ) : (
                  <Clock className="w-4 h-4 text-muted shrink-0" />
                )}
                <span className="font-medium text-text">{step.name}</span>
              </div>
              {idx < steps.length - 1 && (
                <span className="text-muted hidden sm:inline">→</span>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-6 border-b border-border text-xs font-medium">
        {[
          { id: "tests", label: "Individual Tests" },
          { id: "logs", label: "Stdout / Stderr Logs" },
          { id: "instrumentation", label: "Instrumentation Evidence" },
          { id: "artifacts", label: "Artifacts" },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`pb-3 -mb-px transition-colors cursor-pointer ${
              activeTab === tab.id
                ? "text-text font-semibold border-b-2 border-text"
                : "text-muted hover:text-text"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === "tests" && (
          <div className="rounded-xl border border-border bg-surface divide-y divide-border overflow-hidden shadow-sm text-xs">
            {run.testResults.map((t) => (
              <div
                key={t.id}
                className="p-4 flex items-center justify-between hover:bg-soft transition-colors"
              >
                <div className="flex items-center gap-3 font-mono text-text">
                  {t.passed ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-500 shrink-0" />
                  )}
                  <span>{t.fileName}</span>
                </div>
                <div className="flex items-center gap-6 text-muted">
                  <span>{t.testCount} assertions</span>
                  <span className="font-mono">{t.duration}</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === "logs" && (
          <div className="rounded-xl border border-border bg-soft p-5 font-mono text-xs text-text leading-relaxed overflow-x-auto shadow-inner space-y-1">
            <div className="text-muted"># ATIP Ephemeral Runner Sandbox (Quotas: 2.0 CPU, 2048MB RAM, Default-Deny Network)</div>
            <div>[00:00.00] Initiating job container dispatch for run {run.runNumber}</div>
            <div>[00:00.04] SHA verified: a1b2c3d4e5f6</div>
            <div>[00:00.10] Starting instrumented runtime observer...</div>
            <div className="text-emerald-600 dark:text-emerald-400">
              [00:01.40] PASS auth.users.test.ts (5 tests) [320ms]
            </div>
            <div className="text-emerald-600 dark:text-emerald-400">
              [00:02.10] PASS api.payments.test.ts (8 tests) [1.2s]
            </div>
            {run.status === "Failed" && (
              <div className="text-rose-600 dark:text-rose-400 font-semibold mt-2">
                [00:02.18] AssertionError: expected 200, received 401 Unauthorized in oauth.flow.test.py:84
              </div>
            )}
            <div className="text-muted mt-2">[00:02.20] Job execution finished. Artifacts committed to tenant object storage.</div>
          </div>
        )}

        {activeTab === "instrumentation" && (
          <div className="rounded-xl border border-border bg-surface p-6 space-y-4 shadow-sm text-xs">
            <h3 className="font-semibold text-text">
              White-Box Instrumentation Findings
            </h3>
            <p className="text-muted leading-relaxed">
              Execution traces captured 253 executed statement lines and 62 decision branches. Atomic condition monitoring evaluated 28 MC/DC pairs.
            </p>
            <div className="p-4 rounded-lg bg-soft border border-border font-mono text-[11px] text-text">
              Decision: isValidSession &amp;&amp; (hasPermission || isSuperUser)
              <br />
              Observed vector: [T, T, F] =&gt; TRUE (Test: test_auth_permission_granted)
              <br />
              Observed vector: [T, F, F] =&gt; FALSE (Test: test_auth_permission_denied)
            </div>
          </div>
        )}

        {activeTab === "artifacts" && (
          <div className="rounded-xl border border-border bg-surface divide-y divide-border overflow-hidden shadow-sm text-xs">
            {[
              { name: "lcov.info", size: "48 KB", type: "Coverage Report" },
              { name: "junit-report.xml", size: "12 KB", type: "Test Results" },
              { name: "mcdc-traces.json", size: "84 KB", type: "Condition Vectors" },
              { name: "sandbox-audit.log", size: "6 KB", type: "Runner Security Audit" },
            ].map((art) => (
              <div
                key={art.name}
                className="p-4 flex items-center justify-between hover:bg-soft transition-colors"
              >
                <div className="flex items-center gap-3">
                  <FileCode className="w-4 h-4 text-muted" />
                  <span className="font-mono text-text font-medium">
                    {art.name}
                  </span>
                  <Badge variant="neutral">{art.type}</Badge>
                </div>
                <div className="flex items-center gap-4 text-muted">
                  <span>{art.size}</span>
                  <button
                    onClick={() => alert(`Downloading ${art.name} (signed URL demo)`)}
                    className="p-1 rounded text-muted hover:text-text"
                    title="Download artifact"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}
