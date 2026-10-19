"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FolderGit2,
  AlertTriangle,
  Target,
  FileText,
  PlaySquare,
  Sparkles,
  BarChart3,
  Settings,
  X,
} from "lucide-react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const pathname = usePathname();

  const navItems = [
    { label: "Overview", href: "/app", icon: LayoutDashboard },
    { label: "Repositories", href: "/app/repositories", icon: FolderGit2 },
    { label: "Risk Intelligence", href: "/app/risk", icon: AlertTriangle },
    { label: "White-Box Coverage", href: "/app/coverage", icon: Target },
    { label: "Test Plans", href: "/app/test-plans", icon: FileText },
    { label: "Test Runs", href: "/app/runs", icon: PlaySquare },
    { label: "AI Analysis", href: "/app/analysis", icon: Sparkles },
    { label: "Reports", href: "/app/reports", icon: BarChart3 },
  ];

  const isActive = (href: string) => {
    if (href === "/app") {
      return pathname === "/app";
    }
    return pathname.startsWith(href);
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={twMerge(
          clsx(
            "fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-sidebar-bg text-sidebar-text border-r border-sidebar-border transition-transform duration-200 lg:static lg:translate-x-0",
            isOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
          )
        )}
      >
        {/* Brand Header */}
        <div className="flex items-center justify-between px-6 pt-7 pb-6">
          <div>
            <div className="font-bold tracking-tight text-xl text-white flex items-center gap-2">
              ATIP
            </div>
            <div className="text-[11px] leading-tight text-sidebar-muted mt-1 font-medium">
              Autonomous Testing
              <br />
              Intelligence Platform
            </div>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="lg:hidden p-1.5 text-sidebar-muted hover:text-white"
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Main Navigation */}
        <nav className="flex-1 space-y-1 px-3 py-2 overflow-y-auto">
          {navItems.map((item) => {
            const active = isActive(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                className={clsx(
                  "flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  active
                    ? "bg-sidebar-active text-white shadow-sm"
                    : "text-sidebar-muted hover:bg-sidebar-active/50 hover:text-white"
                )}
              >
                <Icon
                  className={clsx(
                    "w-4 h-4 transition-colors",
                    active ? "text-white" : "text-sidebar-muted group-hover:text-white"
                  )}
                />
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Footer / Settings & Profile */}
        <div className="p-3 border-t border-sidebar-border space-y-2">
          <Link
            href="/app/settings"
            onClick={onClose}
            className={clsx(
              "flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors",
              isActive("/app/settings")
                ? "bg-sidebar-active text-white shadow-sm"
                : "text-sidebar-muted hover:bg-sidebar-active/50 hover:text-white"
            )}
          >
            <Settings className="w-4 h-4" />
            <span>Settings</span>
          </Link>

          {/* Profile Card matching exact mockup: J / Jaweria / Personal Workspace */}
          <div className="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-sidebar-surface border border-sidebar-border/60">
            <div className="w-7 h-7 rounded-full bg-neutral-700 text-white flex items-center justify-center font-semibold text-xs shrink-0">
              J
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-xs font-semibold text-white truncate">
                Jaweria
              </div>
              <div className="text-[11px] text-sidebar-muted truncate">
                Personal Workspace
              </div>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
