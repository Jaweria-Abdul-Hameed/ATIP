"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <button
        aria-label="Toggle theme"
        className={
          className ||
          "px-2.5 py-1.5 rounded-lg border border-border bg-surface text-text text-xs font-medium inline-flex items-center gap-1.5"
        }
      >
        <span className="text-muted text-sm">◐</span>
        <span>Theme</span>
      </button>
    );
  }

  const isDark = resolvedTheme === "dark";

  return (
    <button
      onClick={() => setTheme(isDark ? "light" : "dark")}
      aria-label="Toggle light or dark theme"
      className={
        className ||
        "px-2.5 py-1.5 rounded-lg border border-border bg-surface text-text hover:bg-soft transition-colors text-xs font-medium inline-flex items-center gap-1.5 cursor-pointer shadow-sm"
      }
      title={isDark ? "Switch to light mode" : "Switch to dark mode"}
    >
      {isDark ? (
        <Sun className="w-3.5 h-3.5 text-amber-400" />
      ) : (
        <Moon className="w-3.5 h-3.5 text-muted" />
      )}
      <span>Theme</span>
    </button>
  );
}
