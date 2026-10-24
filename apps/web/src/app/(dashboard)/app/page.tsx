"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { AppShell } from "@/components/shell/app-shell";
import { StatCard } from "@/components/ui/stat-card";
import { Badge } from "@/components/ui/badge";
import {
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  FileText,
  PlaySquare,
  FolderGit2,
  CheckCircle2,
  Plus,
  X,
  Server,
  Database,
  ChevronDown,
} from "lucide-react";
import { api } from "@/lib/api-adapter";
import { Repository } from "@/types";
import { DEMO_REPOSITORIES } from "@/lib/fixtures";

export default function OverviewPage() {
  const [connectModalOpen, setConnectModalOpen] = useState(false);
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedRepoFilter, setSelectedRepoFilter] = useState<string>("all");
  const [timeFilter, setTimeFilter] = useState<"30d" | "7d" | "24h">("30d");
  const [newRepoInput, setNewRepoInput] = useState("");

  const [activities, setActivities] = useState([
    {
      id: "act-1",
      icon: PlaySquare,
      title: "Test run completed",
      repo: "nextjs-dashboard",
      badgeText: "Passed",
      badgeVariant: "success" as const,
      timestamp: "2 min ago",
      href: "/app/runs/run-1042",
    },
    {
      id: "act-2",
      icon: AlertTriangle,
      title: "Risk analysis completed",
      repo: "api-service",
      badgeText: "12 high-risk files",
      badgeVariant: "neutral" as const,
      timestamp: "18 min ago",
      href: "/app/risk",
    },
    {
      id: "act-3",
      icon: FileText,
      title: "Test plan generated",
      repo: "ecommerce",
      badgeText: "32 test cases",
      badgeVariant: "neutral" as const,
      timestamp: "41 min ago",
      href: "/app/test-plans",
    },
    {
      id: "act-4",
      icon: FolderGit2,
      title: "Repository connected",
      repo: "mobile-app",
      badgeText: "Completed",
      badgeVariant: "neutral" as const,
      timestamp: "2 hours ago",
      href: "/app/repositories",
    },
  ]);

  useEffect(() => {
    let isMounted = true;
    async function loadRepos() {
      setIsLoading(true);
      try {
        const repos = await api.getRepositories();
        if (isMounted) {
          if (repos && repos.length > 0) {
            const demoNames = new Set(DEMO_REPOSITORIES.map((r) => r.id));
            const uniqueLive = repos.filter((r) => !demoNames.has(r.id));
            setRepositories([...DEMO_REPOSITORIES, ...uniqueLive]);
          } else {
            setRepositories(DEMO_REPOSITORIES);
          }
        }
      } catch (e) {
        if (isMounted) setRepositories(DEMO_REPOSITORIES);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    }
    loadRepos();
    return () => {
      isMounted = false;
    };
  }, []);

  const allRepos = repositories.length > 0 ? repositories : DEMO_REPOSITORIES;

  // Dynamically compute the 4 headline stat cards based on scope and time window
  const dynamicStats = React.useMemo(() => {
    if (selectedRepoFilter === "all") {
      let highRisk = 18;
      let testsGen = 124;
      let passRate = "92%";

      if (timeFilter === "7d") {
        highRisk = 11;
        testsGen = 68;
        passRate = "94%";
      } else if (timeFilter === "24h") {
        highRisk = 3;
        testsGen = 32;
        passRate = "100%";
      }

      return {
        repos: allRepos.length,
        highRisk,
        testsGen,
        passRate,
      };
    }

    const repo = allRepos.find((r) => r.id === selectedRepoFilter);
    if (!repo) {
      return { repos: 1, highRisk: 2, testsGen: 124, passRate: "92%" };
    }

    let highRisk =
      repo.riskScore > 65
        ? Math.round(repo.riskScore / 14)
        : Math.round(repo.riskScore / 20) || 1;
    let testsGen = repo.testCount || 42;
    let passRate = `${repo.coveragePercent || 88}%`;

    if (timeFilter === "7d") {
      testsGen = Math.round(testsGen * 0.6);
    } else if (timeFilter === "24h") {
      testsGen = Math.round(testsGen * 0.25);
    }

    return {
      repos: 1,
      highRisk,
      testsGen,
      passRate,
    };
  }, [selectedRepoFilter, timeFilter, allRepos]);

  // Filter activities to match selected repository
  const filteredActivities = React.useMemo(() => {
    if (selectedRepoFilter === "all") return activities;
    return activities.filter((a) => a.repo === selectedRepoFilter);
  }, [selectedRepoFilter, activities]);

  const handleConnectRepoSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRepoInput.trim()) return;
    const cleanName = newRepoInput.trim().toLowerCase().replace(/[^a-z0-9_-]/g, "-");
    const newRepo: Repository = {
      id: cleanName,
      name: cleanName,
      fullName: `jaweria/${cleanName}`,
      defaultBranch: "main",
      lastSynced: "Just now",
      status: "connected",
      riskScore: 34,
      testCount: 38,
      fileCount: 22,
      coveragePercent: 89,
    };
    setRepositories((prev) => [newRepo, ...prev]);
    setActivities((prev) => [
      {
        id: `act-${Date.now()}`,
        icon: FolderGit2,
        title: "Repository connected",
        repo: cleanName,
        badgeText: "Connected",
        badgeVariant: "success" as const,
        timestamp: "Just now",
        href: `/app/repositories`,
      },
      ...prev,
    ]);
    setSelectedRepoFilter(cleanName);
    setNewRepoInput("");
    setConnectModalOpen(false);
  };

  return (
    <AppShell breadcrumbs={["Overview"]}>
      {/* Editorial Hero Header matching 01_Overview.png */}
      <div className="pt-4 pb-8 max-w-3xl">
        <h1 className="font-serif text-5xl sm:text-6xl lg:text-[62px] font-normal tracking-[-0.035em] text-text leading-[1.08]">
          Better tests.
          <br />
          Safer changes.
        </h1>
        <p className="mt-4 text-base text-muted max-w-xl leading-relaxed">
          Analyze your repositories, detect risk, generate tests, and ship with
          confidence.
        </p>

        <div className="mt-6 flex items-center gap-3">
          <button
            onClick={() => setConnectModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-text text-surface font-medium text-xs hover:opacity-90 transition-opacity shadow-sm cursor-pointer"
          >
            <span>Connect Repository</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Scope & Time Range Controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 mt-4 mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-muted">Filter overview:</span>
          <div className="relative">
            <select
              value={selectedRepoFilter}
              onChange={(e) => setSelectedRepoFilter(e.target.value)}
              className="appearance-none pl-3 pr-8 py-1.5 rounded-lg border border-border bg-surface text-xs font-medium text-text focus:outline-none focus:ring-1 focus:ring-text cursor-pointer shadow-xs"
            >
              <option value="all">All Repositories ({allRepos.length})</option>
              {allRepos.map((r) => (
                <option key={r.id} value={r.id} className="bg-surface text-text">
                  {r.name}
                </option>
              ))}
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted pointer-events-none" />
          </div>

          <div className="relative">
            <select
              value={timeFilter}
              onChange={(e) => setTimeFilter(e.target.value as any)}
              className="appearance-none pl-3 pr-8 py-1.5 rounded-lg border border-border bg-surface text-xs font-medium text-text focus:outline-none focus:ring-1 focus:ring-text cursor-pointer shadow-xs"
            >
              <option value="30d">Last 30 days</option>
              <option value="7d">Last 7 days</option>
              <option value="24h">Last 24 hours</option>
            </select>
            <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted pointer-events-none" />
          </div>
        </div>

        {selectedRepoFilter !== "all" && (
          <button
            onClick={() => setSelectedRepoFilter("all")}
            className="text-xs text-muted hover:text-text underline cursor-pointer"
          >
            Reset filter
          </button>
        )}
      </div>

      {/* 4 Stat Cards matching 01_Overview.png - Dynamically responding to Scope & Time filters */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2">
        <Link href="/app/repositories" className="block group">
          <StatCard
            value={dynamicStats.repos}
            label="Repositories"
            className="group-hover:border-neutral-400 dark:group-hover:border-neutral-600 transition-colors cursor-pointer"
          />
        </Link>
        <Link
          href={`/app/risk${selectedRepoFilter !== "all" ? `?repo=${selectedRepoFilter}` : ""}`}
          className="block group"
        >
          <StatCard
            value={dynamicStats.highRisk}
            label="High-risk files"
            icon={<AlertTriangle className="w-4 h-4 text-amber-500 inline" />}
            className="group-hover:border-neutral-400 dark:group-hover:border-neutral-600 transition-colors cursor-pointer"
          />
        </Link>
        <Link href="/app/test-plans" className="block group">
          <StatCard
            value={dynamicStats.testsGen}
            label="Tests generated"
            className="group-hover:border-neutral-400 dark:group-hover:border-neutral-600 transition-colors cursor-pointer"
          />
        </Link>
        <Link href="/app/runs" className="block group">
          <StatCard
            value={dynamicStats.passRate}
            label="Pass rate"
            icon={<TrendingUp className="w-4 h-4 text-emerald-500 inline" />}
            className="group-hover:border-neutral-400 dark:group-hover:border-neutral-600 transition-colors cursor-pointer"
          />
        </Link>
      </div>

      {/* Recent Activity Section matching 01_Overview.png */}
      <div className="mt-12">
        <div className="flex items-center justify-between pb-4">
          <h2 className="text-sm font-semibold tracking-tight text-text">
            Recent activity {selectedRepoFilter !== "all" && `· ${selectedRepoFilter}`}
          </h2>
          <Link
            href="/app/runs"
            className="text-xs font-medium text-muted hover:text-text transition-colors flex items-center gap-1"
          >
            <span>View all</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="divide-y divide-border rounded-xl border border-border bg-surface overflow-hidden shadow-sm">
          {filteredActivities.length > 0 ? (
            filteredActivities.map((activity) => {
              const Icon = activity.icon;
              return (
                <Link
                  key={activity.id}
                  href={activity.href}
                  className="flex items-center justify-between p-4 hover:bg-soft transition-colors group"
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div className="p-2 rounded-lg bg-soft text-muted group-hover:text-text transition-colors shrink-0">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-text truncate">
                        {activity.title}
                      </div>
                      <div className="text-[11px] text-muted truncate mt-0.5">
                        {activity.repo}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 shrink-0">
                    <Badge variant={activity.badgeVariant}>
                      {activity.badgeText}
                    </Badge>
                    <span className="text-[11px] text-muted hidden sm:inline">
                      {activity.timestamp}
                    </span>
                  </div>
                </Link>
              );
            })
          ) : (
            <div className="p-8 text-center text-xs text-muted">
              No recent activity recorded for {selectedRepoFilter}.
            </div>
          )}
        </div>
      </div>

      {/* Connect Repository Modal with Real State Ingestion */}
      {connectModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-xl border border-border bg-surface p-6 shadow-xl">
            <div className="flex items-center justify-between pb-4 border-b border-border">
              <h3 className="text-sm font-semibold text-text">
                Connect GitHub Repository
              </h3>
              <button
                onClick={() => setConnectModalOpen(false)}
                className="text-muted hover:text-text p-1 rounded-md cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleConnectRepoSubmit} className="py-4 space-y-4">
              <div>
                <label className="block text-xs font-medium text-text mb-1">
                  Repository Name or URL
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. auth-service or owner/repo"
                  value={newRepoInput}
                  onChange={(e) => setNewRepoInput(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-surface text-xs text-text placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-text"
                />
              </div>

              <div className="p-3 rounded-lg border border-border bg-soft text-xs text-muted space-y-1">
                <div className="font-semibold text-text">
                  FastAPI Backend Connected
                </div>
                <div>
                  Connecting a repository initializes automated branch tracking,
                  commit mining, and deterministic risk evaluation.
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-border">
                <button
                  type="button"
                  onClick={() => setConnectModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-3.5 py-1.5 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90 cursor-pointer"
                >
                  Connect &amp; Sync
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppShell>
  );
}
