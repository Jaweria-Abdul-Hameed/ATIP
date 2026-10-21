"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle({ className }: { className?: string }) {
  const { setTheme, resolvedTheme } = useTheme();
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
        <div className="w-3.5 h-3.5 flex items-center justify-center text-muted text-xs">
          ◐
        </div>
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
        "px-2.5 py-1.5 rounded-lg border border-border bg-surface text-text hover:bg-soft transition-colors text-xs font-medium inline-flex items-center gap-1.5 cursor-pointer shadow-sm group select-none"
      }
      title={isDark ? "Switch to light mode" : "Switch to dark mode"}
    >
      {/* Smooth spinning container transitioning between Sun and Moon */}
      <div className="relative w-3.5 h-3.5 flex items-center justify-center shrink-0 overflow-hidden">
        <Sun
          className={`w-3.5 h-3.5 text-amber-400 absolute transition-all duration-300 ease-out transform ${
            isDark
              ? "rotate-0 scale-100 opacity-100"
              : "-rotate-90 scale-0 opacity-0"
          }`}
        />
        <Moon
          className={`w-3.5 h-3.5 text-muted absolute transition-all duration-300 ease-out transform ${
            isDark
              ? "rotate-90 scale-0 opacity-0"
              : "rotate-0 scale-100 opacity-100"
          }`}
        />
      </div>
      <span>Theme</span>
    </button>
  );
}
