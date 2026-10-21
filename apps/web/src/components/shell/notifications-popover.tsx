"use client";

import React, { useState, useRef, useEffect } from "react";
import Link from "next/link";
import {
  Bell,
  CheckCircle2,
  AlertTriangle,
  FileCode2,
  FolderGit2,
  Check,
  ArrowRight,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface NotificationItem {
  id: string;
  icon: React.ElementType;
  iconColor: string;
  title: string;
  description: string;
  timestamp: string;
  unread: boolean;
  href: string;
}

const INITIAL_NOTIFICATIONS: NotificationItem[] = [
  {
    id: "notif-1",
    icon: CheckCircle2,
    iconColor: "text-emerald-500",
    title: "Test Run Completed",
    description: "nextjs-dashboard: #RUN-1042 passed all 32 assertions.",
    timestamp: "2 min ago",
    unread: true,
    href: "/app/runs/run-1042",
  },
  {
    id: "notif-2",
    icon: AlertTriangle,
    iconColor: "text-amber-500",
    title: "High Risk Detected",
    description: "api-service: 12 high-risk changes identified in session auth.",
    timestamp: "18 min ago",
    unread: true,
    href: "/app/risk",
  },
  {
    id: "notif-3",
    icon: FileCode2,
    iconColor: "text-neutral-400",
    title: "MC/DC Proof Required",
    description: "White-box condition independence test pairs pending execution.",
    timestamp: "1 hour ago",
    unread: true,
    href: "/app/coverage",
  },
  {
    id: "notif-4",
    icon: FolderGit2,
    iconColor: "text-neutral-400",
    title: "Repository Synced",
    description: "mobile-app: main branch updated with 4 new commits.",
    timestamp: "2 hours ago",
    unread: false,
    href: "/app/repositories",
  },
];

export function NotificationsPopover() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>(
    INITIAL_NOTIFICATIONS
  );
  const containerRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter((n) => n.unread).length;

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, unread: false })));
  };

  const markAsRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, unread: false } : n))
    );
  };

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

  return (
    <div className="relative" ref={containerRef}>
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen((prev) => !prev)}
        className="p-2 rounded-lg border border-border bg-surface text-muted hover:text-text hover:bg-soft transition-colors relative cursor-pointer focus:outline-none focus:ring-1 focus:ring-text"
        aria-label="Notifications"
        aria-expanded={isOpen}
        title="Notifications"
      >
        <Bell className="w-4 h-4" />
        {unreadCount > 0 && (
          <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
        )}
      </button>

      {/* Popover Card */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-80 sm:w-96 rounded-xl border border-border bg-surface shadow-xl z-50 overflow-hidden animate-in fade-in slide-in-from-top-1 duration-150">
          {/* Header */}
          <div className="flex items-center justify-between p-3.5 border-b border-border bg-surface">
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-text">Notifications</span>
              {unreadCount > 0 ? (
                <Badge variant="neutral" className="text-[10px] px-1.5 py-0.5">
                  {unreadCount} new
                </Badge>
              ) : (
                <span className="text-[11px] text-muted">All caught up</span>
              )}
            </div>

            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="text-[11px] font-medium text-muted hover:text-text flex items-center gap-1 transition-colors cursor-pointer"
              >
                <Check className="w-3 h-3" />
                <span>Mark all read</span>
              </button>
            )}
          </div>

          {/* Notifications List */}
          <div className="divide-y divide-border/60 max-h-80 overflow-y-auto">
            {notifications.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.id}
                  href={item.href}
                  onClick={() => {
                    markAsRead(item.id);
                    setIsOpen(false);
                  }}
                  className="flex items-start gap-3 p-3.5 hover:bg-soft/70 transition-colors group relative text-left"
                >
                  <div className="p-1.5 rounded-lg bg-soft text-muted group-hover:text-text transition-colors shrink-0 mt-0.5">
                    <Icon className={`w-3.5 h-3.5 ${item.iconColor}`} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <div className="text-xs font-semibold text-text truncate">
                        {item.title}
                      </div>
                      <span className="text-[10px] text-muted shrink-0">
                        {item.timestamp}
                      </span>
                    </div>
                    <p className="text-[11px] text-muted mt-0.5 leading-snug line-clamp-2">
                      {item.description}
                    </p>
                  </div>

                  {item.unread && (
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0 self-center" />
                  )}
                </Link>
              );
            })}
          </div>

          {/* Footer */}
          <div className="p-2.5 border-t border-border bg-soft/40 flex items-center justify-between text-xs">
            <Link
              href="/app/runs"
              onClick={() => setIsOpen(false)}
              className="text-[11px] font-medium text-muted hover:text-text transition-colors flex items-center gap-1"
            >
              <span>View all test activity</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
            <Link
              href="/app/settings"
              onClick={() => setIsOpen(false)}
              className="text-[11px] text-muted hover:text-text transition-colors"
            >
              Settings
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
