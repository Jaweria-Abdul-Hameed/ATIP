"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { StatCard } from "@/components/ui/stat-card";
import { DEMO_REPOSITORIES, DEMO_COMMITS } from "@/lib/fixtures";
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
} from "lucide-react";

export default function RepositoryWorkspacePage() {
  const params = useParams();
  const repoId = (params?.id as string) || "nextjs-dashboard";
  const repo =
    DEMO_REPOSITORIES.find((r) => r.id === repoId) || DEMO_REPOSITORIES[0];

  const [activeTab, setActiveTab] = useState<
    "commits" | "overview" | "files" | "dependencies" | "coverage" | "settings"
  >("commits");
  const [selectedBranch, setSelectedBranch] = useState("main");
  const [searchCommitQuery, setSearchCommitQuery] = useState("");
  const [syncing, setSyncing] = useState(false);

  const filteredCommits = DEMO_COMMITS.filter((c) =>
    c.message.toLowerCase().includes(searchCommitQuery.toLowerCase())
  );

  const handleSync = () => {
    setSyncing(true);
    setTimeout(() => setSyncing(false), 1200);
  };

  return (
    <AppShell breadcrumbs={["Repositories", repo.name]}>
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
            <h1 className="font-serif text-2xl sm:text-3xl font-normal tracking-tight text-text">
              {repo.name}
            </h1>
            <div className="flex items-center gap-2 text-xs text-muted mt-1">
              <span>{repo.fullName}</span>
              <a
                href={`https://github.com/${repo.fullName}`}
                target="_blank"
                rel="noreferrer"
                className="hover:text-text"
              >
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
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
                <button className="inline-flex items-center gap-2 px-3 py-2 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft cursor-pointer">
                  <GitBranch className="w-3.5 h-3.5 text-muted" />
                  <span>{selectedBranch}</span>
                  <ChevronDown className="w-3.5 h-3.5 text-muted" />
                </button>
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
          <div className="relative border-l border-border ml-4 pl-6 space-y-5">
            {filteredCommits.map((c) => (
              <div key={c.hash} className="relative group">
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
                      {c.shortHash}
                    </span>
                    <button className="p-1 rounded text-muted hover:text-text">
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Overview */}
      {activeTab === "overview" && (
        <div className="pt-6 space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Risk score" value={`${repo.riskScore} / 100`} sublabel="Elevated change impact" />
            <StatCard label="Files indexed" value={repo.fileCount} sublabel="Python & TypeScript" />
            <StatCard label="Tests discovered" value={repo.testCount} sublabel="Pytest & Vitest" />
            <StatCard label="Coverage" value={`${repo.coveragePercent}%`} sublabel="Imported reports" />
          </div>

          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-text mb-2">
              Repository Health Summary
            </h3>
            <p className="text-xs text-muted leading-relaxed">
              Branch <span className="font-mono text-text">main</span> was last
              indexed 2 hours ago. 3 files exceed the elevated change risk
              threshold. Static AST parsing discovered 312 white-box statement
              objectives.
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
                Indexed Source Files ({repo.fileCount})
              </span>
              <span className="text-xs text-muted">Branch: main</span>
            </div>
            <div className="divide-y divide-border text-xs">
              {[
                { path: "src/auth/session.ts", risk: "High", score: 92, cov: "42%" },
                { path: "src/api/payments.ts", risk: "High", score: 85, cov: "56%" },
                { path: "src/components/Dashboard.tsx", risk: "Medium", score: 68, cov: "61%" },
                { path: "src/lib/db.ts", risk: "Medium", score: 64, cov: "68%" },
                { path: "src/api/users.ts", risk: "Low", score: 38, cov: "84%" },
                { path: "src/utils/validation.ts", risk: "Low", score: 32, cov: "96%" },
              ].map((f) => (
                <div key={f.path} className="flex items-center justify-between p-3.5 hover:bg-soft">
                  <div className="flex items-center gap-2 font-mono text-text">
                    <FileCode2 className="w-4 h-4 text-muted" />
                    <span>{f.path}</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-muted">Coverage: {f.cov}</span>
                    <Badge variant={f.risk === "High" ? "error" : f.risk === "Medium" ? "warning" : "success"}>
                      Risk {f.score}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab: Dependencies */}
      {activeTab === "dependencies" && (
        <div className="pt-6">
          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-text mb-4">
              Module Dependency Graph (Flow Explorer)
            </h3>
            <div className="flex flex-wrap items-center justify-around gap-4 p-8 rounded-lg bg-soft border border-border">
              <div className="p-4 rounded-lg border border-border bg-surface text-center font-mono text-xs shadow-xs">
                API Layer
              </div>
              <span className="text-muted">→</span>
              <div className="p-4 rounded-lg border border-border bg-surface text-center font-mono text-xs shadow-xs">
                Auth Gateway
              </div>
              <span className="text-muted">→</span>
              <div className="p-4 rounded-lg border border-border bg-surface text-center font-mono text-xs shadow-xs">
                Session Store
              </div>
              <span className="text-muted">→</span>
              <div className="p-4 rounded-lg border border-border bg-surface text-center font-mono text-xs shadow-xs">
                Database Pool
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab: Coverage Objectives (Requirement M0-WB-02) */}
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
                defaultValue={repo.defaultBranch}
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
