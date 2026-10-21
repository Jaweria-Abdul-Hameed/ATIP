"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle({ className }: { className?: string }) {
  const { setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [isSpinning, setIsSpinning] = useState(false);

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
        <div className="w-4 h-4 flex items-center justify-center text-muted text-xs">
          ◐
        </div>
        <span>Theme</span>
      </button>
    );
  }

  const isDark = resolvedTheme === "dark";

  const handleToggle = () => {
    setIsSpinning(true);
    setTheme(isDark ? "light" : "dark");
    setTimeout(() => {
      setIsSpinning(false);
    }, 520);
  };

  return (
    <button
      onClick={handleToggle}
      type="button"
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className={
        className ||
        "px-2.5 py-1.5 rounded-lg border border-border bg-surface text-text hover:bg-soft transition-colors text-xs font-medium inline-flex items-center gap-2 cursor-pointer shadow-sm group select-none"
      }
      title={isDark ? "Active: Dark Mode (Click to switch to Light)" : "Active: Light Mode (Click to switch to Dark)"}
    >
      {/* Spring spin container transitioning smoothly between Sun and Moon */}
      <div
        className={`relative w-4 h-4 flex items-center justify-center shrink-0 ${
          isSpinning ? "animate-theme-spin" : ""
        }`}
      >
        {/* Sun Icon: Visible in Light mode, spins out on dark mode */}
        <Sun
          className={`w-4 h-4 text-amber-500 absolute transition-all duration-500 ease-out transform ${
            isDark
              ? "-rotate-90 scale-50 opacity-0 pointer-events-none"
              : "rotate-0 scale-100 opacity-100"
          }`}
        />
        {/* Moon Icon: Visible in Dark mode, spins in on dark mode */}
        <Moon
          className={`w-4 h-4 text-neutral-200 absolute transition-all duration-500 ease-out transform ${
            isDark
              ? "rotate-0 scale-100 opacity-100"
              : "rotate-90 scale-50 opacity-0 pointer-events-none"
          }`}
        />
      </div>
      <span>Theme</span>
    </button>
  );
}
