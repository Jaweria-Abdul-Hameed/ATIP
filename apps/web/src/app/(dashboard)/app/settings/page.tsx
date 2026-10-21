"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { AppShell } from "@/components/shell/app-shell";
import { ThemeToggle } from "@/components/theme-toggle";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api-adapter";
import { MemberApiItem, GitHubInstallationApiItem } from "@/lib/api-client";
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
  Lock,
  Plus,
  X,
  ExternalLink,
} from "lucide-react";

type SettingsTab =
  | "profile"
  | "organization"
  | "members"
  | "github"
  | "ai"
  | "execution"
  | "notifications"
  | "audit"
  | "appearance";

const VALID_TABS: SettingsTab[] = [
  "profile",
  "organization",
  "members",
  "github",
  "ai",
  "execution",
  "notifications",
  "audit",
  "appearance",
];

function SettingsContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const tabParam = searchParams.get("tab") as SettingsTab | null;

  const initialTab =
    tabParam && VALID_TABS.includes(tabParam) ? tabParam : "profile";
  const [activeTab, setActiveTab] = useState<SettingsTab>(initialTab);
  const [saved, setSaved] = useState(false);
  const [members, setMembers] = useState<MemberApiItem[]>([]);
  const [installations, setInstallations] = useState<GitHubInstallationApiItem[]>([]);
  const [installUrl, setInstallUrl] = useState("");
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState("developer");
  const [isInviting, setIsInviting] = useState(false);
  const [inviteSuccess, setInviteSuccess] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function loadTabData() {
      if (activeTab === "members") {
        try {
          const list = await api.getOrganizationMembers("org_default_workspace");
          if (isMounted) setMembers(list);
        } catch {
          if (isMounted) setMembers([]);
        }
      } else if (activeTab === "github") {
        try {
          const [insts, url] = await Promise.all([
            api.getGitHubInstallations(),
            api.getGitHubInstallUrl(),
          ]);
          if (isMounted) {
            setInstallations(insts);
            setInstallUrl(url);
          }
        } catch {
          // fallback
        }
      }
    }
    loadTabData();
    return () => {
      isMounted = false;
    };
  }, [activeTab]);

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail) return;
    setIsInviting(true);
    try {
      await api.inviteMember("org_default_workspace", inviteEmail, inviteRole);
      setInviteSuccess(true);
      const list = await api.getOrganizationMembers("org_default_workspace");
      setMembers(list);
      setTimeout(() => {
        setShowInviteModal(false);
        setInviteSuccess(false);
        setInviteEmail("");
      }, 1500);
    } catch (err) {
      console.error("Invite failed:", err);
    } finally {
      setIsInviting(false);
    }
  };

  useEffect(() => {
    if (tabParam && VALID_TABS.includes(tabParam)) {
      setActiveTab(tabParam);
    }
  }, [tabParam]);

  const handleTabChange = (newTab: SettingsTab) => {
    setActiveTab(newTab);
    router.replace(`/app/settings?tab=${newTab}`, { scroll: false });
  };

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const tabs = [
    { id: "profile" as const, label: "Profile", icon: User },
    { id: "organization" as const, label: "Organization", icon: Building },
    { id: "members" as const, label: "Members & Roles", icon: Users },
    { id: "github" as const, label: "GitHub App", icon: Github },
    { id: "ai" as const, label: "AI Providers", icon: Sparkles },
    { id: "execution" as const, label: "Execution Policies", icon: Shield },
    { id: "notifications" as const, label: "Notifications", icon: Bell },
    { id: "audit" as const, label: "Audit Log", icon: FileText },
    { id: "appearance" as const, label: "Appearance", icon: Palette },
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
              onClick={() => handleTabChange(tab.id)}
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
              <div>
                <h2 className="text-sm font-semibold text-text">
                  Workspace Members ({members.length > 0 ? members.length : 1})
                </h2>
                <p className="text-xs text-muted">Manage roles and invitations for your organization.</p>
              </div>
              <button
                onClick={() => setShowInviteModal(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-border text-xs font-medium text-text hover:bg-soft cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Invite Member</span>
              </button>
            </div>

            <div className="divide-y divide-border">
              {members.length > 0 ? (
                members.map((m) => (
                  <div key={m.id} className="flex items-center justify-between py-3 text-xs">
                    <div className="flex items-center gap-3">
                      <div className="w-7 h-7 rounded-full bg-neutral-800 text-white flex items-center justify-center font-bold text-xs uppercase">
                        {m.name.charAt(0) || "U"}
                      </div>
                      <div>
                        <div className="font-semibold text-text">{m.name}</div>
                        <div className="text-muted text-[11px]">{m.email}</div>
                      </div>
                    </div>
                    <Badge variant={m.role === "owner" ? "neutral" : m.role === "admin" ? "warning" : "default"}>
                      {m.role.toUpperCase()}
                    </Badge>
                  </div>
                ))
              ) : (
                <div className="flex items-center justify-between py-3 text-xs">
                  <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-full bg-neutral-800 text-white flex items-center justify-center font-bold text-xs">
                      J
                    </div>
                    <div>
                      <div className="font-semibold text-text">Jaweria (Lead Engineer)</div>
                      <div className="text-muted text-[11px]">jaweria@atip.local</div>
                    </div>
                  </div>
                  <Badge variant="neutral">OWNER</Badge>
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "github" && (
          <div className="rounded-xl border border-border bg-surface p-6 shadow-sm space-y-4 text-xs">
            <div className="flex items-center justify-between pb-2 border-b border-border">
              <div>
                <h2 className="text-sm font-semibold text-text">
                  GitHub App Integration
                </h2>
                <p className="text-muted leading-relaxed mt-0.5">
                  Phase M2 verified GitHub App installation, installation tokens, and signed webhooks.
                </p>
              </div>
              <a
                href={installUrl || "https://github.com/apps/atip-testing-platform/installations/new"}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-text text-surface font-medium text-xs hover:opacity-90 transition-opacity"
              >
                <Github className="w-3.5 h-3.5" />
                <span>Configure App</span>
                <ExternalLink className="w-3 h-3 ml-0.5" />
              </a>
            </div>

            <div className="p-3.5 rounded-lg border border-border bg-soft space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Github className="w-4 h-4 text-text" />
                  <span className="font-medium text-text">
                    {installations.length > 0 ? installations[0].account_login : "ATIP Testing App"}
                  </span>
                </div>
                <Badge variant={installations.length > 0 ? "success" : "neutral"}>
                  {installations.length > 0 ? "Installed & Active" : "Ready to Install"}
                </Badge>
              </div>
              <div className="font-mono text-[11px] text-muted space-y-1">
                <div>Installation ID: {installations.length > 0 ? installations[0].installation_id : "12345678"}</div>
                <div>Scopes: repository_checks:write, pull_requests:write, contents:read</div>
                <div>Webhooks: HMAC-SHA256 verified, outbox durable ingestion</div>
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
              Sandbox Execution & Security Policies
            </h2>
            <div className="p-4 rounded-lg border border-border bg-soft space-y-3">
              <div className="font-semibold text-text flex items-center gap-2">
                <Shield className="w-4 h-4 text-emerald-500" />
                <span>Hardened Ephemeral Runner</span>
              </div>
              <p className="text-muted leading-relaxed">
                Untrusted repository code never runs on the control plane or web host.
                Tests execute exclusively in hardened, ephemeral Docker/gVisor sandboxes
                with default-deny network access and strict CPU/memory quotas.
              </p>
              <div className="pt-2 flex items-center gap-2">
                <Badge variant="neutral">Default-Deny Egress</Badge>
                <Badge variant="neutral">2.0 CPU / 2048 MB Limit</Badge>
                <Badge variant="neutral">Read-Only Root FS</Badge>
              </div>
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

      {/* Invite Member Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-xl border border-border bg-surface p-6 shadow-xl">
            <div className="flex items-center justify-between pb-4 border-b border-border">
              <h3 className="text-sm font-semibold text-text">
                Invite Workspace Member
              </h3>
              <button
                onClick={() => setShowInviteModal(false)}
                className="text-muted hover:text-text p-1 rounded-md"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleInvite} className="py-4 space-y-4 text-xs">
              <div>
                <label className="block text-xs font-medium text-muted mb-1.5">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  placeholder="engineer@company.com"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-surface text-xs text-text focus:outline-none focus:ring-1 focus:ring-text"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-muted mb-1.5">
                  Role (RBAC)
                </label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-border bg-surface text-xs text-text focus:outline-none focus:ring-1 focus:ring-text"
                >
                  <option value="developer">Developer (Run tests, view plans)</option>
                  <option value="maintainer">Maintainer (Manage repo, test config)</option>
                  <option value="admin">Admin (Manage members, integrations)</option>
                  <option value="viewer">Viewer (Read-only)</option>
                </select>
              </div>

              {inviteSuccess && (
                <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-medium">
                  Invitation sent successfully!
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowInviteModal(false)}
                  className="px-3 py-1.5 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isInviting || inviteSuccess}
                  className="px-3.5 py-1.5 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90 disabled:opacity-50"
                >
                  {isInviting ? "Sending..." : "Send Invitation"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppShell>
  );
}

export default function SettingsPage() {
  return (
    <Suspense
      fallback={
        <AppShell breadcrumbs={["Settings"]}>
          <div className="pt-2 pb-6 border-b border-border">
            <h1 className="font-serif text-3xl sm:text-4xl font-normal tracking-tight text-text">
              Settings
            </h1>
          </div>
        </AppShell>
      }
    >
      <SettingsContent />
    </Suspense>
  );
}
