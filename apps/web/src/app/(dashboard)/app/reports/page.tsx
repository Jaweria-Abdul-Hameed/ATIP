"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/shell/app-shell";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import {
  Download,
  Calendar,
  TrendingUp,
  Filter,
  CheckCircle2,
  Clock,
  Layers,
  Sparkles,
} from "lucide-react";
import {
  DEMO_DAILY_TRENDS,
  DEMO_HISTORICAL_REPORTS,
  DEMO_REPOSITORIES,
} from "@/lib/fixtures";
import { DailyTrendPoint, HistoricalReport } from "@/types";

type MetricKey = "passRate" | "coverage" | "runsCount" | "durationSeconds";

interface MetricConfig {
  key: MetricKey;
  label: string;
  suffix: string;
  format: (v: number) => string;
  min: number;
  max: number;
}

const METRIC_CONFIGS: Record<MetricKey, MetricConfig> = {
  passRate: {
    key: "passRate",
    label: "Test Pass Rate",
    suffix: "%",
    format: (v) => `${v.toFixed(1)}%`,
    min: 80,
    max: 100,
  },
  coverage: {
    key: "coverage",
    label: "White-Box Coverage",
    suffix: "%",
    format: (v) => `${v.toFixed(1)}%`,
    min: 70,
    max: 100,
  },
  runsCount: {
    key: "runsCount",
    label: "Test Runs Executed",
    suffix: " runs",
    format: (v) => `${Math.round(v)} runs`,
    min: 10,
    max: 40,
  },
  durationSeconds: {
    key: "durationSeconds",
    label: "Mean Suite Duration",
    suffix: "s",
    format: (v) => `${Math.floor(v / 60)}m ${Math.round(v % 60)}s`,
    min: 80,
    max: 130,
  },
};

