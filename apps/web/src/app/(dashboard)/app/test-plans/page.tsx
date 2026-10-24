"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { DEMO_TEST_PLANS, DEMO_REPOSITORIES } from "@/lib/fixtures";
import { api } from "@/lib/api-adapter";
import { TestSelectionResultApiItem } from "@/lib/api-client";
import { TestCaseItem } from "@/types";
import { Plus, ArrowRight, Check, X, ShieldCheck } from "lucide-react";

export default function TestPlansPage() {
  const initialPlan = DEMO_TEST_PLANS[0];
  const [activeTab, setActiveTab] = useState<"recommended" | "generated" | "approved">(
    "recommended"
  );
  
  const [testCases, setTestCases] = useState<Array<TestCaseItem & { selected: boolean }>>(
    initialPlan.testCases.map((tc) => ({ ...tc, selected: true }))
  );
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [generateModalOpen, setGenerateModalOpen] = useState(false);
  const [isApproved, setIsApproved] = useState(false);

  // Default to approved mock test cases matching 05_Test_Plans.png
  useEffect(() => {
    // Keep initialPlan.testCases matching authority 05_Test_Plans.png
  }, []);

  const selectedCount = testCases.filter((tc) => tc.selected).length;

  const toggleSelectAll = () => {
    const allSelected = selectedCount === testCases.length;
    setTestCases(testCases.map((tc) => ({ ...tc, selected: !allSelected })));
  };

  const toggleTestCase = (id: string) => {
    setTestCases(
      testCases.map((tc) =>
        tc.id === id ? { ...tc, selected: !tc.selected } : tc
      )
    );
  };

  const handleApprove = () => {
    setIsApproved(true);
    setReviewModalOpen(false);
  };

  return (
    <AppShell breadcrumbs={["Test Plans"]}>
      {/* Header matching 05_Test_Plans.png */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 pb-6">
        <div>
          <h1 className="font-serif text-3xl sm:text-4xl font-normal tracking-tight text-text">
            Test Plans
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-muted">
            AI-generated test plans based on code changes and risk analysis.
          </p>
        </div>

        <div>
          <button
            onClick={() => setGenerateModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-text text-surface font-medium text-xs hover:opacity-90 transition-opacity shadow-sm cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Generate Plan</span>
          </button>
        </div>
      </div>

      {/* Tabs matching 05_Test_Plans.png */}
      <div className="flex items-center gap-6 border-b border-border text-xs font-medium">
        <button
          onClick={() => setActiveTab("recommended")}
          className={`pb-3 -mb-px transition-colors cursor-pointer ${
            activeTab === "recommended"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          Recommended (12)
        </button>
        <button
          onClick={() => setActiveTab("generated")}
          className={`pb-3 -mb-px transition-colors cursor-pointer ${
            activeTab === "generated"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          Generated (6)
        </button>
        <button
          onClick={() => setActiveTab("approved")}
          className={`pb-3 -mb-px transition-colors cursor-pointer ${
            activeTab === "approved"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          Approved ({isApproved ? selectedCount : 4})
        </button>
      </div>

      {/* Test Cases Table matching 05_Test_Plans.png */}
      <div className="mt-6 rounded-xl border border-border bg-surface overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-border bg-soft/50 text-muted font-medium">
                <th className="py-3 px-4 w-10">
                  <input
                    type="checkbox"
                    checked={selectedCount === testCases.length && testCases.length > 0}
                    onChange={toggleSelectAll}
                    className="w-4 h-4 rounded border-border text-text focus:ring-0 cursor-pointer"
                  />
                </th>
                <th className="py-3 px-4 font-medium">Test Case</th>
                <th className="py-3 px-4 font-medium">Priority</th>
                <th className="py-3 px-4 font-medium">Type</th>
                <th className="py-3 px-4 font-medium">Target Component</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {testCases.map((tc) => (
                <tr
                  key={tc.id}
                  onClick={() => toggleTestCase(tc.id)}
                  className="hover:bg-soft transition-colors cursor-pointer"
                >
                  <td
                    className="py-3.5 px-4"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <input
                      type="checkbox"
                      checked={tc.selected}
                      onChange={() => toggleTestCase(tc.id)}
                      className="w-4 h-4 rounded border-border text-text focus:ring-0 cursor-pointer"
                    />
                  </td>
                  <td className="py-3.5 px-4 font-medium text-text">
                    {tc.title}
                  </td>
                  <td className="py-3.5 px-4">
                    <Badge
                      variant={
                        tc.priority === "High"
                          ? "error"
                          : tc.priority === "Medium"
                          ? "warning"
                          : "success"
                      }
                    >
                      {tc.priority}
                    </Badge>
                  </td>
                  <td className="py-3.5 px-4 text-muted">{tc.type}</td>
                  <td className="py-3.5 px-4 font-mono text-muted">
                    {tc.targetComponent}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Floating Bottom Action Bar matching 05_Test_Plans.png */}
      <div className="mt-6 flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-xl border border-border bg-surface shadow-md">
        <div className="text-xs font-medium text-text">
          <span className="font-semibold">{selectedCount}</span> test cases
          selected
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setReviewModalOpen(true)}
            className="px-4 py-2 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft transition-colors shadow-xs cursor-pointer flex items-center gap-1.5"
          >
            <span>Review</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => setReviewModalOpen(true)}
            className="px-4 py-2 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90 transition-opacity shadow-sm cursor-pointer"
          >
            Generate Tests
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
                <h3 className="text-sm font-semibold text-text">
                  Review &amp; Approve Plan ({initialPlan.id})
                </h3>
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
                Server-side role authorization requires Maintainer or Admin role
                to promote test plans from draft to approved execution status.
              </p>
              <div className="p-3 rounded-lg border border-border bg-soft font-mono text-[11px] text-text">
                Selected candidates: {selectedCount}
                <br />
                Target suite: nextjs-dashboard (branch: main)
                <br />
                Sandbox isolation: Default-deny network, CPU/RAM quotas enabled
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-border">
              <button
                onClick={() => setReviewModalOpen(false)}
                className="px-3 py-1.5 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleApprove}
                className="px-3.5 py-1.5 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90 cursor-pointer"
              >
                Approve &amp; Queue Run
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Generate Plan Notice */}
      {generateModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-xl border border-border bg-surface p-6 shadow-2xl">
            <h3 className="text-sm font-semibold text-text pb-2">
              Generate New Test Plan
            </h3>
            <p className="text-xs text-muted leading-relaxed pb-4">
              AI-assisted candidate test planning will analyze commit diffs and
              white-box coverage gaps in Phase M6.
            </p>
            <div className="flex justify-end">
              <button
                onClick={() => setGenerateModalOpen(false)}
                className="px-3 py-1.5 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft cursor-pointer"
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
