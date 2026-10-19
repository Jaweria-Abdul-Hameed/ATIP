"use client";

import React from "react";
import { Search, Bell, Menu } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import { Badge } from "@/components/ui/badge";

interface TopbarProps {
  onOpenMobileMenu?: () => void;
  breadcrumbs?: string[];
}

export function Topbar({ onOpenMobileMenu, breadcrumbs }: TopbarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-border bg-surface/90 px-4 sm:px-8 backdrop-blur-md transition-colors">
      <div className="flex items-center gap-3 flex-1 max-w-xl">
        <button
          onClick={onOpenMobileMenu}
          className="lg:hidden p-2 rounded-lg border border-border text-muted hover:text-text hover:bg-soft transition-colors"
          aria-label="Open sidebar navigation"
        >
          <Menu className="w-4 h-4" />
        </button>

        {breadcrumbs && breadcrumbs.length > 0 ? (
          <nav className="flex items-center text-xs font-medium text-muted gap-2">
            <span>Acme Workspace</span>
            <span>/</span>
            {breadcrumbs.map((crumb, idx) => (
              <React.Fragment key={idx}>
                {idx > 0 && <span>/</span>}
                <span
                  className={
                    idx === breadcrumbs.length - 1
                      ? "text-text font-semibold"
                      : ""
                  }
                >
                  {crumb}
                </span>
              </React.Fragment>
            ))}
          </nav>
        ) : (
          <div className="relative w-full max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
            <input
              type="text"
              placeholder="Search repositories, runs, or files..."
              className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-border bg-surface text-xs text-text placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-text transition-all"
            />
          </div>
        )}
      </div>

      <div className="flex items-center gap-3">
        <Badge variant="neutral" className="hidden sm:inline-flex uppercase tracking-wider text-[10px]">
          Demo data
        </Badge>

        <ThemeToggle />

        <button
          className="p-2 rounded-lg border border-border bg-surface text-muted hover:text-text hover:bg-soft transition-colors relative"
          aria-label="Notifications"
          title="Notifications"
        >
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-amber-500" />
        </button>

        <div className="w-7 h-7 rounded-full bg-neutral-800 text-white flex items-center justify-center font-semibold text-xs shrink-0 cursor-default">
          J
        </div>
      </div>
    </header>
  );
}
