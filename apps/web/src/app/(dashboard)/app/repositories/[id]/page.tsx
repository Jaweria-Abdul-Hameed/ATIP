"use client";

import React, { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { DEMO_REPOSITORIES, DEMO_COMMITS } from "@/lib/fixtures";
import { api } from "@/lib/api-adapter";
import {
  apiClient,
  BranchApiItem,
  CommitApiItem,
  CoverageSummaryApiItem,
  DependencyGraphApiItem,
  FileComplexityApiItem,
} from "@/lib/api-client";
import {
  GitBranch,
  Search,
  RotateCw,
  ExternalLink,
  MoreVertical,
  ChevronDown,
  GitCommit,
  FileCode2,
  Share2,
  ShieldAlert,
  Target,
  ArrowRight,
  Play,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  Activity,
} from "lucide-react";

export default function RepositoryWorkspacePage() {
  const params = useParams();
  const repoId = (params?.id as string) || "nextjs-dashboard";

  const [activeTab, setActiveTab] = useState<
    "commits" | "overview" | "files" | "dependencies" | "coverage" | "settings"
  >("commits");
  const [selectedBranch, setSelectedBranch] = useState("main");
  const [branches, setBranches] = useState<BranchApiItem[]>([]);
  const [searchCommitQuery, setSearchCommitQuery] = useState("");
  const [syncing, setSyncing] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState<string | null>(null);
  const [analysisProgress, setAnalysisProgress] = useState<number>(0);

  // Mined data state
  const [repository, setRepository] = useState<any>(
    DEMO_REPOSITORIES.find((r) => r.id === repoId) || DEMO_REPOSITORIES[0]
  );
  const [commits, setCommits] = useState<any[]>(DEMO_COMMITS);
  const [dependencies, setDependencies] = useState<DependencyGraphApiItem | null>(null);
  const [complexityFiles, setComplexityFiles] = useState<FileComplexityApiItem[]>([]);
  const [coverage, setCoverage] = useState<CoverageSummaryApiItem | null>(null);
  const [loading, setLoading] = useState(true);

  // Load repository and mined data
  const loadRepoData = useCallback(async () => {
    try {
      setLoading(true);
      // 1. Repository info
      const repoData = await api.getRepository(repoId, { forceLive: true });
      if (repoData) {
        setRepository(repoData);
        setSelectedBranch(repoData.defaultBranch || "main");
      }

      // 2. Branches
      const branchList = await apiClient.getRepositoryBranches(repoId).catch(() => []);
      if (branchList.length > 0) {
        setBranches(branchList);
      }

      // 3. Commits
      const liveCommits = await api.getCommits(repoId, {
        branch: selectedBranch,
        forceLive: true,
      });
      if (liveCommits && liveCommits.length > 0) {
        setCommits(liveCommits);
      }

      // 4. Dependencies
      const depGraph = await api.getDependencies(repoId);
      if (depGraph) {
        setDependencies(depGraph);
      }

      // 5. Complexity & Files
      const compList = await api.getComplexity(repoId);
      if (compList && compList.length > 0) {
        setComplexityFiles(compList);
      }

      // 6. Coverage
      const covData = await api.getCoverage(repoId);
      if (covData) {
        setCoverage(covData);
      }
    } catch (err) {
      console.warn("Could not fetch live repo data, using fallback fixtures:", err);
    } finally {
      setLoading(false);
    }
  }, [repoId, selectedBranch]);

  useEffect(() => {
    loadRepoData();
  }, [loadRepoData]);

  // Sync handler
  const handleSync = async () => {
    setSyncing(true);
    try {
      await apiClient.syncRepository(repoId);
      await loadRepoData();
    } catch {
      // Fallback transition
    } finally {
      setTimeout(() => setSyncing(false), 800);
    }
  };

  // Trigger analysis handler
  const handleTriggerAnalysis = async () => {
    setAnalyzing(true);
    setAnalysisStatus("Initializing analysis job...");
    setAnalysisProgress(10);

    try {
      const job = await api.triggerAnalysis(repoId, {
        branch: selectedBranch,
        force_rerun: true,
      });

      setAnalysisStatus(job.current_step || "Running repository analysis");
      setAnalysisProgress(job.progress_pct || 20);

      // Poll analysis progress
      const pollInterval = setInterval(async () => {
        try {
          const updatedJob = await api.getAnalysisJob(job.id);
          setAnalysisStatus(updatedJob.current_step);
          setAnalysisProgress(updatedJob.progress_pct);

          if (
            updatedJob.status === "completed" ||
            updatedJob.status === "failed" ||
            updatedJob.progress_pct >= 100
          ) {
            clearInterval(pollInterval);
            setAnalyzing(false);
            if (updatedJob.status === "completed") {
              setAnalysisStatus("Analysis completed successfully");
              await loadRepoData();
            } else {
              setAnalysisStatus(`Analysis failed: ${updatedJob.error_message || "Unknown error"}`);
            }
          }
        } catch {
          clearInterval(pollInterval);
          setAnalyzing(false);
        }
      }, 1000);
    } catch (err: any) {
      setAnalyzing(false);
      setAnalysisStatus(`Failed to trigger analysis: ${err?.message || "Unknown error"}`);
    }
  };

  const filteredCommits = commits.filter((c) =>
    (c.message || "").toLowerCase().includes(searchCommitQuery.toLowerCase())
  );

  return (
    <AppShell breadcrumbs={["Repositories", repository.name]}>
      {/* Header matching 03_Repository_Workspace.png */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 pb-6 border-b border-border">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl border border-border bg-soft flex items-center justify-center shrink-0">
            {/* GitHub Octocat Mark */}
            <svg
              className="w-7 h-7 text-text"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
              />
            </svg>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-serif text-2xl sm:text-3xl font-normal tracking-tight text-text">
                {repository.name}
              </h1>
              {repository.isPrivate && (
                <Badge variant="neutral" className="text-[10px]">
                  Private
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2 text-xs text-muted mt-1">
              <span>{repository.fullName || repository.name}</span>
              {repository.cloneUrl && (
                <a
                  href={repository.cloneUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-text transition-colors"
                >
                  <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Analyze Repository CTA */}
          <button
            onClick={handleTriggerAnalysis}
            disabled={analyzing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90 transition-opacity shadow-xs cursor-pointer disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 ${analyzing ? "animate-spin" : ""}`} />
            <span>{analyzing ? "Analyzing..." : "Analyze repository"}</span>
          </button>

          {/* Sync now CTA */}
          <button
            onClick={handleSync}
            disabled={syncing}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft transition-colors shadow-xs cursor-pointer"
          >
            <RotateCw className={`w-3.5 h-3.5 ${syncing ? "animate-spin" : ""}`} />
            <span>{syncing ? "Syncing..." : "Sync now"}</span>
          </button>

          <button className="p-1.5 rounded-lg border border-border bg-surface text-muted hover:text-text transition-colors">
            <MoreVertical className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Analysis Running Banner */}
      {(analyzing || analysisStatus) && (
        <div className="mt-4 p-3.5 rounded-xl border border-border bg-soft flex items-center justify-between text-xs">
          <div className="flex items-center gap-2.5">
            {analyzing ? (
              <RotateCw className="w-4 h-4 animate-spin text-text" />
            ) : analysisStatus?.includes("completed") ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            ) : (
              <Activity className="w-4 h-4 text-muted" />
            )}
            <span className="font-medium text-text">{analysisStatus}</span>
          </div>
          {analyzing && (
            <div className="flex items-center gap-2">
              <div className="w-32 h-1.5 rounded-full bg-border overflow-hidden">
                <div
                  className="h-full bg-text transition-all duration-300"
                  style={{ width: `${analysisProgress}%` }}
                />
              </div>
              <span className="font-mono text-muted text-[11px]">{analysisProgress}%</span>
            </div>
          )}
        </div>
      )}

      {/* Workspace Tabs matching exact design */}
      <div className="flex items-center gap-6 border-b border-border text-xs font-medium mt-4">
        {[
          { id: "overview", label: "Overview" },
          { id: "commits", label: "Commits" },
          { id: "files", label: "Files" },
          { id: "dependencies", label: "Dependencies" },
          { id: "coverage", label: "Coverage Objectives" },
          { id: "settings", label: "Settings" },
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

      {/* Tab: Commits (Authority Screenshot 03_Repository_Workspace.png) */}
      {activeTab === "commits" && (
        <div className="pt-4">
          {/* Commit Filters Toolbar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mb-6">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              {/* Branch Selector */}
              <div className="relative">
                <select
                  value={selectedBranch}
                  onChange={(e) => setSelectedBranch(e.target.value)}
                  className="appearance-none pl-8 pr-8 py-2 rounded-lg border border-border bg-surface text-xs font-medium text-text focus:outline-none focus:ring-1 focus:ring-text cursor-pointer"
                >
                  {branches.length > 0 ? (
                    branches.map((b) => (
                      <option key={b.name} value={b.name}>
                        {b.name}
                      </option>
                    ))
                  ) : (
                    <option value="main">main</option>
                  )}
                </select>
                <GitBranch className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted pointer-events-none" />
                <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted pointer-events-none" />
              </div>

              {/* Search Commits */}
              <div className="relative flex-1 sm:w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted" />
                <input
                  type="text"
                  value={searchCommitQuery}
                  onChange={(e) => setSearchCommitQuery(e.target.value)}
                  placeholder="Search commits..."
                  className="w-full pl-8 pr-3 py-2 rounded-lg border border-border bg-surface text-xs text-text placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-text"
                />
              </div>
            </div>

            <div className="relative self-end sm:self-auto">
              <select className="appearance-none pl-3 pr-8 py-2 rounded-lg border border-border bg-surface text-xs font-medium text-text focus:outline-none focus:ring-1 focus:ring-text cursor-pointer">
                <option>Last 30 days</option>
                <option>Last 7 days</option>
                <option>All time</option>
              </select>
              <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted pointer-events-none" />
            </div>
          </div>

          {/* Timeline of Commits matching screenshot layout */}
          {filteredCommits.length > 0 ? (
            <div className="relative border-l border-border ml-4 pl-6 space-y-5">
              {filteredCommits.map((c) => (
                <div key={c.hash || c.commit_sha} className="relative group">
                  {/* Timeline Dot */}
                  <div className="absolute -left-[31px] top-1.5 w-2.5 h-2.5 rounded-full bg-surface border-2 border-muted group-hover:border-text transition-colors" />

                  <div className="flex items-center justify-between p-3.5 rounded-xl border border-border bg-surface hover:bg-soft transition-colors shadow-xs">
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="mt-0.5 text-muted group-hover:text-text transition-colors">
                        <GitCommit className="w-4 h-4" />
                      </div>
                      <div className="min-w-0">
                        <div className="text-xs sm:text-sm font-medium text-text truncate">
                          {c.message}
                        </div>
                        <div className="text-[11px] text-muted mt-0.5">
                          {c.author} · {c.timestamp}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span className="font-mono text-[11px] px-2 py-0.5 rounded bg-soft text-muted border border-border">
                        {c.shortHash || (c.hash ? c.hash.slice(0, 7) : "commit")}
                      </span>
                      <button className="p-1 rounded text-muted hover:text-text">
                        <MoreVertical className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 rounded-xl border border-dashed border-border bg-soft text-center space-y-3">
              <GitCommit className="w-8 h-8 text-muted mx-auto" />
              <p className="text-xs font-medium text-text">No commits mined for this branch yet</p>
              <p className="text-[11px] text-muted max-w-sm mx-auto">
                Trigger an analysis run to safely mine commits, diffs, and ownership hotspots without executing repository code.
              </p>
              <button
                onClick={handleTriggerAnalysis}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90"
              >
                <Play className="w-3.5 h-3.5" />
                <span>Mine Commits Now</span>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Tab: Overview */}
      {activeTab === "overview" && (
        <div className="pt-6 space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              label="Risk score"
              value={`${repository.riskScore || 0} / 100`}
              sublabel="Deterministic assessment"
            />
            <StatCard
              label="Files indexed"
              value={complexityFiles.length > 0 ? complexityFiles.length : repository.fileCount || 0}
              sublabel="Python & TypeScript"
            />
            <StatCard
              label="Dependencies"
              value={dependencies ? dependencies.total_edges : 0}
              sublabel="Import graph edges"
            />
            <StatCard
              label="Coverage"
              value={coverage ? `${coverage.statement_coverage_pct}%` : "No data"}
              sublabel={coverage ? `${coverage.statements_covered}/${coverage.statements_total} lines` : "Ingest coverage report"}
            />
          </div>

          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-text mb-2">
              Repository Health Summary
            </h3>
            <p className="text-xs text-muted leading-relaxed">
              Branch <span className="font-mono text-text">{selectedBranch}</span> is monitored.
              {dependencies
                ? ` Dependency graph contains ${dependencies.total_nodes} nodes and ${dependencies.total_edges} edges with ${dependencies.circular_cycles.length} circular cycles detected.`
                : " Repository analysis has not been executed yet."}
              {coverage && ` Current statement coverage stands at ${coverage.statement_coverage_pct}% across ${coverage.files_count} indexed files.`}
            </p>
          </div>
        </div>
      )}

      {/* Tab: Files */}
      {activeTab === "files" && (
        <div className="pt-6">
          <div className="rounded-xl border border-border bg-surface overflow-hidden shadow-sm">
            <div className="p-4 border-b border-border flex items-center justify-between">
              <span className="text-xs font-semibold text-text">
                Indexed Source Files ({complexityFiles.length})
              </span>
              <span className="text-xs text-muted">Branch: {selectedBranch}</span>
            </div>
            {complexityFiles.length > 0 ? (
              <div className="divide-y divide-border text-xs">
                {complexityFiles.map((f) => (
                  <div key={f.file_path} className="flex items-center justify-between p-3.5 hover:bg-soft">
                    <div className="flex items-center gap-2 font-mono text-text">
                      <FileCode2 className="w-4 h-4 text-muted" />
                      <span>{f.file_path}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-muted text-[11px]">{f.lines_total} lines</span>
                      <span className="text-muted text-[11px]">Complexity: {f.cyclomatic_complexity}</span>
                      <span className="text-muted text-[11px]">MI: {f.maintainability_index}</span>
                      <Badge variant={f.cyclomatic_complexity > 5 ? "warning" : "success"}>
                        {f.language}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-muted space-y-2">
                <FileCode2 className="w-8 h-8 mx-auto text-muted" />
                <p>No source files analyzed yet for this repository.</p>
                <button
                  onClick={handleTriggerAnalysis}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-text text-surface text-xs font-medium"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Run Analysis</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab: Dependencies */}
      {activeTab === "dependencies" && (
        <div className="pt-6 space-y-4">
          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-text">
                Module Dependency & Import Graph
              </h3>
              {dependencies && (
                <div className="flex items-center gap-3 text-xs text-muted">
                  <span>{dependencies.total_nodes} nodes</span>
                  <span>·</span>
                  <span>{dependencies.total_edges} edges</span>
                  <span>·</span>
                  <span>{dependencies.internal_edges_count} internal</span>
                  <span>·</span>
                  <span>{dependencies.external_edges_count} external</span>
                </div>
              )}
            </div>

            {dependencies && dependencies.circular_cycles.length > 0 && (
              <div className="mb-4 p-3 rounded-lg border border-amber-200 dark:border-amber-900 bg-amber-50 dark:bg-amber-950/20 text-xs text-amber-800 dark:text-amber-300 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold">Circular Dependencies Detected:</span>
                  <ul className="list-disc list-inside mt-1 space-y-0.5 font-mono text-[11px]">
                    {dependencies.circular_cycles.map((c, i) => (
                      <li key={i}>{c.join(" → ")}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {dependencies && dependencies.edges.length > 0 ? (
              <div className="border border-border rounded-lg overflow-hidden divide-y divide-border text-xs">
                {dependencies.edges.slice(0, 20).map((e, idx) => (
                  <div key={idx} className="flex items-center justify-between p-3 hover:bg-soft">
                    <div className="flex items-center gap-2 font-mono text-text">
                      <span className="text-text">{e.source}</span>
                      <span className="text-muted">→</span>
                      <span className="font-semibold text-text">{e.target}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={e.is_external ? "neutral" : "success"} className="text-[10px]">
                        {e.is_external ? "External Package" : "Internal Module"}
                      </Badge>
                      <span className="text-muted text-[11px]">line {e.line}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-muted space-y-2">
                <Layers className="w-8 h-8 mx-auto text-muted" />
                <p>No dependency graph built yet for this repository.</p>
                <button
                  onClick={handleTriggerAnalysis}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-text text-surface text-xs font-medium"
                >
                  <Play className="w-3.5 h-3.5" />
                  <span>Build Dependency Graph</span>
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab: Coverage Objectives */}
      {activeTab === "coverage" && (
        <div className="pt-6 space-y-4">
          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-text">
                White-Box Coverage Inventory
              </h3>
              <p className="text-xs text-muted mt-1">
                Statement, branch, condition, MC/DC, basis path, loop, def-use, and exception targets.
              </p>
            </div>
            <Link
              href="/app/coverage"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90 transition-opacity"
            >
              <span>Open Coverage Matrix</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {coverage ? (
            <div className="rounded-xl border border-border bg-surface p-6 shadow-sm space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <StatCard
                  label="Statement Coverage"
                  value={`${coverage.statement_coverage_pct}%`}
                  sublabel={`${coverage.statements_covered} / ${coverage.statements_total} statements`}
                />
                <StatCard
                  label="Branch Coverage"
                  value={`${coverage.branch_coverage_pct}%`}
                  sublabel={`${coverage.branches_covered} / ${coverage.branches_total} branches`}
                />
                <StatCard
                  label="Format"
                  value={coverage.format_type}
                  sublabel="Ingested parser"
                />
                <StatCard
                  label="Files Indexed"
                  value={coverage.files_count}
                  sublabel="Coverage reports"
                />
              </div>

              <div className="border border-border rounded-lg overflow-hidden divide-y divide-border text-xs">
                {Object.entries(coverage.files).map(([fp, f]) => (
                  <div key={fp} className="flex items-center justify-between p-3 hover:bg-soft">
                    <span className="font-mono text-text">{fp}</span>
                    <div className="flex items-center gap-3">
                      <span className="text-muted text-[11px]">
                        {f.statements_covered}/{f.statements_total} covered
                      </span>
                      <Badge variant={f.coverage_pct >= 80 ? "success" : f.coverage_pct >= 50 ? "warning" : "error"}>
                        {f.coverage_pct}%
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-border bg-soft p-8 text-center text-xs text-muted space-y-2">
              <Target className="w-8 h-8 mx-auto text-muted" />
              <p className="font-medium text-text">No coverage report ingested yet</p>
              <p className="max-w-md mx-auto text-[11px]">
                ATIP never fakes coverage figures. Ingest standard Coverage.py JSON, LCOV, or Cobertura XML reports via API endpoint <span className="font-mono text-text">POST /repositories/{repoId}/coverage/ingest</span>.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Tab: Settings */}
      {activeTab === "settings" && (
        <div className="pt-6">
          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm max-w-xl space-y-4">
            <h3 className="text-sm font-semibold text-text">
              Repository Analysis Settings
            </h3>
            <div>
              <label className="text-xs font-medium text-muted block mb-1">
                Default Branch
              </label>
              <input
                type="text"
                defaultValue={repository.defaultBranch || "main"}
                className="w-full px-3 py-2 rounded-lg border border-border bg-surface text-xs text-text"
              />
            </div>
            <div>
              <label className="text-xs font-medium text-muted block mb-1">
                Webhook Event Filter
              </label>
              <input
                type="text"
                defaultValue="push, pull_request"
                className="w-full px-3 py-2 rounded-lg border border-border bg-surface text-xs text-text"
              />
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
