"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { DEMO_RISK_FILES, DEMO_REPOSITORIES } from "@/lib/fixtures";
import { RiskyFile } from "@/types";
import {
  Download,
  ChevronDown,
  ChevronRight,
  X,
  AlertTriangle,
  ShieldAlert,
  Info,
} from "lucide-react";

export default function RiskIntelligencePage() {
  const [selectedRepo, setSelectedRepo] = useState("nextjs-dashboard");
  const [selectedBranch, setSelectedBranch] = useState("main");
  const [selectedTimeRange, setSelectedTimeRange] = useState("Last 30 days");
  const [selectedFile, setSelectedFile] = useState<RiskyFile | null>(null);

  const handleExport = () => {
    const csvContent =
      "data:text/csv;charset=utf-8," +
      ["File,Risk Score,Severity,Risk Factors,Last Changed"]
        .concat(
          DEMO_RISK_FILES.map(
            (f) =>
              `"${f.filePath}",${f.riskScore},"${f.severity}","${f.riskFactors}","${f.lastChanged}"`
          )
        )
        .join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `atip-risk-${selectedRepo}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <AppShell breadcrumbs={["Risk Intelligence"]}>
      {/* Header matching 04_Risk_Intelligence.png */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 pb-6">
        <div>
          <h1 className="font-serif text-3xl sm:text-4xl font-normal tracking-tight text-text">
            Risk Intelligence
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-muted">
            Identify high-risk code changes and vulnerable components.
          </p>
        </div>

        <div>
          <button
            onClick={handleExport}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft transition-colors shadow-xs cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-muted" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Filter Dropdowns matching screenshot */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 my-4">
        {/* Repository Selector */}
        <div className="p-3 rounded-xl border border-border bg-surface">
          <label className="block text-[11px] font-medium text-muted mb-1">
            Repository
          </label>
          <div className="relative">
            <select
              value={selectedRepo}
              onChange={(e) => setSelectedRepo(e.target.value)}
              className="w-full appearance-none bg-transparent text-xs font-medium text-text focus:outline-none cursor-pointer pr-6"
            >
              {DEMO_REPOSITORIES.map((r) => (
                <option key={r.id} value={r.id} className="bg-surface text-text">
                  {r.name}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-0 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted pointer-events-none" />
          </div>
        </div>

        {/* Branch Selector */}
        <div className="p-3 rounded-xl border border-border bg-surface">
          <label className="block text-[11px] font-medium text-muted mb-1">
            Branch
          </label>
          <div className="relative">
            <select
              value={selectedBranch}
              onChange={(e) => setSelectedBranch(e.target.value)}
              className="w-full appearance-none bg-transparent text-xs font-medium text-text focus:outline-none cursor-pointer pr-6"
            >
              <option value="main" className="bg-surface text-text">main</option>
              <option value="develop" className="bg-surface text-text">develop</option>
              <option value="feature/auth" className="bg-surface text-text">feature/auth</option>
            </select>
            <ChevronDown className="absolute right-0 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted pointer-events-none" />
          </div>
        </div>

        {/* Time range Selector */}
        <div className="p-3 rounded-xl border border-border bg-surface">
          <label className="block text-[11px] font-medium text-muted mb-1">
            Time range
          </label>
          <div className="relative">
            <select
              value={selectedTimeRange}
              onChange={(e) => setSelectedTimeRange(e.target.value)}
              className="w-full appearance-none bg-transparent text-xs font-medium text-text focus:outline-none cursor-pointer pr-6"
            >
              <option value="Last 30 days" className="bg-surface text-text">Last 30 days</option>
              <option value="Last 7 days" className="bg-surface text-text">Last 7 days</option>
              <option value="All time" className="bg-surface text-text">All time</option>
            </select>
            <ChevronDown className="absolute right-0 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Risk Table matching 04_Risk_Intelligence.png */}
      <div className="mt-6 rounded-xl border border-border bg-surface overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="border-b border-border bg-soft/50 text-muted font-medium">
                <th className="py-3 px-4 font-medium">File / Component</th>
                <th className="py-3 px-4 font-medium text-center">Risk Score</th>
                <th className="py-3 px-4 font-medium">Risk Factors</th>
                <th className="py-3 px-4 font-medium text-right">Last Changed</th>
                <th className="py-3 px-4 text-center"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {DEMO_RISK_FILES.map((file) => (
                <tr
                  key={file.id}
                  onClick={() => setSelectedFile(file)}
                  className="hover:bg-soft transition-colors cursor-pointer group"
                >
                  <td className="py-3.5 px-4 font-mono text-text">
                    {file.filePath}
                  </td>
                  <td className="py-3.5 px-4 text-center">
                    <div className="inline-flex items-center gap-2">
                      <span className="font-semibold text-text">
                        {file.riskScore}
                      </span>
                      <Badge
                        variant={
                          file.severity === "high"
                            ? "error"
                            : file.severity === "medium"
                            ? "warning"
                            : "success"
                        }
                      >
                        {file.severity === "high"
                          ? "High"
                          : file.severity === "medium"
                          ? "Medium"
                          : "Low"}
                      </Badge>
                    </div>
                  </td>
                  <td className="py-3.5 px-4 text-muted">
                    {file.riskFactors}
                  </td>
                  <td className="py-3.5 px-4 text-right text-muted">
                    {file.lastChanged}
                  </td>
                  <td className="py-3.5 px-4 text-center text-muted group-hover:text-text">
                    <ChevronRight className="w-4 h-4 inline" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Detail Drawer for Selected File */}
      {selectedFile && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs">
          <div className="w-full max-w-lg bg-surface border-l border-border h-full p-6 overflow-y-auto shadow-2xl flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-border">
              <div>
                <div className="text-[11px] font-semibold text-muted uppercase tracking-wider">
                  Risk Evidence Drilldown
                </div>
                <h3 className="font-mono text-sm font-semibold text-text mt-1">
                  {selectedFile.filePath}
                </h3>
              </div>
              <button
                onClick={() => setSelectedFile(null)}
                className="p-1.5 rounded-lg border border-border text-muted hover:text-text"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="py-6 space-y-6 flex-1">
              <div className="grid grid-cols-2 gap-3">
                <div className="p-4 rounded-xl border border-border bg-soft">
                  <div className="text-[11px] text-muted">Risk Score</div>
                  <div className="text-2xl font-bold text-text mt-1">
                    {selectedFile.riskScore} / 100
                  </div>
                </div>
                <div className="p-4 rounded-xl border border-border bg-soft">
                  <div className="text-[11px] text-muted">Test Coverage</div>
                  <div className="text-2xl font-bold text-text mt-1">
                    {selectedFile.coveragePercent}%
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-text mb-2">
                  Key Risk Drivers
                </h4>
                <ul className="space-y-2 text-xs text-muted">
                  {selectedFile.reasons.map((r, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-amber-500 font-bold">•</span>
                      <span>{r}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="p-4 rounded-xl border border-border bg-soft text-xs text-muted space-y-2">
                <div className="flex items-center gap-1.5 font-semibold text-text">
                  <Info className="w-4 h-4" />
                  <span>Explainability & Provenance</span>
                </div>
                <p>
                  Scores are computed using the deterministic risk engine
                  weights: churn frequency (35%), recent bug associations (25%),
                  cyclomatic branch complexity (20%), and coverage deficit
                  (20%).
                </p>
              </div>
            </div>

            <div className="pt-4 border-t border-border flex justify-end gap-2">
              <button
                onClick={() => setSelectedFile(null)}
                className="px-3.5 py-2 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft"
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
