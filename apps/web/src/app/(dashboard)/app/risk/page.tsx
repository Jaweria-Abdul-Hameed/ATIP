"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { DEMO_RISK_FILES, DEMO_REPOSITORIES } from "@/lib/fixtures";
import { api } from "@/lib/api-adapter";
import {
  apiClient,
  FileRiskAssessmentApiItem,
  RiskAssessmentSummaryApiItem,
  ChangeImpactNodeApiItem,
} from "@/lib/api-client";
import {
  Download,
  ChevronDown,
  ChevronRight,
  X,
  AlertTriangle,
  ShieldAlert,
  Info,
  RefreshCw,
  GitBranch,
  Layers,
  Activity,
  CheckCircle2,
  FileText,
} from "lucide-react";

export default function RiskIntelligencePage() {
  const [repositories, setRepositories] = useState<Array<{ id: string; name: string }>>([]);
  const [selectedRepoId, setSelectedRepoId] = useState<string>("");
  const [selectedBranch, setSelectedBranch] = useState("main");
  const [selectedTimeRange, setSelectedTimeRange] = useState("Last 30 days");
  
  const [loading, setLoading] = useState(false);
  const [recomputing, setRecomputing] = useState(false);
  const [liveAssessment, setLiveAssessment] = useState<RiskAssessmentSummaryApiItem | null>(null);
  const [impactNodes, setImpactNodes] = useState<ChangeImpactNodeApiItem[]>([]);
  const [selectedFile, setSelectedFile] = useState<FileRiskAssessmentApiItem | null>(null);
  const [activeView, setActiveView] = useState<"files" | "impact">("files");

  // Load repositories on mount
  useEffect(() => {
    async function loadRepos() {
      try {
        const repos = await api.getRepositories();
        if (repos && repos.length > 0) {
          setRepositories(repos.map((r) => ({ id: r.id, name: r.name })));
          setSelectedRepoId(repos[0].id);
        } else {
          setRepositories(DEMO_REPOSITORIES.map((r) => ({ id: r.id, name: r.name })));
          setSelectedRepoId(DEMO_REPOSITORIES[0].id);
        }
      } catch {
        setRepositories(DEMO_REPOSITORIES.map((r) => ({ id: r.id, name: r.name })));
        setSelectedRepoId(DEMO_REPOSITORIES[0].id);
      }
    }
    loadRepos();
  }, []);

  // Fetch risk assessment whenever selectedRepoId or selectedBranch changes
  useEffect(() => {
    if (!selectedRepoId) return;

    let mounted = true;
    async function fetchRisk() {
      setLoading(true);
      try {
        const summary = await api.getRisks(selectedRepoId, { branch: selectedBranch });
        if (mounted) {
          if (summary && summary.files && summary.files.length > 0) {
            setLiveAssessment(summary);
          } else {
            setLiveAssessment(null);
          }
        }
      } catch (err) {
        console.warn("Failed fetching live risk assessment:", err);
        if (mounted) setLiveAssessment(null);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    fetchRisk();

    return () => {
      mounted = false;
    };
  }, [selectedRepoId, selectedBranch]);

  const handleTriggerRecompute = async () => {
    if (!selectedRepoId) return;
    setRecomputing(true);
    try {
      const fresh = await apiClient.evaluateRepositoryRisks(selectedRepoId, {
        branch: selectedBranch,
        force_recompute: true,
      });
      setLiveAssessment(fresh);
    } catch (err) {
      console.error("Failed to recompute risks:", err);
    } finally {
      setRecomputing(false);
    }
  };

  const handleExport = () => {
    const filesToExport = liveAssessment
      ? liveAssessment.files.map((f) => ({
          path: f.file_path,
          score: f.risk_score,
          tier: f.risk_tier,
          factors: f.factors.map((fc) => `${fc.name}: ${fc.impact}`).join("; "),
          confidence: `${Math.round(f.confidence * 100)}%`,
        }))
      : DEMO_RISK_FILES.map((f) => ({
          path: f.filePath,
          score: f.riskScore,
          tier: f.severity,
          factors: f.riskFactors,
          confidence: "95%",
        }));

    const csvContent =
      "data:text/csv;charset=utf-8," +
      ["File,Risk Score,Tier,Risk Factors,Confidence"]
        .concat(
          filesToExport.map(
            (f) => `"${f.path}",${f.score},"${f.tier}","${f.factors}","${f.confidence}"`
          )
        )
        .join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `atip-risk-${selectedRepoId || "export"}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const isLive = liveAssessment !== null && liveAssessment.files.length > 0;
  const filesList = isLive ? liveAssessment.files : [];

  return (
    <AppShell breadcrumbs={["Risk Intelligence"]}>
      {/* Header matching 04_Risk_Intelligence.png */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 pb-6 border-b border-border/50">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-serif text-3xl sm:text-4xl font-normal tracking-tight text-text">
              Risk Intelligence
            </h1>
            <Badge variant={isLive ? "success" : "neutral"} className="text-[10px]">
              {isLive ? `Live: ${liveAssessment.model_version}` : "Demo Fixture"}
            </Badge>
          </div>
          <p className="mt-1 text-xs sm:text-sm text-muted">
            Deterministic explainable defect-risk engine with change-impact propagation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isLive && (
            <button
              onClick={handleTriggerRecompute}
              disabled={recomputing}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft transition-colors shadow-xs cursor-pointer disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-muted ${recomputing ? "animate-spin" : ""}`} />
              <span>{recomputing ? "Evaluating..." : "Re-evaluate"}</span>
            </button>
          )}
          <button
            onClick={handleExport}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft transition-colors shadow-xs cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-muted" />
            <span>Export</span>
          </button>
        </div>
      </div>

      {/* Filter Dropdowns */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 my-4">
        {/* Repository Selector */}
        <div className="p-3 rounded-xl border border-border bg-surface">
          <label className="block text-[11px] font-medium text-muted mb-1">
            Repository
          </label>
          <div className="relative">
            <select
              value={selectedRepoId}
              onChange={(e) => setSelectedRepoId(e.target.value)}
              className="w-full appearance-none bg-transparent text-xs font-medium text-text focus:outline-none cursor-pointer pr-6"
            >
              {repositories.map((r) => (
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

      {/* Model Overview & Feature Weights Summary */}
      {isLive && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 my-4">
          <div className="p-4 rounded-xl border border-border bg-surface">
            <div className="text-[11px] font-medium text-muted uppercase tracking-wider">Repository Risk</div>
            <div className="flex items-baseline gap-2 mt-1.5">
              <span className="font-serif text-3xl font-normal text-text">{liveAssessment.overall_score}</span>
              <span className="text-xs text-muted">/ 100</span>
              <Badge
                variant={
                  liveAssessment.risk_tier === "critical"
                    ? "error"
                    : liveAssessment.risk_tier === "high"
                    ? "warning"
                    : liveAssessment.risk_tier === "medium"
                    ? "warning"
                    : "success"
                }
              >
                {liveAssessment.risk_tier.toUpperCase()}
              </Badge>
            </div>
            <div className="text-[11px] text-muted mt-2">
              Hotspot composite (70% top 10%, 30% median)
            </div>
          </div>

          <div className="p-4 rounded-xl border border-border bg-surface">
            <div className="text-[11px] font-medium text-muted uppercase tracking-wider">Model Confidence</div>
            <div className="flex items-baseline gap-2 mt-1.5">
              <span className="font-serif text-3xl font-normal text-text">
                {Math.round(liveAssessment.confidence * 100)}%
              </span>
              {liveAssessment.has_missing_data && (
                <Badge variant="warning" className="text-[10px]">Missing Data Fallback</Badge>
              )}
            </div>
            <div className="text-[11px] text-muted mt-2">
              Weighted factor completeness
            </div>
          </div>

          <div className="p-4 rounded-xl border border-border bg-surface">
            <div className="text-[11px] font-medium text-muted uppercase tracking-wider">Files Assessed</div>
            <div className="flex items-baseline gap-2 mt-1.5">
              <span className="font-serif text-3xl font-normal text-text">
                {liveAssessment.summary_stats.files_analyzed || liveAssessment.files.length}
              </span>
              <span className="text-xs text-muted">
                ({liveAssessment.summary_stats.critical_risk_count || 0} critical, {liveAssessment.summary_stats.high_risk_count || 0} high)
              </span>
            </div>
            <div className="text-[11px] text-muted mt-2">
              Evaluated commit: {liveAssessment.commit_sha.slice(0, 8)}
            </div>
          </div>

          <div className="p-4 rounded-xl border border-border bg-surface">
            <div className="text-[11px] font-medium text-muted uppercase tracking-wider">Deterministic Weights</div>
            <div className="space-y-1 mt-1.5 text-[11px] text-muted font-mono">
              <div className="flex justify-between"><span>Complexity:</span> <span>25%</span></div>
              <div className="flex justify-between"><span>Churn & Volume:</span> <span>25%</span></div>
              <div className="flex justify-between"><span>Blast Radius:</span> <span>25%</span></div>
              <div className="flex justify-between"><span>Coverage Gap:</span> <span>15%</span></div>
              <div className="flex justify-between"><span>Defect History:</span> <span>10%</span></div>
            </div>
          </div>
        </div>
      )}

      {/* View Toggle Tabs */}
      <div className="flex items-center gap-6 border-b border-border text-xs font-medium my-4">
        <button
          onClick={() => setActiveView("files")}
          className={`pb-2.5 -mb-px transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeView === "files"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Ranked Files ({isLive ? filesList.length : DEMO_RISK_FILES.length})</span>
        </button>
        {isLive && liveAssessment.impacted_nodes && liveAssessment.impacted_nodes.length > 0 && (
          <button
            onClick={() => setActiveView("impact")}
            className={`pb-2.5 -mb-px transition-colors cursor-pointer flex items-center gap-1.5 ${
              activeView === "impact"
                ? "text-text font-semibold border-b-2 border-text"
                : "text-muted hover:text-text"
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Change Impact Graph ({liveAssessment.impacted_nodes.length} nodes)</span>
          </button>
        )}
      </div>

      {/* Main Table View */}
      {activeView === "files" ? (
        <div className="mt-4 rounded-xl border border-border bg-surface overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-border bg-soft/50 text-muted font-medium">
                  <th className="py-3 px-4 font-medium">File / Component</th>
                  <th className="py-3 px-4 font-medium text-center">Risk Score</th>
                  <th className="py-3 px-4 font-medium">Primary Risk Drivers</th>
                  <th className="py-3 px-4 font-medium text-center">Blast Radius</th>
                  <th className="py-3 px-4 font-medium text-right">Confidence</th>
                  <th className="py-3 px-4 text-center"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {isLive ? (
                  filesList.map((file) => (
                    <tr
                      key={file.file_path}
                      onClick={() => setSelectedFile(file)}
                      className="hover:bg-soft transition-colors cursor-pointer group"
                    >
                      <td className="py-3.5 px-4 font-mono text-text">
                        <div className="font-semibold">{file.file_path}</div>
                        {file.has_missing_data && (
                          <div className="text-[10px] text-amber-500 font-sans mt-0.5">
                            * Missing: {file.missing_reasons[0]}
                          </div>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <div className="inline-flex items-center gap-2">
                          <span className="font-serif text-base font-normal text-text">
                            {file.risk_score}
                          </span>
                          <Badge
                            variant={
                              file.risk_tier === "critical"
                                ? "error"
                                : file.risk_tier === "high"
                                ? "warning"
                                : file.risk_tier === "medium"
                                ? "warning"
                                : "success"
                            }
                          >
                            {file.risk_tier.toUpperCase()}
                          </Badge>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-muted">
                        <div className="space-y-0.5">
                          {file.factors
                            .filter((f) => f.normalized_score >= 50)
                            .slice(0, 2)
                            .map((f, i) => (
                              <div key={i} className="text-[11px] truncate max-w-md">
                                <span className="font-medium text-text">{f.name}:</span> {f.description}
                              </div>
                            ))}
                          {file.factors.filter((f) => f.normalized_score >= 50).length === 0 && (
                            <span className="text-[11px] text-muted italic">All factors within low thresholds</span>
                          )}
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-center text-muted">
                        <span className="font-mono text-text">{file.direct_dependents_count}</span> direct
                        {file.transitive_dependents_count > file.direct_dependents_count && (
                          <span className="text-[10px] block text-muted">({file.transitive_dependents_count} transitive)</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 text-right text-muted font-mono">
                        {Math.round(file.confidence * 100)}%
                      </td>
                      <td className="py-3.5 px-4 text-center text-muted group-hover:text-text">
                        <ChevronRight className="w-4 h-4 inline" />
                      </td>
                    </tr>
                  ))
                ) : (
                  DEMO_RISK_FILES.map((file) => (
                    <tr
                      key={file.id}
                      onClick={() => {}}
                      className="hover:bg-soft transition-colors cursor-pointer group"
                    >
                      <td className="py-3.5 px-4 font-mono text-text">{file.filePath}</td>
                      <td className="py-3.5 px-4 text-center">
                        <div className="inline-flex items-center gap-2">
                          <span className="font-serif text-base font-normal text-text">{file.riskScore}</span>
                          <Badge variant={file.severity === "high" ? "error" : "warning"}>
                            {file.severity.toUpperCase()}
                          </Badge>
                        </div>
                      </td>
                      <td className="py-3.5 px-4 text-muted">{file.riskFactors}</td>
                      <td className="py-3.5 px-4 text-center text-muted font-mono">3 direct</td>
                      <td className="py-3.5 px-4 text-right text-muted">{file.lastChanged}</td>
                      <td className="py-3.5 px-4 text-center text-muted group-hover:text-text">
                        <ChevronRight className="w-4 h-4 inline" />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* Change Impact Propagation Graph View */
        <div className="mt-4 rounded-xl border border-border bg-surface overflow-hidden shadow-sm p-4">
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-text">Transitive Change-Impact Propagation</h3>
            <p className="text-xs text-muted">
              Bounded BFS traversal tracking downstream files affected by changes, with decay factor per hop.
            </p>
          </div>
          <div className="space-y-3">
            {liveAssessment?.impacted_nodes?.map((node, i) => (
              <div
                key={i}
                className="p-3.5 rounded-lg border border-border bg-soft flex items-center justify-between gap-4"
              >
                <div className="flex items-center gap-3">
                  <Badge variant={node.is_direct ? "error" : "warning"}>
                    {node.is_direct ? "Direct Change" : `Hop Depth ${node.depth}`}
                  </Badge>
                  <div>
                    <span className="font-mono text-xs font-semibold text-text">{node.file_path}</span>
                    <p className="text-[11px] text-muted mt-0.5">{node.propagation_reason}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-mono font-medium text-text">
                    Impact: {node.impact_score.toFixed(1)}%
                  </div>
                  {node.imported_by.length > 0 && (
                    <div className="text-[10px] text-muted">
                      via {node.imported_by.slice(0, 2).join(", ")}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Detail Drawer for Selected File with Explainable Factor Breakdown */}
      {selectedFile && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/40 backdrop-blur-xs">
          <div className="w-full max-w-xl bg-surface border-l border-border h-full p-6 overflow-y-auto shadow-2xl flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-border">
              <div>
                <div className="text-[11px] font-semibold text-muted uppercase tracking-wider">
                  Risk Evidence & Factor Breakdown
                </div>
                <h3 className="font-mono text-sm font-semibold text-text mt-1 break-all">
                  {selectedFile.file_path}
                </h3>
              </div>
              <button
                onClick={() => setSelectedFile(null)}
                className="p-1.5 rounded-lg border border-border text-muted hover:text-text cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="py-6 space-y-6 flex-1">
              {/* Score & Confidence Overview */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3.5 rounded-xl border border-border bg-soft">
                  <div className="text-[11px] text-muted">Risk Score</div>
                  <div className="text-2xl font-serif font-normal text-text mt-1">
                    {selectedFile.risk_score} <span className="text-xs font-sans text-muted">/ 100</span>
                  </div>
                </div>
                <div className="p-3.5 rounded-xl border border-border bg-soft">
                  <div className="text-[11px] text-muted">Severity Tier</div>
                  <div className="mt-1.5">
                    <Badge variant={selectedFile.risk_tier === "critical" ? "error" : "warning"}>
                      {selectedFile.risk_tier.toUpperCase()}
                    </Badge>
                  </div>
                </div>
                <div className="p-3.5 rounded-xl border border-border bg-soft">
                  <div className="text-[11px] text-muted">Confidence</div>
                  <div className="text-2xl font-serif font-normal text-text mt-1">
                    {Math.round(selectedFile.confidence * 100)}%
                  </div>
                </div>
              </div>

              {/* Missing data warnings if present */}
              {selectedFile.has_missing_data && (
                <div className="p-3.5 rounded-xl border border-amber-500/30 bg-amber-500/5 text-xs text-amber-600 dark:text-amber-400">
                  <div className="flex items-center gap-1.5 font-semibold mb-1">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Missing Evidence Handled Honestly</span>
                  </div>
                  <ul className="list-disc list-inside space-y-0.5 text-[11px]">
                    {selectedFile.missing_reasons.map((r, i) => (
                      <li key={i}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 5 Explainable Factor Cards */}
              <div>
                <h4 className="text-xs font-semibold text-text uppercase tracking-wider mb-3">
                  Explainable Factor Contribution
                </h4>
                <div className="space-y-3">
                  {selectedFile.factors.map((factor) => (
                    <div
                      key={factor.factor_key}
                      className="p-3.5 rounded-xl border border-border bg-soft/70 space-y-1.5"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-text">{factor.name}</span>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-muted text-[11px]">
                            wt: {factor.weight} | pts: +{factor.weighted_score.toFixed(1)}
                          </span>
                          <Badge
                            variant={
                              factor.impact === "critical"
                                ? "error"
                                : factor.impact === "high"
                                ? "warning"
                                : factor.impact === "medium"
                                ? "warning"
                                : "success"
                            }
                          >
                            {factor.impact.toUpperCase()}
                          </Badge>
                        </div>
                      </div>
                      <p className="text-xs text-muted">{factor.description}</p>
                      {factor.is_missing && factor.missing_reason && (
                        <div className="text-[10px] text-amber-500 italic">
                          Fallback: {factor.missing_reason}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Underlying Mined Signals */}
              <div>
                <h4 className="text-xs font-semibold text-text uppercase tracking-wider mb-2">
                  Mined Telemetry
                </h4>
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="p-2.5 rounded-lg border border-border bg-surface">
                    <span className="text-muted block text-[10px]">Cyclomatic CC:</span>
                    <span className="text-text font-medium">
                      {selectedFile.cyclomatic_complexity != null ? selectedFile.cyclomatic_complexity : "N/A (unparsed)"}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg border border-border bg-surface">
                    <span className="text-muted block text-[10px]">Maintainability Index:</span>
                    <span className="text-text font-medium">
                      {selectedFile.maintainability_index != null ? `${selectedFile.maintainability_index.toFixed(1)} / 100` : "N/A"}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg border border-border bg-surface">
                    <span className="text-muted block text-[10px]">Historical Churn:</span>
                    <span className="text-text font-medium">
                      {selectedFile.churn_count} commits ({selectedFile.lines_changed} lines)
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg border border-border bg-surface">
                    <span className="text-muted block text-[10px]">Blast Radius:</span>
                    <span className="text-text font-medium">
                      {selectedFile.direct_dependents_count} direct, {selectedFile.transitive_dependents_count} transitive
                    </span>
                  </div>
                  <div className="p-2.5 rounded-lg border border-border bg-surface">
                    <span className="text-muted block text-[10px]">Bug-fix Commits:</span>
                    <span className="text-text font-medium">{selectedFile.defect_commit_count} commits</span>
                  </div>
                  <div className="p-2.5 rounded-lg border border-border bg-surface">
                    <span className="text-muted block text-[10px]">Associated Tests:</span>
                    <span className="text-text font-medium">
                      {selectedFile.associated_tests.length > 0
                        ? `${selectedFile.associated_tests.length} test files`
                        : "None (Coverage Gap)"}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-border flex justify-end gap-2">
              <button
                onClick={() => setSelectedFile(null)}
                className="px-3.5 py-2 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft cursor-pointer"
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
