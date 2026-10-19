"use client";

import React from "react";
import Link from "next/link";
import { ThemeToggle } from "@/components/theme-toggle";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Lock } from "lucide-react";

export default function SignInPage() {
  return (
    <div className="min-h-screen bg-bg text-text flex flex-col justify-between p-6">
      <div className="flex items-center justify-between">
        <div className="font-bold tracking-tight text-xl text-text">
          ATIP
        </div>
        <ThemeToggle />
      </div>

      <div className="w-full max-w-sm mx-auto my-auto p-8 rounded-2xl border border-border bg-surface shadow-md space-y-6">
        <div>
          <Badge variant="neutral" className="mb-3">
            OIDC Authentication
          </Badge>
          <h1 className="font-serif text-2xl font-normal text-text">
            Welcome to ATIP
          </h1>
          <p className="text-xs text-muted mt-1 leading-relaxed">
            Autonomous Testing Intelligence Platform. Sign in with your organization
            Single Sign-On.
          </p>
        </div>

        <div className="space-y-3">
          <Link
            href="/app"
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-text text-surface text-xs font-semibold hover:opacity-90 transition-opacity shadow-sm"
          >
            <Lock className="w-3.5 h-3.5" />
            <span>Continue with SSO</span>
          </Link>

          <Link
            href="/app"
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft transition-colors"
          >
            <span>Enter Demo Workspace</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="pt-4 border-t border-border text-[11px] text-muted text-center leading-relaxed">
          Production OIDC identity provider integration is provisioned in Phase M2.
        </div>
      </div>

      <div className="text-center text-[11px] text-muted">
        ATIP · Autonomous Testing Intelligence Platform
      </div>
    </div>
  );
}
