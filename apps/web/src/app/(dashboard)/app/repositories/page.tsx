"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api-adapter";
import { DiscoveredRepositoryApiItem } from "@/lib/api-client";
import { Repository } from "@/types";
import {
  Search,
  Plus,
  ChevronDown,
  FolderGit2,
  FileCode2,
  RotateCw,
  X,
  Database,
  Server,
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
  const [useLiveBackend, setUseLiveBackend] = useState(true);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [discoveredRepos, setDiscoveredRepos] = useState<DiscoveredRepositoryApiItem[]>([]);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [isConnecting, setIsConnecting] = useState<number | null>(null);

  const fetchDiscovered = async () => {
    setIsDiscovering(true);
    try {
      const items = await api.discoverRepositories();
      setDiscoveredRepos(items);
    } catch {
      setDiscoveredRepos([]);
    } finally {
      setIsDiscovering(false);
    }
  };

  useEffect(() => {
    if (showConnectModal) {
      fetchDiscovered();
    }
  }, [showConnectModal]);

  const handleConnect = async (repo: DiscoveredRepositoryApiItem) => {
    setIsConnecting(repo.github_repo_id);
    try {
      await api.connectRepository({
        github_repo_id: repo.github_repo_id,
        name: repo.name,
        full_name: repo.full_name,
        default_branch: repo.default_branch,
        is_private: repo.is_private,
        clone_url: repo.clone_url,
        language: repo.language,
      });
      const updated = await api.getRepositories({ forceLive: true });
      setRepositories(updated);
      setShowConnectModal(false);
    } catch (err) {
      console.error("Failed to connect repository:", err);
    } finally {
      setIsConnecting(null);
    }
  };

  useEffect(() => {
    let isMounted = true;
    async function loadRepos() {
      setIsLoading(true);
      try {
        const repos = await api.getRepositories({ forceLive: useLiveBackend });
        if (isMounted) {
          setRepositories(repos);
        }
      } catch (e) {
        if (isMounted) setRepositories([]);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }
    loadRepos();
    return () => {
      isMounted = false;
    };
  }, [useLiveBackend]);

  const filteredRepos = repositories.filter((repo) => {
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
          <div className="flex items-center gap-2 mb-2">
            <button
              onClick={() => setUseLiveBackend(!useLiveBackend)}
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-medium border border-border bg-surface text-muted hover:text-text transition-colors cursor-pointer"
              title="Click to toggle between live FastAPI PostgreSQL backend and demo fixtures"
            >
              {useLiveBackend ? (
                <>
                  <Database className="w-3 h-3 text-emerald-500" />
                  <span>Backend: Live PostgreSQL</span>
                </>
              ) : (
                <>
                  <Server className="w-3 h-3 text-amber-500" />
                  <span>Backend: Demo Fixtures</span>
                </>
              )}
            </button>
          </div>
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
          All ({repositories.length})
        </button>
        <button
          onClick={() => setActiveTab("connected")}
          className={`pb-3 -mb-px transition-colors relative cursor-pointer ${
            activeTab === "connected"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          Connected ({repositories.filter((r) => r.status === "connected" || r.status === "ready").length})
        </button>
        <button
          onClick={() => setActiveTab("syncing")}
          className={`pb-3 -mb-px transition-colors relative cursor-pointer ${
            activeTab === "syncing"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          Syncing ({repositories.filter((r) => r.status === "syncing").length})
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
              onChange={(e) => setSortBy(e.target.value as "lastSynced" | "riskScore" | "name")}
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

      {/* Repository Cards List or Empty State */}
      <div className="space-y-3">
        {repositories.length === 0 && !isLoading ? (
          <div className="text-center py-16 px-6 rounded-xl border border-dashed border-border bg-surface flex flex-col items-center justify-center">
            <div className="p-3 rounded-full bg-soft text-muted mb-4">
              <FolderGit2 className="w-6 h-6" />
            </div>
            <h3 className="font-serif text-lg font-medium text-text mb-1">
              No repositories connected yet
            </h3>
            <p className="text-xs text-muted max-w-sm mb-6 leading-relaxed">
              Your PostgreSQL database has no repository records. Connect a repository
              or explore our demo fixtures to preview intelligence features.
            </p>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowConnectModal(true)}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-text text-surface font-medium text-xs hover:opacity-90 transition-opacity shadow-sm cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Connect Repository</span>
              </button>
              <button
                onClick={() => setUseLiveBackend(false)}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-border bg-surface text-text font-medium text-xs hover:bg-soft transition-colors cursor-pointer"
              >
                <span>Explore Demo Repositories</span>
              </button>
            </div>
          </div>
        ) : filteredRepos.length === 0 && !isLoading ? (
          <div className="text-center py-12 rounded-xl border border-border bg-surface text-muted text-xs">
            No repositories found matching &quot;{searchQuery}&quot;.
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

                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-text">
                    Score: {repo.riskScore}
                  </span>
                  <Badge
                    variant={
                      repo.riskScore > 70
                        ? "error"
                        : repo.riskScore > 40
                          ? "warning"
                          : "neutral"
                    }
                  >
                    {repo.riskScore > 70
                      ? "High"
                      : repo.riskScore > 40
                        ? "Medium"
                        : "Low"}
                  </Badge>
                </div>
              </div>
            </Link>
          ))
        )}
      </div>

      {/* Connect Repository Modal */}
      {showConnectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-xl border border-border bg-surface p-6 shadow-xl">
            <div className="flex items-center justify-between pb-4 border-b border-border">
              <h3 className="text-sm font-semibold text-text">
                Connect GitHub Repository
              </h3>
              <button
                onClick={() => setShowConnectModal(false)}
                className="text-muted hover:text-text p-1 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="py-4 space-y-3">
              <p className="text-xs text-muted leading-relaxed">
                Connect a GitHub repository to enable autonomous test intelligence.
                Installation management and webhook sync are powered by Phase M2 GitHub integration.
              </p>

              <div className="space-y-2">
                <div className="text-xs font-semibold text-text">Discovered from GitHub App</div>
                {isDiscovering ? (
                  <div className="text-xs text-muted py-4 text-center">Discovering available repositories...</div>
                ) : discoveredRepos.length === 0 ? (
                  <div className="p-3 rounded-lg border border-border bg-soft text-xs text-muted">
                    No new repositories discovered. Verify GitHub App installation.
                  </div>
                ) : (
                  <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                    {discoveredRepos.map((repo) => (
                      <div
                        key={repo.github_repo_id}
                        className="flex items-center justify-between p-2.5 rounded-lg border border-border bg-soft text-xs"
                      >
                        <div className="min-w-0 pr-2">
                          <div className="font-semibold text-text truncate">{repo.name}</div>
                          <div className="text-[11px] text-muted truncate">{repo.full_name} • {repo.language || "Code"}</div>
                        </div>
                        {repo.is_connected ? (
                          <Badge variant="neutral">Connected</Badge>
                        ) : (
                          <button
                            onClick={() => handleConnect(repo)}
                            disabled={isConnecting === repo.github_repo_id}
                            className="px-2.5 py-1 rounded bg-text text-surface font-medium text-[11px] hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
                          >
                            {isConnecting === repo.github_repo_id ? "Connecting..." : "Connect"}
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setShowConnectModal(false)}
                className="px-3 py-1.5 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft"
              >
                Close
              </button>
              <button
                onClick={() => {
                  setShowConnectModal(false);
                  setUseLiveBackend(false);
                }}
                className="px-3.5 py-1.5 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90"
              >
                Load Demo Repositories
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
