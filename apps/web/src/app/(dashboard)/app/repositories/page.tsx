"use client";

import React, { useState } from "react";
import Link from "next/link";
import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { DEMO_REPOSITORIES } from "@/lib/fixtures";
import {
  Search,
  Plus,
  MoreVertical,
  ChevronDown,
  FolderGit2,
  FileCode2,
  RotateCw,
} from "lucide-react";

export default function RepositoriesPage() {
  const [activeTab, setActiveTab] = useState<"all" | "connected" | "syncing">(
    "all"
  );
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"lastSynced" | "riskScore" | "name">(
    "lastSynced"
  );
  const [showConnectModal, setShowConnectModal] = useState(false);

  const filteredRepos = DEMO_REPOSITORIES.filter((repo) => {
    const matchesSearch =
      repo.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      repo.fullName.toLowerCase().includes(searchQuery.toLowerCase());
    if (activeTab === "syncing") return matchesSearch && repo.status === "syncing";
    if (activeTab === "connected")
      return matchesSearch && (repo.status === "connected" || repo.status === "ready");
    return matchesSearch;
  });

  return (
    <AppShell breadcrumbs={["Repositories"]}>
      {/* Header matching 02_Repositories.png */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 pb-6">
        <div>
          <h1 className="font-serif text-3xl sm:text-4xl font-normal tracking-tight text-text">
            Repositories
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-muted">
            Connect and manage your GitHub repositories.
          </p>
        </div>

        <div>
          <button
            onClick={() => setShowConnectModal(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-text text-surface font-medium text-xs hover:opacity-90 transition-opacity shadow-sm cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Connect Repository</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-6 border-b border-border text-xs font-medium">
        <button
          onClick={() => setActiveTab("all")}
          className={`pb-3 -mb-px transition-colors relative cursor-pointer ${
            activeTab === "all"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          All ({DEMO_REPOSITORIES.length})
        </button>
        <button
          onClick={() => setActiveTab("connected")}
          className={`pb-3 -mb-px transition-colors relative cursor-pointer ${
            activeTab === "connected"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          Connected ({DEMO_REPOSITORIES.length})
        </button>
        <button
          onClick={() => setActiveTab("syncing")}
          className={`pb-3 -mb-px transition-colors relative cursor-pointer ${
            activeTab === "syncing"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          Syncing (0)
        </button>
      </div>

      {/* Search and Filters Toolbar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 my-5">
        <div className="relative w-full sm:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search repositories..."
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-border bg-surface text-xs text-text placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-text transition-all"
          />
        </div>

        <div className="flex items-center gap-2 self-end sm:self-auto">
          <div className="relative">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="appearance-none pl-3 pr-8 py-2 rounded-lg border border-border bg-surface text-xs font-medium text-text focus:outline-none focus:ring-1 focus:ring-text cursor-pointer"
            >
              <option value="lastSynced">Last synced</option>
              <option value="riskScore">Risk score</option>
              <option value="name">Name</option>
            </select>
            <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Repository Cards List */}
      <div className="space-y-3">
        {filteredRepos.length === 0 ? (
          <div className="text-center py-12 rounded-xl border border-border bg-surface text-muted text-xs">
            No repositories found matching your query.
          </div>
        ) : (
          filteredRepos.map((repo) => (
            <Link
              key={repo.id}
              href={`/app/repositories/${repo.id}`}
              className="flex items-center justify-between p-4 rounded-xl border border-border bg-surface hover:bg-soft transition-all shadow-xs group"
            >
              <div className="flex items-center gap-3.5 min-w-0">
                <div className="p-2.5 rounded-lg border border-border bg-soft text-text shrink-0">
                  <FileCode2 className="w-5 h-5 text-muted group-hover:text-text transition-colors" />
                </div>
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-text truncate">
                    {repo.name}
                  </div>
                  <div className="text-xs text-muted truncate mt-0.5">
                    {repo.fullName}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4 shrink-0">
                <div className="flex items-center gap-1.5 text-xs text-muted">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 inline-block" />
                  <span className="hidden sm:inline">Last synced</span>
                  <span>{repo.lastSynced}</span>
                </div>

                <button
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                  }}
                  className="p-1 rounded-md text-muted hover:text-text transition-colors"
                  aria-label="Repository options"
                >
                  <MoreVertical className="w-4 h-4" />
                </button>
              </div>
            </Link>
          ))
        )}
      </div>

      {/* Connect Repository Modal */}
      {showConnectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-xl border border-border bg-surface p-6 shadow-xl">
            <h3 className="text-sm font-semibold text-text pb-2">
              Connect Repository
            </h3>
            <p className="text-xs text-muted leading-relaxed pb-4">
              Real GitHub App installation integration is provisioned in Phase
              M2. Currently showing verified local workspace fixtures.
            </p>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowConnectModal(false)}
                className="px-3 py-1.5 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft"
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
