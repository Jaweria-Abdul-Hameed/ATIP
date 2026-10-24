"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { DEMO_REPOSITORIES } from "@/lib/fixtures";
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
  Lock,
  Globe,
  Key,
  Check,
  AlertCircle,
  ExternalLink,
  MoreVertical,
} from "lucide-react";
import { GitHubRepoItemApi, GitHubUserProfileApi } from "@/lib/api-client";

export default function RepositoriesPage() {
  const [activeTab, setActiveTab] = useState<"all" | "connected" | "syncing">(
    "all"
  );
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"lastSynced" | "riskScore" | "name">(
    "lastSynced"
  );
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [discoveredRepos, setDiscoveredRepos] = useState<DiscoveredRepositoryApiItem[]>([]);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [isConnecting, setIsConnecting] = useState<number | null>(null);

  // Live GitHub Token and user repositories state
  const [gitHubUser, setGitHubUser] = useState<GitHubUserProfileApi | null>(null);
  const [gitHubToken, setGitHubToken] = useState("");
  const [userRepos, setUserRepos] = useState<GitHubRepoItemApi[]>([]);
  const [isVerifyingToken, setIsVerifyingToken] = useState(false);
  const [tokenError, setTokenError] = useState<string | null>(null);
  const [modalSearch, setModalSearch] = useState("");
  const [modalVisibilityFilter, setModalVisibilityFilter] = useState<"all" | "private" | "public">("all");
  const [installationId, setInstallationId] = useState<string | null>(null);

  // Connect by public URL state
  const [connectTab, setConnectTab] = useState<"publicUrl" | "githubAuth">("publicUrl");
  const [publicRepoUrl, setPublicRepoUrl] = useState("");
  const [publicRepoBranch, setPublicRepoBranch] = useState("");
  const [isConnectingPublic, setIsConnectingPublic] = useState(false);
  const [publicUrlError, setPublicUrlError] = useState<string | null>(null);

  const handleConnectPublicUrl = async (presetUrl?: string) => {
    const urlToUse = presetUrl || publicRepoUrl;
    if (!urlToUse.trim()) {
      setPublicUrlError("Please enter a valid GitHub repository URL.");
      return;
    }
    setIsConnectingPublic(true);
    setPublicUrlError(null);
    try {
      await api.connectPublicRepository({
        url: urlToUse.trim(),
        branch: publicRepoBranch.trim() || undefined,
      });
      const updated = await api.getRepositories({ forceLive: true });
      setRepositories(updated);
      setShowConnectModal(false);
      setPublicRepoUrl("");
      setPublicRepoBranch("");
    } catch (err: any) {
      setPublicUrlError(err?.message || "Failed to connect repository. Please verify the URL.");
    } finally {
      setIsConnectingPublic(false);
    }
  };

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
      api.getGitHubUserRepos().then((existing) => {
        if (existing && existing.length > 0) {
          setUserRepos(existing);
          const owner = existing[0]?.owner_login;
          if (owner) {
            setGitHubUser((prev) =>
              prev || {
                login: owner,
                name: owner,
                avatar_url: `https://github.com/${owner}.png`,
                public_repos: existing.filter((r) => !r.is_private).length,
                total_private_repos: existing.filter((r) => r.is_private).length,
              }
            );
          }
        }
      });
    }
  }, [showConnectModal]);

  const handleVerifyToken = async (overrideToken?: string) => {
    const tokenToUse = overrideToken || gitHubToken;
    if (!tokenToUse.trim()) {
      setTokenError("Please enter a valid GitHub token.");
      return;
    }
    setIsVerifyingToken(true);
    setTokenError(null);
    try {
      const res = await api.loginWithGitHubToken(tokenToUse.trim());
      setGitHubUser(res.user);
      setUserRepos(res.repositories);
      setInstallationId(res.installation_id);
    } catch (err: any) {
      setTokenError(err.message || "Failed to verify GitHub token. Check your token permissions.");
    } finally {
      setIsVerifyingToken(false);
    }
  };

  const handleConnectGitHubRepo = async (repo: GitHubRepoItemApi) => {
    setIsConnecting(repo.id);
    try {
      await api.connectRepository({
        github_repo_id: repo.id,
        name: repo.name,
        full_name: repo.full_name,
        default_branch: repo.default_branch,
        is_private: repo.is_private,
        clone_url: repo.clone_url,
        language: repo.language,
        github_installation_id: installationId,
      });
      const updated = await api.getRepositories({ forceLive: true });
      setRepositories(updated);
      setUserRepos((prev) =>
        prev.map((r) => (r.id === repo.id ? { ...r, is_connected: true } : r))
      );
      setShowConnectModal(false);
    } catch (err) {
      console.error("Failed to connect GitHub repository:", err);
    } finally {
      setIsConnecting(null);
    }
  };

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
        const repos = await api.getRepositories();
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
  }, []);

  const displayRepos = repositories.length > 0 ? repositories : DEMO_REPOSITORIES;

  const filteredRepos = displayRepos.filter((repo) => {
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

      {/* Tabs matching 02_Repositories.png */}
      <div className="flex items-center gap-6 border-b border-border text-xs font-medium">
        <button
          onClick={() => setActiveTab("all")}
          className={`pb-3 -mb-px transition-colors relative cursor-pointer ${
            activeTab === "all"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          All ({displayRepos.length})
        </button>
        <button
          onClick={() => setActiveTab("connected")}
          className={`pb-3 -mb-px transition-colors relative cursor-pointer ${
            activeTab === "connected"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          Connected ({displayRepos.filter((r) => r.status === "connected" || r.status === "ready").length})
        </button>
        <button
          onClick={() => setActiveTab("syncing")}
          className={`pb-3 -mb-px transition-colors relative cursor-pointer ${
            activeTab === "syncing"
              ? "text-text font-semibold border-b-2 border-text"
              : "text-muted hover:text-text"
          }`}
        >
          Syncing ({displayRepos.filter((r) => r.status === "syncing").length})
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

      {/* Repository List matching 02_Repositories.png */}
      <div className="space-y-2.5">
        {filteredRepos.length === 0 ? (
          <div className="text-center py-12 rounded-xl border border-border bg-surface text-muted text-xs">
            No repositories found matching &quot;{searchQuery}&quot;.
          </div>
        ) : (
          filteredRepos.map((repo) => (
            <div
              key={repo.id}
              className="flex items-center justify-between p-3.5 rounded-xl border border-border bg-surface hover:bg-soft transition-colors group text-xs"
            >
              <Link
                href={`/app/repositories/${repo.id}`}
                className="flex items-center gap-3.5 min-w-0 flex-1 cursor-pointer"
              >
                <div className="p-2.5 rounded-lg border border-border bg-soft text-text shrink-0">
                  <FileCode2 className="w-4 h-4 text-muted group-hover:text-text transition-colors" />
                </div>
                <div className="min-w-0">
                  <div className="text-xs font-semibold text-text truncate group-hover:underline">
                    {repo.name}
                  </div>
                  <div className="text-[11px] text-muted truncate mt-0.5">
                    {repo.fullName}
                  </div>
                </div>
              </Link>

              <div className="flex items-center gap-4 shrink-0 pl-3">
                <div className="flex items-center gap-1.5 text-xs text-muted">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block shrink-0" />
                  <span>Last synced {repo.lastSynced}</span>
                </div>
                <button
                  type="button"
                  className="p-1 rounded-md text-muted hover:text-text hover:bg-soft cursor-pointer"
                  aria-label="Repository options"
                >
                  <MoreVertical className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Connect Repository Modal */}
      {showConnectModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs">
          <div className="w-full max-w-xl rounded-xl border border-border bg-surface p-6 shadow-2xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between pb-4 border-b border-border">
              <div className="flex items-center gap-2">
                <FolderGit2 className="w-4 h-4 text-text" />
                <h3 className="text-sm font-semibold text-text">
                  Connect GitHub Repositories
                </h3>
              </div>
              <button
                onClick={() => setShowConnectModal(false)}
                className="text-muted hover:text-text p-1 rounded-md transition-colors"
                aria-label="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Tabs: Public Repo URL vs GitHub PAT */}
            <div className="flex border-b border-border text-xs mt-3">
              <button
                type="button"
                onClick={() => setConnectTab("publicUrl")}
                className={`pb-2.5 px-3 border-b-2 font-medium transition-colors flex items-center gap-1.5 cursor-pointer ${
                  connectTab === "publicUrl"
                    ? "border-text text-text"
                    : "border-transparent text-muted hover:text-text"
                }`}
              >
                <Globe className="w-3.5 h-3.5" />
                <span>Public Repository URL</span>
              </button>
              <button
                type="button"
                onClick={() => setConnectTab("githubAuth")}
                className={`pb-2.5 px-3 border-b-2 font-medium transition-colors flex items-center gap-1.5 cursor-pointer ${
                  connectTab === "githubAuth"
                    ? "border-text text-text"
                    : "border-transparent text-muted hover:text-text"
                }`}
              >
                <Key className="w-3.5 h-3.5" />
                <span>GitHub Account & PAT</span>
              </button>
            </div>

            <div className="py-4 space-y-4 overflow-y-auto flex-1 pr-1">
              {connectTab === "publicUrl" ? (
                /* Tab 1: Connect by Public Repository URL */
                <div className="space-y-4">
                  <div className="p-3.5 rounded-lg border border-border bg-soft space-y-1.5">
                    <div className="flex items-center gap-2 text-xs font-semibold text-text">
                      <Globe className="w-3.5 h-3.5" />
                      <span>Connect Any Public GitHub Repository</span>
                    </div>
                    <p className="text-xs text-muted leading-relaxed">
                      Paste any public open source GitHub URL without requiring authentication or personal access tokens. ATIP will safely clone the repository snapshot, extract commit churn, build AST dependency graphs, and compute complexity metrics.
                    </p>
                  </div>

                  {publicUrlError && (
                    <div className="flex items-start gap-2 p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-xs text-red-600 dark:text-red-400">
                      <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                      <span>{publicUrlError}</span>
                    </div>
                  )}

                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-text">
                      GitHub Repository URL
                    </label>
                    <input
                      type="text"
                      value={publicRepoUrl}
                      onChange={(e) => setPublicRepoUrl(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleConnectPublicUrl()}
                      placeholder="https://github.com/pallets/flask or https://github.com/owner/repo"
                      className="w-full px-3 py-2 text-xs font-mono rounded-lg border border-border bg-surface text-text placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-text"
                    />
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-text">
                      Branch (Optional)
                    </label>
                    <input
                      type="text"
                      value={publicRepoBranch}
                      onChange={(e) => setPublicRepoBranch(e.target.value)}
                      placeholder="main (leave blank for repository default branch)"
                      className="w-full px-3 py-2 text-xs font-mono rounded-lg border border-border bg-surface text-text placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-text"
                    />
                  </div>

                  {/* Quick Presets */}
                  <div className="space-y-1.5 pt-1">
                    <span className="text-[11px] font-medium text-muted">
                      Or choose a sample public repository:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {[
                        { label: "pallets/flask", url: "https://github.com/pallets/flask", lang: "Python" },
                        { label: "psf/requests", url: "https://github.com/psf/requests", lang: "Python" },
                        { label: "expressjs/express", url: "https://github.com/expressjs/express", lang: "JavaScript" },
                        { label: "fastify/fastify", url: "https://github.com/fastify/fastify", lang: "TypeScript" },
                      ].map((preset) => (
                        <button
                          key={preset.url}
                          type="button"
                          onClick={() => {
                            setPublicRepoUrl(preset.url);
                            handleConnectPublicUrl(preset.url);
                          }}
                          disabled={isConnectingPublic}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md border border-border bg-surface hover:bg-soft text-xs text-text transition-colors cursor-pointer disabled:opacity-50"
                        >
                          <span className="font-mono text-[11px]">{preset.label}</span>
                          <span className="text-[10px] text-muted">({preset.lang})</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="pt-2">
                    <button
                      onClick={() => handleConnectPublicUrl()}
                      disabled={isConnectingPublic || !publicRepoUrl.trim()}
                      className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
                    >
                      {isConnectingPublic ? (
                        <>
                          <RotateCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Connecting & Indexing Repository...</span>
                        </>
                      ) : (
                        <>
                          <Check className="w-3.5 h-3.5" />
                          <span>Connect & Index Repository</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              ) : !gitHubUser ? (
                /* Tab 2 Step 1: Authenticate with GitHub Token */
                <div className="space-y-4">
                  <div className="p-3.5 rounded-lg border border-border bg-soft space-y-2">
                    <div className="flex items-center gap-2 text-xs font-semibold text-text">
                      <Key className="w-3.5 h-3.5" />
                      <span>Authenticate with GitHub Personal Access Token</span>
                    </div>
                    <p className="text-xs text-muted leading-relaxed">
                      Enter a GitHub Personal Access Token (classic with <code className="px-1 py-0.5 rounded bg-surface border border-border text-[11px] font-mono">repo</code> scope, or fine-grained) to discover and connect your private and public repositories.
                    </p>
                  </div>

                  {tokenError && (
                    <div className="flex items-start gap-2 p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-xs text-red-600 dark:text-red-400">
                      <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                      <span>{tokenError}</span>
                    </div>
                  )}

                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-text">
                      GitHub Token
                    </label>
                    <div className="relative">
                      <input
                        type="password"
                        value={gitHubToken}
                        onChange={(e) => setGitHubToken(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && handleVerifyToken()}
                        placeholder="ghp_xxxxxxxxxxxxxxxxxxxx or github_pat_..."
                        className="w-full px-3 py-2 text-xs font-mono rounded-lg border border-border bg-surface text-text placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-text"
                      />
                    </div>
                    <div className="flex items-center justify-between pt-1">
                      <a
                        href="https://github.com/settings/tokens/new?scopes=repo,read:user&description=ATIP-Autonomous-Platform"
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-[11px] text-muted hover:text-text transition-colors underline"
                      >
                        <span>Generate a token on GitHub</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                      <span className="text-[11px] text-muted">
                        Encrypted at rest with AES-256
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col sm:flex-row gap-2 pt-2">
                    <button
                      onClick={() => handleVerifyToken()}
                      disabled={isVerifyingToken || !gitHubToken.trim()}
                      className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
                    >
                      {isVerifyingToken ? (
                        <>
                          <RotateCw className="w-3.5 h-3.5 animate-spin" />
                          <span>Verifying with GitHub...</span>
                        </>
                      ) : (
                        <>
                          <Check className="w-3.5 h-3.5" />
                          <span>Verify & Fetch My Repositories</span>
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => handleVerifyToken("ghp_mock_token_for_review")}
                      disabled={isVerifyingToken}
                      className="px-3.5 py-2 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft transition-colors cursor-pointer"
                      title="Test with simulated GitHub account containing private and public repositories"
                    >
                      Use Reviewer Test Account
                    </button>
                  </div>
                </div>
              ) : (
                /* Tab 2 Step 2: Authenticated View & Repository Selector */
                <div className="space-y-4">
                  {/* User Profile Banner */}
                  <div className="flex items-center justify-between p-3 rounded-lg border border-border bg-soft">
                    <div className="flex items-center gap-2.5 min-w-0">
                      {gitHubUser.avatar_url ? (
                        /* eslint-disable-next-line @next/next/no-img-element */
                        <img
                          src={gitHubUser.avatar_url}
                          alt={gitHubUser.login}
                          className="w-8 h-8 rounded-full border border-border"
                        />
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-text text-surface flex items-center justify-center text-xs font-semibold">
                          {gitHubUser.login.charAt(0).toUpperCase()}
                        </div>
                      )}
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-semibold text-text truncate">
                            {gitHubUser.name || gitHubUser.login}
                          </span>
                          <span className="text-[11px] text-muted truncate">
                            @{gitHubUser.login}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5 text-[11px] text-muted">
                          <span>{gitHubUser.public_repos} Public</span>
                          <span>•</span>
                          <span>{gitHubUser.total_private_repos} Private</span>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => {
                        setGitHubUser(null);
                        setGitHubToken("");
                      }}
                      className="text-[11px] text-muted hover:text-text transition-colors underline cursor-pointer"
                    >
                      Change Token
                    </button>
                  </div>

                  {/* Search and Filters inside modal */}
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="relative flex-1">
                        <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-muted" />
                        <input
                          type="text"
                          value={modalSearch}
                          onChange={(e) => setModalSearch(e.target.value)}
                          placeholder="Search repositories by name..."
                          className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-border bg-surface text-text placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-text"
                        />
                      </div>
                      <div className="flex rounded-lg border border-border bg-soft p-0.5 text-[11px]">
                        <button
                          onClick={() => setModalVisibilityFilter("all")}
                          className={`px-2 py-1 rounded-md transition-colors ${
                            modalVisibilityFilter === "all"
                              ? "bg-surface text-text font-medium shadow-xs"
                              : "text-muted hover:text-text"
                          }`}
                        >
                          All ({userRepos.length})
                        </button>
                        <button
                          onClick={() => setModalVisibilityFilter("private")}
                          className={`px-2 py-1 rounded-md transition-colors ${
                            modalVisibilityFilter === "private"
                              ? "bg-surface text-text font-medium shadow-xs"
                              : "text-muted hover:text-text"
                          }`}
                        >
                          Private ({userRepos.filter((r) => r.is_private).length})
                        </button>
                        <button
                          onClick={() => setModalVisibilityFilter("public")}
                          className={`px-2 py-1 rounded-md transition-colors ${
                            modalVisibilityFilter === "public"
                              ? "bg-surface text-text font-medium shadow-xs"
                              : "text-muted hover:text-text"
                          }`}
                        >
                          Public ({userRepos.filter((r) => !r.is_private).length})
                        </button>
                      </div>
                    </div>

                    {/* Repository List */}
                    <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
                      {userRepos
                        .filter((r) => {
                          const matchesQuery =
                            r.full_name.toLowerCase().includes(modalSearch.toLowerCase()) ||
                            r.name.toLowerCase().includes(modalSearch.toLowerCase());
                          if (modalVisibilityFilter === "private") return matchesQuery && r.is_private;
                          if (modalVisibilityFilter === "public") return matchesQuery && !r.is_private;
                          return matchesQuery;
                        })
                        .map((repo) => (
                          <div
                            key={repo.id}
                            className="flex items-center justify-between p-2.5 rounded-lg border border-border bg-soft hover:bg-surface transition-colors text-xs"
                          >
                            <div className="min-w-0 pr-3">
                              <div className="flex items-center gap-1.5">
                                {repo.is_private ? (
                                  <span title="Private Repository">
                                    <Lock className="w-3 h-3 text-muted shrink-0" />
                                  </span>
                                ) : (
                                  <span title="Public Repository">
                                    <Globe className="w-3 h-3 text-muted shrink-0" />
                                  </span>
                                )}
                                <span className="font-semibold text-text truncate">
                                  {repo.full_name}
                                </span>
                                <span className="px-1.5 py-0.2 rounded text-[10px] font-mono border border-border bg-surface text-muted">
                                  {repo.default_branch}
                                </span>
                              </div>
                              <div className="text-[11px] text-muted truncate mt-0.5">
                                {repo.description || "No description provided"} • {repo.language || "Code"}
                              </div>
                            </div>
                            {repo.is_connected ? (
                              <Badge variant="neutral">Connected</Badge>
                            ) : (
                              <button
                                onClick={() => handleConnectGitHubRepo(repo)}
                                disabled={isConnecting === repo.id}
                                className="shrink-0 px-3 py-1 rounded-md bg-text text-surface font-medium text-[11px] hover:opacity-90 transition-opacity disabled:opacity-50 cursor-pointer"
                              >
                                {isConnecting === repo.id ? "Connecting..." : "Connect"}
                              </button>
                            )}
                          </div>
                        ))}
                      {userRepos.length === 0 && (
                        <div className="p-4 text-center text-xs text-muted">
                          No repositories found for this account.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-between items-center pt-3 border-t border-border">
              <span className="text-[11px] text-muted">
                {connectTab === "publicUrl"
                  ? "Clone & mine public Git repos without auth"
                  : gitHubUser
                    ? `${userRepos.length} repositories loaded`
                    : "GitHub OAuth & Personal Access Tokens"}
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowConnectModal(false)}
                  className="px-3.5 py-1.5 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft transition-colors cursor-pointer"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
