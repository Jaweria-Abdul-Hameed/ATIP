"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  User,
  Building,
  Shield,
  LogOut,
  Check,
  ChevronsUpDown,
  ExternalLink,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface ProfilePopoverProps {
  variant?: "topbar" | "sidebar";
  onCloseParent?: () => void;
}

export function ProfilePopover({
  variant = "topbar",
  onCloseParent,
}: ProfilePopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeWorkspace, setActiveWorkspace] = useState("Personal Workspace");
  const containerRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  // Close on outside click or Escape key
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const handleSignOut = () => {
    setIsOpen(false);
    if (onCloseParent) onCloseParent();
    router.push("/sign-in");
  };

  const handleNavigate = (path: string) => {
    setIsOpen(false);
    if (onCloseParent) onCloseParent();
    router.push(path);
  };

  if (variant === "sidebar") {
    return (
      <div className="relative w-full" ref={containerRef}>
        {/* Sidebar Trigger: The bottom-left profile card */}
        <button
          type="button"
          onClick={() => setIsOpen((prev) => !prev)}
          className="w-full flex items-center justify-between gap-3 px-3 py-2.5 rounded-lg bg-sidebar-surface border border-sidebar-border/60 hover:border-sidebar-border hover:bg-sidebar-active/60 transition-colors text-left cursor-pointer group"
          aria-expanded={isOpen}
          aria-label="User profile menu"
        >
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-7 h-7 rounded-full bg-neutral-700 text-white flex items-center justify-center font-semibold text-xs shrink-0 ring-1 ring-white/10 group-hover:ring-white/20 transition-all">
              J
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-semibold text-white truncate">
                Jaweria
              </div>
              <div className="text-[11px] text-sidebar-muted truncate">
                {activeWorkspace}
              </div>
            </div>
          </div>
          <ChevronsUpDown className="w-3.5 h-3.5 text-sidebar-muted group-hover:text-white transition-colors shrink-0" />
        </button>

        {/* Sidebar Popover (opens upward) */}
        {isOpen && (
          <div className="absolute bottom-full mb-2 left-0 w-64 rounded-xl border border-sidebar-border bg-sidebar-surface text-white shadow-2xl z-50 overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-150">
            {/* User Header */}
            <div className="p-3.5 border-b border-sidebar-border/80">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-neutral-700 text-white flex items-center justify-center font-bold text-sm shrink-0">
                  J
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-xs font-semibold text-white truncate">
                    Jaweria
                  </div>
                  <div className="text-[11px] text-sidebar-muted truncate">
                    jaweria@atip.local
                  </div>
                  <div className="mt-1">
                    <span className="inline-block px-1.5 py-0.5 rounded text-[10px] font-medium bg-white/10 text-neutral-200">
                      Owner
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Workspace Switcher */}
            <div className="p-2 border-b border-sidebar-border/80">
              <div className="text-[10px] font-semibold text-sidebar-muted uppercase tracking-wider px-2 py-1">
                Workspaces
              </div>
              <button
                type="button"
                onClick={() => setActiveWorkspace("Personal Workspace")}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs text-sidebar-text hover:bg-sidebar-active transition-colors text-left"
              >
                <div className="truncate">Personal Workspace</div>
                {activeWorkspace === "Personal Workspace" && (
                  <Check className="w-3.5 h-3.5 text-white shrink-0" />
                )}
              </button>
              <button
                type="button"
                onClick={() => setActiveWorkspace("Acme Workspace")}
                className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs text-sidebar-text hover:bg-sidebar-active transition-colors text-left"
              >
                <div className="truncate">Acme Workspace</div>
                {activeWorkspace === "Acme Workspace" && (
                  <Check className="w-3.5 h-3.5 text-white shrink-0" />
                )}
              </button>
            </div>

            {/* Quick Links */}
            <div className="p-1.5 space-y-0.5">
              <button
                type="button"
                onClick={() => handleNavigate("/app/settings?tab=profile")}
                className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs text-sidebar-text hover:bg-sidebar-active hover:text-white transition-colors text-left cursor-pointer"
              >
                <User className="w-3.5 h-3.5 text-sidebar-muted" />
                <span>Profile Settings</span>
              </button>
              <button
                type="button"
                onClick={() => handleNavigate("/app/settings?tab=members")}
                className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs text-sidebar-text hover:bg-sidebar-active hover:text-white transition-colors text-left cursor-pointer"
              >
                <Building className="w-3.5 h-3.5 text-sidebar-muted" />
                <span>Organization & Members</span>
              </button>
              <button
                type="button"
                onClick={() => handleNavigate("/app/settings?tab=execution")}
                className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs text-sidebar-text hover:bg-sidebar-active hover:text-white transition-colors text-left cursor-pointer"
              >
                <Shield className="w-3.5 h-3.5 text-sidebar-muted" />
                <span>Security & Execution Policies</span>
              </button>
            </div>

            {/* Sign Out */}
            <div className="p-1.5 border-t border-sidebar-border/80">
              <button
                type="button"
                onClick={handleSignOut}
                className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-colors text-left cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign out</span>
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  // Variant: Topbar Avatar Button & Popover (opens downward)
  return (
    <div className="relative" ref={containerRef}>
      {/* Topbar Trigger: The avatar button */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        className="w-7 h-7 rounded-full bg-neutral-800 text-white flex items-center justify-center font-semibold text-xs shrink-0 cursor-pointer hover:ring-2 hover:ring-neutral-400 dark:hover:ring-neutral-600 focus:outline-none focus:ring-2 focus:ring-text transition-all"
        aria-expanded={isOpen}
        aria-label="User account menu"
        title="Jaweria (jaweria@atip.local)"
      >
        J
      </button>

      {/* Topbar Popover (opens downward) */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-64 rounded-xl border border-border bg-surface text-text shadow-xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-1 duration-150">
          {/* User Header */}
          <div className="p-3.5 border-b border-border bg-soft/30">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-neutral-800 text-white flex items-center justify-center font-bold text-sm shrink-0">
                J
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-xs font-semibold text-text truncate">
                  Jaweria
                </div>
                <div className="text-[11px] text-muted truncate">
                  jaweria@atip.local
                </div>
                <div className="mt-1">
                  <Badge variant="neutral" className="text-[10px] px-1.5 py-0.2">
                    Owner
                  </Badge>
                </div>
              </div>
            </div>
          </div>

          {/* Workspaces */}
          <div className="p-2 border-b border-border">
            <div className="text-[10px] font-semibold text-muted uppercase tracking-wider px-2 py-1">
              Active Workspace
            </div>
            <button
              type="button"
              onClick={() => setActiveWorkspace("Acme Workspace")}
              className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs text-text hover:bg-soft transition-colors text-left"
            >
              <div className="truncate">Acme Workspace</div>
              {activeWorkspace === "Acme Workspace" && (
                <Check className="w-3.5 h-3.5 text-text shrink-0" />
              )}
            </button>
            <button
              type="button"
              onClick={() => setActiveWorkspace("Personal Workspace")}
              className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs text-text hover:bg-soft transition-colors text-left"
            >
              <div className="truncate">Personal Workspace</div>
              {activeWorkspace === "Personal Workspace" && (
                <Check className="w-3.5 h-3.5 text-text shrink-0" />
              )}
            </button>
          </div>

          {/* Quick Links */}
          <div className="p-1.5 space-y-0.5">
            <button
              type="button"
              onClick={() => handleNavigate("/app/settings?tab=profile")}
              className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs text-text hover:bg-soft transition-colors text-left cursor-pointer"
            >
              <User className="w-3.5 h-3.5 text-muted" />
              <span>Profile Settings</span>
            </button>
            <button
              type="button"
              onClick={() => handleNavigate("/app/settings?tab=members")}
              className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs text-text hover:bg-soft transition-colors text-left cursor-pointer"
            >
              <Building className="w-3.5 h-3.5 text-muted" />
              <span>Organization & Members</span>
            </button>
            <button
              type="button"
              onClick={() => handleNavigate("/app/settings?tab=execution")}
              className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs text-text hover:bg-soft transition-colors text-left cursor-pointer"
            >
              <Shield className="w-3.5 h-3.5 text-muted" />
              <span>Security & Execution Policies</span>
            </button>
          </div>

          {/* Sign Out */}
          <div className="p-1.5 border-t border-border bg-soft/20">
            <button
              type="button"
              onClick={handleSignOut}
              className="w-full flex items-center gap-2.5 px-2.5 py-1.5 rounded-lg text-xs text-red-600 dark:text-red-400 hover:bg-red-500/10 transition-colors text-left cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
