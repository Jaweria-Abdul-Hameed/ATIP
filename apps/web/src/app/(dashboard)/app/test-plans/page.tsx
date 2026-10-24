"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { DEMO_TEST_PLANS, DEMO_REPOSITORIES } from "@/lib/fixtures";
import { api } from "@/lib/api-adapter";
import {
  apiClient,
  TestSelectionResultApiItem,
  SelectedRegressionTestApiItem,
  TestGapApiItem,
} from "@/lib/api-client";
import {
  Plus,
  ArrowRight,
  Check,
  X,
  ShieldCheck,
  AlertTriangle,
  Flame,
  CheckCircle2,
  ChevronDown,
  RefreshCw,
  Layers,
} from "lucide-react";

export default function TestPlansPage() {
  const initialPlan = DEMO_TEST_PLANS[0];
  const [repositories, setRepositories] = useState<Array<{ id: string; name: string }>>([]);
  const [selectedRepoId, setSelectedRepoId] = useState<string>("");
  const [activeTab, setActiveTab] = useState<"recommended" | "gaps" | "flaky" | "approved">(
    "recommended"
  );
  
  const [loading, setLoading] = useState(false);
  const [testSelection, setTestSelection] = useState<TestSelectionResultApiItem | null>(null);
  const [selectedTests, setSelectedTests] = useState<Record<string, boolean>>({});

  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [generateModalOpen, setGenerateModalOpen] = useState(false);
  const [isApproved, setIsApproved] = useState(false);

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

  // Fetch impacted test selection whenever selected repo changes
  useEffect(() => {
    if (!selectedRepoId) return;

    let mounted = true;
    async function fetchSelection() {
      setLoading(true);
      try {
        const result = await api.getTestSelection(selectedRepoId);
        if (mounted) {
          if (result && (result.selected_tests.length > 0 || result.test_gaps.length > 0)) {
            setTestSelection(result);
            const initSelected: Record<string, boolean> = {};
            result.selected_tests.forEach((t) => {
              initSelected[t.test_file] = true;
            });
            setSelectedTests(initSelected);
          } else {
            setTestSelection(null);
          }
        }
      } catch {
        if (mounted) setTestSelection(null);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    fetchSelection();

    return () => {
      mounted = false;
    };
  }, [selectedRepoId]);

  const isLive = testSelection !== null;
  const currentTests = isLive ? testSelection.selected_tests : [];
  const testGaps = isLive ? testSelection.test_gaps : [];
  const flakyTests = isLive ? testSelection.flaky_tests : [];

  const selectedCount = isLive
    ? Object.values(selectedTests).filter(Boolean).length
    : initialPlan.testCases.length;

  const toggleSelectAll = () => {
    if (!isLive) return;
    const allSelected = selectedCount === currentTests.length;
    const updated: Record<string, boolean> = {};
    currentTests.forEach((t) => {
      updated[t.test_file] = !allSelected;
    });
    setSelectedTests(updated);
  };

  const toggleTest = (file: string) => {
    setSelectedTests((prev) => ({ ...prev, [file]: !prev[file] }));
  };

  return (
    <AppShell breadcrumbs={["Test Plans"]}>
      {/* Header matching 05_Test_Plans.png */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 pb-6 border-b border-border/50">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-serif text-3xl sm:text-4xl font-normal tracking-tight text-text">
              Test Plans
            </h1>
            <Badge variant={isLive ? "success" : "neutral"} className="text-[10px]">
              {isLive ? "Live Impact Intelligence" : "Demo Fixture"}
            </Badge>
          </div>
          <p className="mt-1 text-xs sm:text-sm text-muted">
            Change-impact test selection, coverage gap identification, and flaky test mitigation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Repository Selector */}
          <div className="relative">
            <select
              value={selectedRepoId}
              onChange={(e) => setSelectedRepoId(e.target.value)}
              className="appearance-none bg-surface border border-border px-3 py-2 pr-7 rounded-lg text-xs font-medium text-text focus:outline-none cursor-pointer"
            >
              {repositories.map((r) => (
                <option key={r.id} value={r.id} className="bg-surface text-text">
                  {r.name}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted pointer-events-none" />
          </div>

          <button
            onClick={() => setGenerateModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-text text-surface font-medium text-xs hover:opacity-90 transition-opacity shadow-sm cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Generate Plan</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-6 border-b border-border text-xs font-medium my-4">
        <button
          onClick={() => setActiveTab("recommended")}
          className={`pb-3 -mb-px transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeTab === "recommended"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Recommended ({isLive ? currentTests.length : 12})</span>
        </button>
        <button
          onClick={() => setActiveTab("gaps")}
          className={`pb-3 -mb-px transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeTab === "gaps"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
          <span>Test Gaps ({isLive ? testGaps.length : 3})</span>
        </button>
        <button
          onClick={() => setActiveTab("flaky")}
          className={`pb-3 -mb-px transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeTab === "flaky"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          <Flame className="w-3.5 h-3.5 text-red-500" />
          <span>Flaky Signals ({isLive ? flakyTests.length : 1})</span>
        </button>
        <button
          onClick={() => setActiveTab("approved")}
          className={`pb-3 -mb-px transition-colors cursor-pointer flex items-center gap-1.5 ${
            activeTab === "approved"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
          <span>Approved ({isApproved ? selectedCount : 4})</span>
        </button>
      </div>

      {/* Recommended Tab View */}
      {activeTab === "recommended" && (
        <div className="mt-4 rounded-xl border border-border bg-surface overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-border bg-soft/50 text-muted font-medium">
                  <th className="py-3 px-4 w-10">
                    <input
                      type="checkbox"
                      checked={isLive ? selectedCount === currentTests.length && currentTests.length > 0 : true}
                      onChange={toggleSelectAll}
                      className="w-4 h-4 rounded border-border text-text focus:ring-0 cursor-pointer"
                    />
                  </th>
                  <th className="py-3 px-4 font-medium">Selected Test Suite</th>
                  <th className="py-3 px-4 font-medium">Priority</th>
                  <th className="py-3 px-4 font-medium">Selection Reason</th>
                  <th className="py-3 px-4 font-medium">Target Component</th>
                  <th className="py-3 px-4 text-center">Depth</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {isLive ? (
                  currentTests.map((t) => (
                    <tr
                      key={t.test_file}
                      onClick={() => toggleTest(t.test_file)}
                      className="hover:bg-soft transition-colors cursor-pointer"
                    >
                      <td className="py-3.5 px-4" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="checkbox"
                          checked={!!selectedTests[t.test_file]}
                          onChange={() => toggleTest(t.test_file)}
                          className="w-4 h-4 rounded border-border text-text focus:ring-0 cursor-pointer"
                        />
                      </td>
                      <td className="py-3.5 px-4 font-medium font-mono text-text">
                        {t.test_file}
                        {t.is_flaky_candidate && (
                          <span className="ml-2 inline-flex items-center gap-0.5 text-[10px] text-amber-500 font-sans">
                            <Flame className="w-3 h-3" /> Flaky Signal
                          </span>
                        )}
                      </td>
                      <td className="py-3.5 px-4">
                        <Badge
                          variant={
                            t.priority === "critical"
                              ? "error"
                              : t.priority === "high"
                              ? "warning"
                              : "success"
                          }
                        >
                          {t.priority.toUpperCase()}
                        </Badge>
                      </td>
                      <td className="py-3.5 px-4 text-muted">{t.selection_reason}</td>
                      <td className="py-3.5 px-4 font-mono text-muted">{t.target_file}</td>
                      <td className="py-3.5 px-4 text-center font-mono text-muted">{t.depth}</td>
                    </tr>
                  ))
                ) : (
                  initialPlan.testCases.map((tc) => (
                    <tr key={tc.id} className="hover:bg-soft transition-colors cursor-pointer">
                      <td className="py-3.5 px-4">
                        <input
                          type="checkbox"
                          defaultChecked
                          className="w-4 h-4 rounded border-border text-text focus:ring-0 cursor-pointer"
                        />
                      </td>
                      <td className="py-3.5 px-4 font-medium text-text">{tc.title}</td>
                      <td className="py-3.5 px-4">
                        <Badge variant={tc.priority === "High" ? "error" : "warning"}>
                          {tc.priority}
                        </Badge>
                      </td>
                      <td className="py-3.5 px-4 text-muted">{tc.type}</td>
                      <td className="py-3.5 px-4 font-mono text-muted">{tc.targetComponent}</td>
                      <td className="py-3.5 px-4 text-center text-muted font-mono">1</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Test Gaps View */}
      {activeTab === "gaps" && (
        <div className="mt-4 rounded-xl border border-border bg-surface overflow-hidden shadow-sm">
          <div className="p-4 border-b border-border bg-soft/30">
            <h3 className="text-xs font-semibold text-text uppercase tracking-wider">
              Identified Test Gaps (Missing Regression Coverage)
            </h3>
            <p className="text-xs text-muted mt-0.5">
              Files altered or impacted in blast radius that lack corresponding unit or integration test suites.
            </p>
          </div>
          <div className="divide-y divide-border text-xs">
            {testGaps.length > 0 ? (
              testGaps.map((gap, i) => (
                <div key={i} className="p-4 flex items-center justify-between gap-4 hover:bg-soft">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold text-text">{gap.file_path}</span>
                      <Badge variant={gap.severity === "critical" ? "error" : "warning"}>
                        Score: {gap.risk_score}
                      </Badge>
                      <Badge variant="neutral">{gap.gap_type}</Badge>
                    </div>
                    <p className="text-xs text-muted mt-1">{gap.recommendation}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-[11px] text-muted block font-mono">
                      {gap.impacted_dependents_count} dependents
                    </span>
                    <button
                      onClick={() => setGenerateModalOpen(true)}
                      className="mt-1 px-2.5 py-1 rounded border border-border text-xs text-text hover:bg-surface font-medium cursor-pointer"
                    >
                      Propose Test
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-muted">
                No test gaps identified. All impacted components have associated regression tests.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Flaky Candidates View */}
      {activeTab === "flaky" && (
        <div className="mt-4 rounded-xl border border-border bg-surface overflow-hidden shadow-sm">
          <div className="p-4 border-b border-border bg-soft/30">
            <h3 className="text-xs font-semibold text-text uppercase tracking-wider">
              Flakiness Vulnerability Analysis
            </h3>
            <p className="text-xs text-muted mt-0.5">
              Tests flagged for potential non-deterministic timing, thread sleeping, or dynamic state drift.
            </p>
          </div>
          <div className="divide-y divide-border text-xs">
            {flakyTests.length > 0 ? (
              flakyTests.map((flk, i) => (
                <div key={i} className="p-4 flex items-center justify-between gap-4 hover:bg-soft">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-semibold text-text">{flk.test_file}</span>
                      <Badge variant="error">Flakiness Score: {Math.round(flk.flakiness_score * 100)}%</Badge>
                    </div>
                    <ul className="mt-1 list-disc list-inside text-muted space-y-0.5 text-[11px]">
                      {flk.flakiness_reasons.map((r, ri) => (
                        <li key={ri}>{r}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-muted">
                No flaky patterns detected in selected regression suite.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Approved Tab View */}
      {activeTab === "approved" && (
        <div className="mt-4 p-8 rounded-xl border border-border bg-surface text-center">
          <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
          <h3 className="text-sm font-semibold text-text">Approved Test Plan Ready</h3>
          <p className="text-xs text-muted mt-1 max-w-md mx-auto">
            {isApproved
              ? `${selectedCount} selected regression tests have been human-approved for sandbox execution.`
              : "Default test suite approved for regression verification."}
          </p>
        </div>
      )}

      {/* Floating Bottom Action Bar */}
      <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-xl border border-border bg-surface shadow-md">
        <div className="text-xs font-medium text-text">
          <span className="font-semibold">{selectedCount}</span> test cases selected
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setReviewModalOpen(true)}
            className="px-4 py-2 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft transition-colors shadow-xs cursor-pointer flex items-center gap-1.5"
          >
            <span>Review Plan</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => {
              setIsApproved(true);
              setActiveTab("approved");
            }}
            className="px-4 py-2 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90 transition-opacity shadow-sm cursor-pointer"
          >
            Approve Plan
          </button>
        </div>
      </div>

      {/* Review Modal */}
      {reviewModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
          <div className="w-full max-w-lg rounded-xl border border-border bg-surface p-6 shadow-2xl">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-emerald-500" />
                <h3 className="text-sm font-semibold text-text">Review Test Plan</h3>
              </div>
              <button
                onClick={() => setReviewModalOpen(false)}
                className="text-muted hover:text-text p-1 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="py-4 space-y-3 text-xs text-muted">
              <p>
                This test plan targets {selectedCount} regression tests across changed modules and transitive
                dependents within repository <span className="font-mono text-text">{selectedRepoId}</span>.
              </p>
              <div className="p-3 rounded-lg border border-border bg-soft space-y-1 font-mono text-[11px]">
                <div>Selected Tests: {selectedCount}</div>
                <div>Impacted Gaps Flagged: {testGaps.length}</div>
                <div>Isolation Policy: Hardened ephemeral sandbox</div>
              </div>
            </div>

            <div className="pt-3 border-t border-border flex justify-end gap-2">
              <button
                onClick={() => setReviewModalOpen(false)}
                className="px-3.5 py-2 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setIsApproved(true);
                  setReviewModalOpen(false);
                  setActiveTab("approved");
                }}
                className="px-3.5 py-2 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90 cursor-pointer"
              >
                Approve & Schedule
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
