"use client";

import React, { useState } from "react";
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
} from "lucide-react";
import { DEMO_REPOSITORIES } from "@/lib/fixtures";

export default function OverviewPage() {
  const [connectModalOpen, setConnectModalOpen] = useState(false);

  const recentActivity = [
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
  ];

  return (
    <AppShell breadcrumbs={["Overview"]}>
      {/* Editorial Hero Header */}
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

      {/* 4 Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2">
        <StatCard
          value={DEMO_REPOSITORIES.length}
          label="Repositories"
          className="hover:border-neutral-400 dark:hover:border-neutral-600 transition-colors"
        />
        <StatCard
          value="18"
          label="High-risk files"
          icon={<AlertTriangle className="w-4 h-4 text-amber-500 inline" />}
          className="hover:border-neutral-400 dark:hover:border-neutral-600 transition-colors"
        />
        <StatCard
          value="124"
          label="Tests generated"
          className="hover:border-neutral-400 dark:hover:border-neutral-600 transition-colors"
        />
        <StatCard
          value="92%"
          label="Pass rate"
          icon={<TrendingUp className="w-4 h-4 text-emerald-500 inline" />}
          className="hover:border-neutral-400 dark:hover:border-neutral-600 transition-colors"
        />
      </div>

      {/* Recent Activity Section */}
      <div className="mt-12">
        <div className="flex items-center justify-between pb-4">
          <h2 className="text-sm font-semibold tracking-tight text-text">
            Recent activity
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
          {recentActivity.map((activity) => {
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
          })}
        </div>
      </div>

      {/* Connect Repository Modal */}
      {connectModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-xl border border-border bg-surface p-6 shadow-xl">
            <div className="flex items-center justify-between pb-4 border-b border-border">
              <h3 className="text-sm font-semibold text-text">
                Connect GitHub Repository
              </h3>
              <button
                onClick={() => setConnectModalOpen(false)}
                className="text-muted hover:text-text p-1 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="py-4 space-y-3">
              <p className="text-xs text-muted leading-relaxed">
                Connect your GitHub organization or personal account through our
                verified GitHub App with fine-grained repository permissions.
              </p>
              <div className="p-3 rounded-lg border border-border bg-soft text-xs text-muted space-y-1">
                <div className="font-semibold text-text">
                  Demonstration Notice
                </div>
                <div>
                  Production GitHub App installation requires OAuth setup in
                  Phase M2. All repositories below are loaded via isolated demo
                  fixtures.
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setConnectModalOpen(false)}
                className="px-3 py-1.5 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft"
              >
                Cancel
              </button>
              <Link
                href="/app/repositories"
                onClick={() => setConnectModalOpen(false)}
                className="px-3.5 py-1.5 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90"
              >
                View Repositories
              </Link>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
