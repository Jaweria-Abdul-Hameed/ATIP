"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/shell/app-shell";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import { Download, FileText, BarChart3, Calendar, ArrowRight } from "lucide-react";

export default function ReportsPage() {
  const [exportFormat, setExportFormat] = useState<"csv" | "json">("csv");

  const reports = [
    {
      id: "rep-1",
      title: "Weekly Quality & Coverage Summary",
      date: "Oct 18, 2026",
      coverage: "88.2%",
      runs: 124,
      status: "Available",
    },
    {
      id: "rep-2",
      title: "White-Box Mutation & MC/DC Audit",
      date: "Oct 17, 2026",
      coverage: "74.0%",
      runs: 86,
      status: "Available",
    },
    {
      id: "rep-3",
      title: "Repository Churn & Risk Delta Report",
      date: "Oct 16, 2026",
      coverage: "81.5%",
      runs: 95,
      status: "Available",
    },
  ];

  const handleDownload = (title: string) => {
    alert(`Exporting ${title} in ${exportFormat.toUpperCase()} format.`);
  };

  return (
    <AppShell breadcrumbs={["Reports"]}>
      {/* Header matching ui-reference.html */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 pb-6">
        <div>
          <h1 className="font-serif text-3xl sm:text-4xl font-normal tracking-tight text-text">
            Reports & Quality Trends
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-muted">
            Quality trends and traceable engineering evidence across
            repositories.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value as any)}
            className="px-3 py-2 rounded-lg border border-border bg-surface text-xs font-medium text-text focus:outline-none cursor-pointer"
          >
            <option value="csv">CSV Export</option>
            <option value="json">JSON Manifest</option>
          </select>

          <button
            onClick={() => handleDownload("Global Quality Report")}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-text text-surface font-medium text-xs hover:opacity-90 transition-opacity shadow-sm cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Report</span>
          </button>
        </div>
      </div>

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <StatCard label="Test success" value="96.8%" sublabel="Last 30 days" />
        <StatCard label="Mean duration" value="1m 52s" sublabel="Per test suite" />
        <StatCard label="Risk trend" value="−12%" sublabel="Reduced churn" />
        <StatCard label="Investigations" value="14" sublabel="AI-assisted triages" />
      </div>

      {/* Main Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Quality Trend Bars */}
        <div className="lg:col-span-7 rounded-xl border border-border bg-surface p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-text">
              Test Reliability &amp; Pass Rate Trend
            </h2>
            <span className="text-xs text-muted">Daily aggregated</span>
          </div>

          <div className="h-44 flex items-end gap-3 pt-6 pb-2 border-b border-border">
            {[45, 52, 60, 58, 70, 75, 68, 88, 82, 92, 89, 96].map(
              (height, idx) => (
                <div
                  key={idx}
                  className="flex-1 flex flex-col items-center gap-1.5 group"
                >
                  <div
                    style={{ height: `${height}%` }}
                    className="w-full rounded-t-sm bg-neutral-800 dark:bg-neutral-200 group-hover:opacity-75 transition-opacity"
                    title={`Day ${idx + 1}: ${height}% pass rate`}
                  />
                  <span className="text-[10px] text-muted font-mono">
                    {idx + 1}
                  </span>
                </div>
              )
            )}
          </div>
          <div className="flex items-center justify-between text-[11px] text-muted pt-3">
            <span>October 1</span>
            <span>October 18</span>
          </div>
        </div>

        {/* Recent Reports List */}
        <div className="lg:col-span-5 rounded-xl border border-border bg-surface p-6 shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-sm font-semibold text-text mb-4">
              Historical Report Exports
            </h2>

            <div className="space-y-3">
              {reports.map((r) => (
                <div
                  key={r.id}
                  className="p-3.5 rounded-lg border border-border hover:bg-soft transition-colors flex items-center justify-between text-xs"
                >
                  <div className="min-w-0">
                    <div className="font-semibold text-text truncate">
                      {r.title}
                    </div>
                    <div className="text-[11px] text-muted mt-0.5">
                      {r.date} · {r.runs} runs analyzed
                    </div>
                  </div>
                  <button
                    onClick={() => handleDownload(r.title)}
                    className="p-1.5 rounded-md border border-border bg-surface text-muted hover:text-text shrink-0"
                    title="Download report"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-border text-[11px] text-muted">
            Reports are organization-scoped and signed with tamper-resistant audit checksums.
          </div>
        </div>
      </div>

      {/* White-Box Quality History Panel (Requirement M0-WB-02) */}
      <div className="mt-8 rounded-xl border border-border bg-surface p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-text mb-2">
          White-box Quality History
        </h3>
        <p className="text-xs text-muted leading-relaxed mb-4">
          Per-technique covered / uncovered / unknown / unsupported objectives, MC/DC evidence, and mutation scores filtered by repository snapshot.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3 rounded-lg border border-border bg-soft">
            <div className="text-[10px] text-muted">Statement Executed</div>
            <div className="text-base font-serif font-normal text-text mt-1">253 / 312 (81%)</div>
          </div>
          <div className="p-3 rounded-lg border border-border bg-soft">
            <div className="text-[10px] text-muted">Decisions Evaluated</div>
            <div className="text-base font-serif font-normal text-text mt-1">62 / 84 (74%)</div>
          </div>
          <div className="p-3 rounded-lg border border-border bg-soft">
            <div className="text-[10px] text-muted">MC/DC Independence</div>
            <div className="text-base font-serif font-normal text-text mt-1">1 Verified Pair</div>
          </div>
          <div className="p-3 rounded-lg border border-border bg-soft">
            <div className="text-[10px] text-muted">Mutants Killed</div>
            <div className="text-base font-serif font-normal text-text mt-1">50 / 80 (62.5%)</div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
