"use client";

import React, { useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { DEMO_TEST_RUNS } from "@/lib/fixtures";
import {
  Play,
  ChevronRight,
  CheckCircle2,
  XCircle,
  Clock,
  Terminal,
  ExternalLink,
} from "lucide-react";

export default function TestRunsPage() {
  const [activeTab, setActiveTab] = useState<
    "all" | "passed" | "failed" | "running"
  >("all");
  const [selectedRunId, setSelectedRunId] = useState<string>("run-1042");
  const [detailTab, setDetailTab] = useState<
    "summary" | "results" | "logs"
  >("results");

  const selectedRun =
    DEMO_TEST_RUNS.find((r) => r.id === selectedRunId) || DEMO_TEST_RUNS[0];

  const filteredRuns = DEMO_TEST_RUNS.filter((run) => {
    if (activeTab === "passed") return run.status === "Passed";
    if (activeTab === "failed") return run.status === "Failed";
    if (activeTab === "running") return run.status === "Running";
    return true;
  });

  return (
    <AppShell breadcrumbs={["Test Runs"]}>
      {/* Header matching 06_Test_Runs.png */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 pb-6">
        <div>
          <h1 className="font-serif text-3xl sm:text-4xl font-normal tracking-tight text-text">
            Test Runs
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-muted">
            Execute and monitor test runs across your repositories.
          </p>
        </div>

        <div>
          <button className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-text text-surface font-medium text-xs hover:opacity-90 transition-opacity shadow-sm cursor-pointer">
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Run New Tests</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-6 border-b border-border text-xs font-medium">
        <button
          onClick={() => setActiveTab("all")}
          className={`pb-3 -mb-px transition-colors cursor-pointer ${
            activeTab === "all"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          All Runs (24)
        </button>
        <button
          onClick={() => setActiveTab("passed")}
          className={`pb-3 -mb-px transition-colors cursor-pointer ${
            activeTab === "passed"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          Passed (18)
        </button>
        <button
          onClick={() => setActiveTab("failed")}
          className={`pb-3 -mb-px transition-colors cursor-pointer ${
            activeTab === "failed"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          Failed (4)
        </button>
        <button
          onClick={() => setActiveTab("running")}
          className={`pb-3 -mb-px transition-colors cursor-pointer ${
            activeTab === "running"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          Running (2)
        </button>
      </div>

      {/* Run List Items */}
      <div className="space-y-3 my-6">
        {filteredRuns.map((run) => {
          const isSelected = run.id === selectedRunId;
          return (
            <div
              key={run.id}
              onClick={() => setSelectedRunId(run.id)}
              className={`flex items-center justify-between p-4 rounded-xl border transition-all cursor-pointer shadow-xs ${
                isSelected
                  ? "border-text bg-soft"
                  : "border-border bg-surface hover:bg-soft"
              }`}
            >
              <div className="flex items-center gap-3.5 min-w-0">
                <div className="p-2 rounded-lg border border-border bg-soft text-muted shrink-0">
                  <Terminal className="w-4 h-4 text-text" />
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-text truncate">
                    {run.repoName}
                  </div>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-soft text-muted border border-border">
                      {run.branch}
                    </span>
                    <span className="text-xs text-muted">
                      {run.totalTests} tests
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4 shrink-0">
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
                <span className="text-xs text-muted hidden sm:inline">
                  {run.timestamp}
                </span>
                <ChevronRight className="w-4 h-4 text-muted" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Run Details Panel (bottom of 06_Test_Runs.png) */}
      {selectedRun && (
        <div className="mt-8 rounded-xl border border-border bg-surface overflow-hidden shadow-sm">
          {/* Header */}
          <div className="p-5 border-b border-border flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg border border-border bg-soft text-muted">
                <Terminal className="w-4 h-4 text-text" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-text">
                  {selectedRun.repoName} / {selectedRun.branch}
                </h3>
                <div className="text-xs text-muted mt-0.5">
                  {selectedRun.timestamp}
                </div>
              </div>
              <Badge
                variant={
                  selectedRun.status === "Passed"
                    ? "success"
                    : selectedRun.status === "Failed"
                    ? "error"
                    : "neutral"
                }
              >
                {selectedRun.status}
              </Badge>
            </div>

            <Link
              href={`/app/runs/${selectedRun.id}`}
              className="text-xs font-medium text-muted hover:text-text transition-colors flex items-center gap-1 self-start sm:self-auto"
            >
              <span>Full run details</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* Sub-Tabs */}
          <div className="flex items-center gap-6 px-5 border-b border-border text-xs font-medium">
            <button
              onClick={() => setDetailTab("summary")}
              className={`py-3 -mb-px transition-colors cursor-pointer ${
                detailTab === "summary"
                  ? "text-text font-semibold border-b-2 border-text"
                  : "text-muted hover:text-text"
              }`}
            >
              Summary
            </button>
            <button
              onClick={() => setDetailTab("results")}
              className={`py-3 -mb-px transition-colors cursor-pointer ${
                detailTab === "results"
                  ? "text-text font-semibold border-b-2 border-text"
                  : "text-muted hover:text-text"
              }`}
            >
              Test Results
            </button>
            <button
              onClick={() => setDetailTab("logs")}
              className={`py-3 -mb-px transition-colors cursor-pointer ${
                detailTab === "logs"
                  ? "text-text font-semibold border-b-2 border-text"
                  : "text-muted hover:text-text"
              }`}
            >
              Logs
            </button>
          </div>

          {/* Sub-header metric counts */}
          <div className="p-5 border-b border-border flex items-center justify-between text-xs text-muted">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5 text-text font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                <span className="font-serif text-sm font-normal">{selectedRun.passedCount}</span> passed
              </span>
              <span><span className="font-serif text-sm font-normal text-text">{selectedRun.failedCount}</span> failed</span>
              <span><span className="font-serif text-sm font-normal text-text">{selectedRun.skippedCount}</span> skipped</span>
            </div>
            <div className="flex items-center gap-1 font-mono text-xs">
              <Clock className="w-3.5 h-3.5 text-muted" />
              <span>{selectedRun.duration}</span>
            </div>
          </div>

          {/* Tab Content */}
          {detailTab === "results" && (
            <div className="divide-y divide-border text-xs">
              {selectedRun.testResults.map((t) => (
                <div
                  key={t.id}
                  className="p-4 flex items-center justify-between hover:bg-soft transition-colors"
                >
                  <div className="flex items-center gap-3 font-mono text-text">
                    <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
                    <span>{t.fileName}</span>
                  </div>
                  <div className="flex items-center gap-6 text-muted">
                    <span>{t.testCount} tests</span>
                    <span className="font-mono">{t.duration}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {detailTab === "summary" && (
            <div className="p-6 text-xs text-muted leading-relaxed space-y-2">
              <p>
                Executed within isolated Docker sandbox runner. Memory limit: 2048MB, CPU quota: 2.0.
              </p>
              <p>
                Instrumentation recorded 32 test assertions, zero unhandled exceptions, and passed all policy gates.
              </p>
            </div>
          )}

          {detailTab === "logs" && (
            <div className="p-5 font-mono text-xs bg-soft text-text leading-relaxed overflow-x-auto space-y-1">
              <div>[00:00.01] Sandbox runner provisioned (container id: sbx-9014)</div>
              <div>[00:00.05] Mounting immutable repository snapshot sha: a1b2c3d</div>
              <div>[00:00.12] Executing test suite: vitest run --coverage</div>
              <div className="text-emerald-600 dark:text-emerald-400">
                [00:02.14] ✓ 4 test suites passed (32 tests)
              </div>
              <div>[00:02.15] Collecting white-box instrumentation artifacts...</div>
              <div>[00:02.18] Run completed with status: PASSED</div>
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}