export default function ReportsPage() {
  const [selectedMetric, setSelectedMetric] = useState<MetricKey>("passRate");
  const [selectedRepo, setSelectedRepo] = useState<string>("all");
  const [exportFormat, setExportFormat] = useState<"csv" | "json">("csv");
  const [hoveredPoint, setHoveredPoint] = useState<DailyTrendPoint | null>(null);
  const [chartMode, setChartMode] = useState<"dual" | "bars" | "area">("dual");

  const metricConfig = METRIC_CONFIGS[selectedMetric];
  const activePoint =
    hoveredPoint || DEMO_DAILY_TRENDS[DEMO_DAILY_TRENDS.length - 1];

  // Client-side genuine file export
  const handleExportGlobal = () => {
    let content = "";
    let mimeType = "";
    let fileName = "";

    if (exportFormat === "csv") {
      const headers =
        "Date,Day,PassRate(%),Coverage(%),TotalRuns,PassedTests,FailedTests,Duration(s)\n";
      const rows = DEMO_DAILY_TRENDS.map(
        (p) =>
          `${p.date},${p.day},${p.passRate},${p.coverage},${p.runsCount},${p.passedCount},${p.failedCount},${p.durationSeconds}`
      ).join("\n");
      content = headers + rows;
      mimeType = "text/csv;charset=utf-8;";
      fileName = `atip-quality-trends-${new Date().toISOString().slice(0, 10)}.csv`;
    } else {
      const data = {
        exportedAt: new Date().toISOString(),
        organization: "Acme Workspace",
        selectedRepository: selectedRepo,
        activeMetric: metricConfig.label,
        trends: DEMO_DAILY_TRENDS,
        historicalReports: DEMO_HISTORICAL_REPORTS,
      };
      content = JSON.stringify(data, null, 2);
      mimeType = "application/json;charset=utf-8;";
      fileName = `atip-quality-trends-${new Date().toISOString().slice(0, 10)}.json`;
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", fileName);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleDownloadHistorical = (report: HistoricalReport) => {
    const csvContent =
      `Report ID,Title,Repository,Date,Coverage,Total Runs,Status\n` +
      `${report.id},"${report.title}","${report.repo}","${report.date}","${report.coverage}",${report.runs},${report.status}\n`;
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", report.downloadFileName);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // SVG coordinates calculation for the 14 demo points (width: 560, height: 160)
  const svgWidth = 560;
  const svgHeight = 160;
  const paddingX = 18;
  const paddingTop = 20;
  const plotWidth = svgWidth - paddingX * 2;
  const plotHeight = svgHeight - paddingTop - 25;

  const points = DEMO_DAILY_TRENDS.map((p, idx) => {
    const rawVal = p[selectedMetric];
    const normalized = Math.min(
      1,
      Math.max(0, (rawVal - metricConfig.min) / (metricConfig.max - metricConfig.min))
    );
    const x = paddingX + (idx / (DEMO_DAILY_TRENDS.length - 1)) * plotWidth;
    const y = paddingTop + (1 - normalized) * plotHeight;
    return { x, y, rawVal, p };
  });

  // Construct smooth SVG path (Cubic Bezier curves)
  const linePath = points.reduce((acc, pt, i, arr) => {
    if (i === 0) return `M ${pt.x.toFixed(1)},${pt.y.toFixed(1)}`;
    const prev = arr[i - 1];
    const cx1 = (prev.x + (pt.x - prev.x) / 2).toFixed(1);
    const cy1 = prev.y.toFixed(1);
    const cx2 = (prev.x + (pt.x - prev.x) / 2).toFixed(1);
    const cy2 = pt.y.toFixed(1);
    return `${acc} C ${cx1},${cy1} ${cx2},${cy2} ${pt.x.toFixed(1)},${pt.y.toFixed(1)}`;
  }, "");

  const areaPath = `${linePath} L ${points[points.length - 1].x.toFixed(1)},${(svgHeight - 10).toFixed(1)} L ${points[0].x.toFixed(1)},${(svgHeight - 10).toFixed(1)} Z`;

  return (
    <AppShell breadcrumbs={["Reports"]}>
      {/* Editorial Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 pb-6">
        <div>
          <h1 className="font-serif text-3xl sm:text-4xl font-normal tracking-tight text-text">
            Reports &amp; Quality Trends
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-muted">
            Quality trends and traceable engineering evidence across repositories.
          </p>
        </div>

        {/* Global Export Action */}
        <div className="flex items-center gap-2">
          <select
            value={exportFormat}
            onChange={(e) => setExportFormat(e.target.value as "csv" | "json")}
            className="px-3 py-2 rounded-lg border border-border bg-surface text-xs font-medium text-text focus:outline-none cursor-pointer"
            aria-label="Select export format"
          >
            <option value="csv">CSV Export</option>
            <option value="json">JSON Manifest</option>
          </select>

          <button
            onClick={handleExportGlobal}
            type="button"
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
        {/* Interactive Quality Trend Graph Card */}
        <div className="lg:col-span-7 rounded-xl border border-border bg-surface p-6 shadow-sm flex flex-col justify-between">
          <div>
            {/* Graph Header & Controls */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-border">
              <div>
                <h2 className="text-sm font-semibold text-text flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-500" />
                  <span>Test Reliability &amp; Quality Trend</span>
                </h2>
                <div className="mt-1 flex items-center gap-2 text-xs text-muted">
                  <span>{activePoint.day}, 2026:</span>
                  <span className="font-semibold text-text">
                    {metricConfig.format(activePoint[selectedMetric])}
                  </span>
                  <span className="text-muted text-[11px]">
                    ({activePoint.runsCount} runs · {activePoint.passedCount} passed · {activePoint.failedCount} failed)
                  </span>
                </div>
              </div>

              {/* Metric Selector Tabs */}
              <div className="flex items-center gap-1 p-1 rounded-lg border border-border bg-soft/50 text-[11px]">
                {(
                  [
                    { key: "passRate", label: "Pass Rate" },
                    { key: "coverage", label: "Coverage" },
                    { key: "runsCount", label: "Runs" },
                    { key: "durationSeconds", label: "Duration" },
                  ] as const
                ).map((m) => (
                  <button
                    key={m.key}
                    onClick={() => setSelectedMetric(m.key)}
                    className={`px-2 py-1 rounded-md font-medium transition-colors cursor-pointer ${
                      selectedMetric === m.key
                        ? "bg-surface text-text shadow-xs"
                        : "text-muted hover:text-text"
                    }`}
                  >
                    {m.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Filter and View mode row */}
            <div className="flex items-center justify-between pt-3 pb-2 text-xs">
              <div className="flex items-center gap-2">
                <span className="text-muted text-[11px]">Repository:</span>
                <select
                  value={selectedRepo}
                  onChange={(e) => setSelectedRepo(e.target.value)}
                  className="px-2 py-1 rounded border border-border bg-surface text-text text-[11px] focus:outline-none cursor-pointer"
                >
                  <option value="all">All Repositories (Aggregated)</option>
                  {DEMO_REPOSITORIES.map((repo) => (
                    <option key={repo.id} value={repo.id}>
                      {repo.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-1.5 text-[11px] text-muted">
                <button
                  onClick={() => setChartMode("dual")}
                  className={`px-1.5 py-0.5 rounded cursor-pointer ${
                    chartMode === "dual" ? "bg-soft text-text font-medium" : "hover:text-text"
                  }`}
                >
                  Dual
                </button>
                <span>·</span>
                <button
                  onClick={() => setChartMode("bars")}
                  className={`px-1.5 py-0.5 rounded cursor-pointer ${
                    chartMode === "bars" ? "bg-soft text-text font-medium" : "hover:text-text"
                  }`}
                >
                  Bars
                </button>
                <span>·</span>
                <button
                  onClick={() => setChartMode("area")}
                  className={`px-1.5 py-0.5 rounded cursor-pointer ${
                    chartMode === "area" ? "bg-soft text-text font-medium" : "hover:text-text"
                  }`}
                >
                  Line
                </button>
              </div>
            </div>

            {/* Interactive Graph Canvas */}
            <div className="relative mt-2 h-52 w-full select-none">
              {/* Dotted Grid lines */}
              <div className="absolute inset-0 flex flex-col justify-between pointer-events-none pb-7">
                {[1, 2, 3, 4].map((i) => (
                  <div
                    key={i}
                    className="w-full border-b border-dashed border-border/70"
                  />
                ))}
              </div>

              {/* Continuous Trend Line / Area SVG Layer */}
              {(chartMode === "dual" || chartMode === "area") && (
                <svg
                  className="absolute inset-0 w-full h-full pointer-events-none overflow-visible"
                  viewBox={`0 0 ${svgWidth} ${svgHeight}`}
                  preserveAspectRatio="none"
                >
                  <defs>
                    <linearGradient
                      id="qualityAreaGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="0%"
                        stopColor="currentColor"
                        className="text-neutral-900 dark:text-neutral-100"
                        stopOpacity="0.22"
                      />
                      <stop
                        offset="100%"
                        stopColor="currentColor"
                        className="text-neutral-900 dark:text-neutral-100"
                        stopOpacity="0.0"
                      />
                    </linearGradient>
                  </defs>

                  {/* Shaded Area fill */}
                  <path
                    d={areaPath}
                    fill="url(#qualityAreaGradient)"
                    className="transition-all duration-300"
                  />

                  {/* Smooth Stroked Curve */}
                  <path
                    d={linePath}
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="text-neutral-800 dark:text-neutral-200 transition-all duration-300"
                  />

                  {/* Point dots on curve */}
                  {points.map((pt, i) => (
                    <circle
                      key={i}
                      cx={pt.x}
                      cy={pt.y}
                      r={activePoint.date === pt.p.date ? "4.5" : "2.5"}
                      className={`transition-all duration-150 ${
                        activePoint.date === pt.p.date
                          ? "fill-text stroke-surface stroke-2"
                          : "fill-neutral-600 dark:fill-neutral-300"
                      }`}
                    />
                  ))}
                </svg>
              )}

              {/* Bar Columns Container (guaranteed non-zero explicit pixel height) */}
              <div className="absolute inset-0 flex items-end justify-between gap-1 sm:gap-2 pb-7 pt-4">
                {DEMO_DAILY_TRENDS.map((point) => {
                  const rawVal = point[selectedMetric];
                  const normalized = Math.min(
                    1,
                    Math.max(
                      0.08,
                      (rawVal - metricConfig.min) /
                        (metricConfig.max - metricConfig.min)
                    )
                  );
                  const isHovered = activePoint.date === point.date;

                  return (
                    <div
                      key={point.date}
                      onMouseEnter={() => setHoveredPoint(point)}
                      onMouseLeave={() => setHoveredPoint(null)}
                      className="flex-1 h-full flex flex-col justify-end items-center group cursor-pointer relative"
                    >
                      {/* Tooltip on hover */}
                      {isHovered && (
                        <div className="absolute bottom-full mb-2 z-30 px-2.5 py-1.5 rounded-lg bg-neutral-900 dark:bg-neutral-100 text-neutral-100 dark:text-neutral-900 text-[10px] font-medium shadow-xl whitespace-nowrap pointer-events-none transition-all">
                          <div className="font-semibold">{point.day}, 2026</div>
                          <div className="mt-0.5">
                            {metricConfig.label}: {metricConfig.format(rawVal)}
                          </div>
                          <div className="text-[9px] opacity-80 mt-0.5">
                            {point.runsCount} runs · {point.passedCount} passed
                          </div>
                        </div>
                      )}

                      {/* Bar Pillar */}
                      {(chartMode === "dual" || chartMode === "bars") && (
                        <div
                          style={{
                            height: `${Math.round(normalized * 100)}%`,
                          }}
                          className={`w-full rounded-t-sm transition-all duration-200 ${
                            isHovered
                              ? "bg-text shadow-sm"
                              : chartMode === "dual"
                              ? "bg-neutral-800/40 dark:bg-neutral-200/35 hover:bg-neutral-800/80 dark:hover:bg-neutral-200/80"
                              : "bg-neutral-800 dark:bg-neutral-200 hover:bg-text"
                          }`}
                        />
                      )}
                    </div>
                  );
                })}
              </div>

              {/* X-Axis Baseline & Labels */}
              <div className="absolute bottom-0 inset-x-0 h-6 border-t border-border flex items-center justify-between text-[10px] text-muted font-mono pt-1">
                <span>{DEMO_DAILY_TRENDS[0].day}</span>
                <span className="hidden sm:inline">
                  {DEMO_DAILY_TRENDS[Math.floor(DEMO_DAILY_TRENDS.length / 2)].day}
                </span>
                <span>
                  {DEMO_DAILY_TRENDS[DEMO_DAILY_TRENDS.length - 1].day}
                </span>
              </div>
            </div>
          </div>

          {/* Graph Footer Note */}
          <div className="mt-4 pt-3 border-t border-border/80 flex items-center justify-between text-[11px] text-muted">
            <span>Aggregated 14-day history</span>
            <span className="text-emerald-600 dark:text-emerald-400 font-medium">
              ↑ +8.4% improvement
            </span>
          </div>
        </div>

        {/* Recent Reports List */}
        <div className="lg:col-span-5 rounded-xl border border-border bg-surface p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-text">
                Historical Report Exports
              </h2>
              <span className="text-xs text-muted">Signed audit checksums</span>
            </div>

            <div className="space-y-3">
              {DEMO_HISTORICAL_REPORTS.map((r) => (
                <div
                  key={r.id}
                  className="p-3.5 rounded-lg border border-border hover:bg-soft transition-colors flex items-center justify-between text-xs group"
                >
                  <div className="min-w-0 pr-2">
                    <div className="font-semibold text-text truncate">
                      {r.title}
                    </div>
                    <div className="text-[11px] text-muted mt-0.5">
                      {r.date} · {r.repo} · {r.runs} runs analyzed
                    </div>
                  </div>

                  <button
                    onClick={() => handleDownloadHistorical(r)}
                    type="button"
                    className="p-2 rounded-lg border border-border bg-surface text-muted hover:text-text hover:bg-soft shrink-0 transition-colors cursor-pointer"
                    title={`Download ${r.downloadFileName}`}
                    aria-label={`Download ${r.title}`}
                  >
                    <Download className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-border text-[11px] text-muted leading-relaxed">
            Reports are organization-scoped, deterministic, and signed with tamper-resistant audit checksums.
          </div>
        </div>
      </div>

      {/* White-Box Quality History Panel (Requirement M0-WB-02) */}
      <div className="mt-8 rounded-xl border border-border bg-surface p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
          <h3 className="text-sm font-semibold text-text">
            White-Box Quality History
          </h3>
          <Badge variant="neutral" className="text-[10px]">
            Snapshot: main · 8c3e91a
          </Badge>
        </div>
        <p className="text-xs text-muted leading-relaxed mb-4">
          Per-technique covered / uncovered / unknown / unsupported objectives, MC/DC evidence, and mutation scores filtered by repository snapshot.
        </p>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3.5 rounded-lg border border-border bg-soft">
            <div className="text-[10px] text-muted">Statement Executed</div>
            <div className="text-base font-serif font-normal text-text mt-1">
              253 / 312 (81%)
            </div>
          </div>
          <div className="p-3.5 rounded-lg border border-border bg-soft">
            <div className="text-[10px] text-muted">Decisions Evaluated</div>
            <div className="text-base font-serif font-normal text-text mt-1">
              62 / 84 (74%)
            </div>
          </div>
          <div className="p-3.5 rounded-lg border border-border bg-soft">
            <div className="text-[10px] text-muted">MC/DC Independence</div>
            <div className="text-base font-serif font-normal text-text mt-1">
              1 Verified Pair
            </div>
          </div>
          <div className="p-3.5 rounded-lg border border-border bg-soft">
            <div className="text-[10px] text-muted">Mutants Killed</div>
            <div className="text-base font-serif font-normal text-text mt-1">
              50 / 80 (62.5%)
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
