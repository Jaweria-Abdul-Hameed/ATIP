"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/shell/app-shell";
import { ThemeToggle } from "@/components/theme-toggle";
import { Badge } from "@/components/ui/badge";
import { DEMO_USER } from "@/lib/fixtures";
import {
  User,
  Building,
  Users,
  Github,
  Sparkles,
  Shield,
  Bell,
  FileText,
  Palette,
  Check,
  AlertTriangle,
  Lock,
} from "lucide-react";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<
    | "profile"
    | "organization"
    | "members"
    | "github"
    | "ai"
    | "execution"
    | "notifications"
    | "audit"
    | "appearance"
  >("profile");

  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const tabs = [
    { id: "profile", label: "Profile", icon: User },
    { id: "organization", label: "Organization", icon: Building },
    { id: "members", label: "Members & Roles", icon: Users },
    { id: "github", label: "GitHub App", icon: Github },
    { id: "ai", label: "AI Providers", icon: Sparkles },
    { id: "execution", label: "Execution Policies", icon: Shield },
    { id: "notifications", label: "Notifications", icon: Bell },
    { id: "audit", label: "Audit Log", icon: FileText },
    { id: "appearance", label: "Appearance", icon: Palette },
  ];

  return (
    <AppShell breadcrumbs={["Settings"]}>
      {/* Header */}
      <div className="pt-2 pb-6 border-b border-border">
        <h1 className="font-serif text-3xl sm:text-4xl font-normal tracking-tight text-text">
          Settings
        </h1>
        <p className="mt-1 text-xs sm:text-sm text-muted">
          Manage your organization workspace, integrations, security, and
          appearance.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-6 border-b border-border text-xs font-medium overflow-x-auto my-4">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`pb-3 -mb-px transition-colors flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
                activeTab === tab.id
                  ? "text-text font-semibold border-b-2 border-text"
                  : "text-muted hover:text-text"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Contents */}
      <div className="mt-6 max-w-2xl">
        {activeTab === "profile" && (
          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm space-y-5">
            <h2 className="text-sm font-semibold text-text">User Profile</h2>
            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                Full Name
              </label>
              <input
                type="text"
                defaultValue={DEMO_USER.name}
                className="w-full px-3 py-2 rounded-lg border border-border bg-surface text-xs text-text focus:outline-none focus:ring-1 focus:ring-text"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                Email Address
              </label>
              <input
                type="email"
                defaultValue={DEMO_USER.email}
                className="w-full px-3 py-2 rounded-lg border border-border bg-surface text-xs text-text focus:outline-none focus:ring-1 focus:ring-text"
              />
            </div>
            <div className="pt-2">
              <button
                onClick={handleSave}
                className="px-4 py-2 rounded-lg bg-text text-surface font-medium text-xs hover:opacity-90 transition-opacity cursor-pointer"
              >
                {saved ? "Saved ✓" : "Save Changes"}
              </button>
            </div>
          </div>
        )}

        {activeTab === "organization" && (
          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm space-y-5">
            <h2 className="text-sm font-semibold text-text">
              Workspace Settings
            </h2>
            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                Organization Name
              </label>
              <input
                type="text"
                defaultValue="Personal Workspace"
                className="w-full px-3 py-2 rounded-lg border border-border bg-surface text-xs text-text focus:outline-none focus:ring-1 focus:ring-text"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-muted mb-1.5">
                Slug identifier
              </label>
              <input
                type="text"
                defaultValue="personal-workspace"
                disabled
                className="w-full px-3 py-2 rounded-lg border border-border bg-soft font-mono text-xs text-muted"
              />
            </div>
          </div>
        )}

        {activeTab === "members" && (
          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-border">
              <h2 className="text-sm font-semibold text-text">
                Workspace Members (1)
              </h2>
              <button className="px-3 py-1.5 rounded-lg border border-border text-xs font-medium text-text hover:bg-soft">
                + Invite Member
              </button>
            </div>
            <div className="flex items-center justify-between py-2 text-xs">
              <div className="flex items-center gap-3">
                <div className="w-7 h-7 rounded-full bg-neutral-800 text-white flex items-center justify-center font-bold text-xs">
                  J
                </div>
                <div>
                  <div className="font-semibold text-text">Jaweria</div>
                  <div className="text-muted text-[11px]">jaweria@atip.local</div>
                </div>
              </div>
              <Badge variant="neutral">Owner</Badge>
            </div>
          </div>
        )}

        {activeTab === "github" && (
          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm space-y-4 text-xs">
            <h2 className="text-sm font-semibold text-text">
              GitHub App Integration
            </h2>
            <p className="text-muted leading-relaxed">
              Connect your repositories via the official ATIP GitHub App. Requires
              OAuth setup and webhook configuration in Phase M2.
            </p>
            <div className="p-3 rounded-lg border border-border bg-soft space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-medium text-text">Installation Status</span>
                <Badge variant="warning">Setup in M2</Badge>
              </div>
              <div className="font-mono text-[11px] text-muted">
                App ID: atip-local-dev · Scopes: repository_checks, pull_requests:read
              </div>
            </div>
          </div>
        )}

        {activeTab === "ai" && (
          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm space-y-5 text-xs">
            <h2 className="text-sm font-semibold text-text">
              AI Provider Gateway
            </h2>
            <p className="text-muted leading-relaxed">
              ATIP supports multi-provider LLM gateways. Secrets are strictly masked
              and never shared across tenants.
            </p>
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-muted mb-1">
                  Google Gemini API Key
                </label>
                <div className="relative">
                  <input
                    type="password"
                    defaultValue="sk-gemini-sample-key-masked-xxxx"
                    className="w-full px-3 py-2 rounded-lg border border-border bg-surface font-mono text-xs text-text pr-10"
                  />
                  <Lock className="absolute right-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-muted mb-1">
                  Provider Privacy Consent
                </label>
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    defaultChecked
                    className="w-4 h-4 rounded border-border text-text"
                  />
                  <span className="text-muted">
                    Allow sending redacted code diffs to Gemini for failure investigation
                  </span>
                </label>
              </div>
            </div>
          </div>
        )}

        {activeTab === "execution" && (
          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm space-y-4 text-xs">
            <h2 className="text-sm font-semibold text-text">
              Sandbox Execution Policies
            </h2>
            <div className="p-3 rounded-lg border border-border bg-soft space-y-2">
              <div className="font-semibold text-text">Security Guarantee</div>
              <p className="text-muted">
                Untrusted repository code never runs on the control plane. Tests
                execute only in hardened ephemeral isolation with default-deny network
                access.
              </p>
            </div>
          </div>
        )}

        {activeTab === "notifications" && (
          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm space-y-4 text-xs">
            <h2 className="text-sm font-semibold text-text">
              Notification Preferences
            </h2>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" defaultChecked className="w-4 h-4 rounded" />
              <span>Email notifications for test run failures</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" defaultChecked className="w-4 h-4 rounded" />
              <span>Notify when high-risk commits are discovered</span>
            </label>
          </div>
        )}

        {activeTab === "audit" && (
          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm space-y-4 text-xs">
            <h2 className="text-sm font-semibold text-text">Audit Log</h2>
            <div className="divide-y divide-border font-mono text-[11px] text-muted">
              <div className="py-2 flex justify-between">
                <span>user.login.sso</span>
                <span>Today 14:22</span>
              </div>
              <div className="py-2 flex justify-between">
                <span>test_plan.approved</span>
                <span>Today 14:25</span>
              </div>
              <div className="py-2 flex justify-between">
                <span>test_run.dispatched</span>
                <span>Today 14:26</span>
              </div>
            </div>
          </div>
        )}

        {activeTab === "appearance" && (
          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm space-y-4 text-xs">
            <h2 className="text-sm font-semibold text-text">
              Theme &amp; Appearance
            </h2>
            <p className="text-muted">
              Switch between the verified light and dark themes. Preference is
              persisted in local storage.
            </p>
            <div className="pt-2">
              <ThemeToggle className="px-4 py-2 rounded-lg border border-border bg-surface text-text hover:bg-soft text-xs font-medium inline-flex items-center gap-2 cursor-pointer" />
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
