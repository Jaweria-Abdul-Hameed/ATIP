"use client";

import React from "react";
import { Search, Menu } from "lucide-react";
import { NotificationsPopover } from "@/components/shell/notifications-popover";

interface TopbarProps {
  onOpenMobileMenu?: () => void;
  breadcrumbs?: string[];
  searchPlaceholder?: string;
}

export function Topbar({ onOpenMobileMenu, searchPlaceholder }: TopbarProps) {
  return (
    <header className="sticky top-0 z-30 flex h-14 w-full items-center justify-between border-b border-border bg-bg/95 px-4 sm:px-6 backdrop-blur-md transition-colors">
      <div className="flex items-center gap-3 flex-1 max-w-lg">
        <button
          onClick={onOpenMobileMenu}
          className="lg:hidden p-1.5 text-muted hover:text-text"
          aria-label="Open sidebar navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="relative w-full max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted" />
          <input
            type="text"
            placeholder={searchPlaceholder || "Search repositories, runs, or files..."}
            className="w-full pl-9 pr-3 py-1.5 rounded-lg border border-border bg-surface text-xs text-text placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-text transition-all"
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <NotificationsPopover />
      </div>
    </header>
  );
}
