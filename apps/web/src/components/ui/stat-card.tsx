import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

interface StatCardProps {
  label?: string;
  value: string | number;
  sublabel?: string;
  icon?: React.ReactNode;
  className?: string;
  topLabel?: boolean;
}

export function StatCard({
  label,
  value,
  sublabel,
  icon,
  className,
  topLabel = false,
}: StatCardProps) {
  return (
    <div
      className={twMerge(
        clsx(
          "p-5 rounded-xl border border-border bg-surface shadow-sm transition-all",
          className
        )
      )}
    >
      {topLabel && label && (
        <div className="text-xs font-medium text-muted mb-2">{label}</div>
      )}
      <div className="flex items-center justify-between">
        <div className="text-2xl sm:text-3xl font-semibold tracking-tight text-text flex items-center gap-2">
          {icon}
          <span>{value}</span>
        </div>
      </div>
      {!topLabel && label && (
        <div className="text-xs font-medium text-muted mt-2">{label}</div>
      )}
      {sublabel && (
        <div className="text-[11px] text-muted/80 mt-1">{sublabel}</div>
      )}
    </div>
  );
}
