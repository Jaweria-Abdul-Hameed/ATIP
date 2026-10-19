"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ThemeToggle } from "@/components/theme-toggle";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Lock, Mail, KeyRound, Building2 } from "lucide-react";

export default function SignInPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showSsoInput, setShowSsoInput] = useState(false);
  const [ssoDomain, setSsoDomain] = useState("");
  const [loading, setLoading] = useState(false);

  // Seamless login handler: immediately navigates to /app without locking anyone out
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      router.push("/app");
    }, 400);
  };

  const handleOAuthLogin = (provider: "github" | "google") => {
    setLoading(true);
    setTimeout(() => {
      router.push("/app");
    }, 400);
  };

  return (
    <div className="min-h-screen bg-bg text-text flex flex-col justify-between p-6">
      {/* Header Bar */}
      <header className="flex items-center justify-between max-w-6xl w-full mx-auto">
        <Link href="/app" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-text text-surface font-bold text-sm flex items-center justify-center transition-transform group-hover:scale-105">
            A
          </div>
          <div>
            <div className="font-bold tracking-tight text-sm text-text leading-tight">
              ATIP
            </div>
            <div className="text-[10px] text-muted leading-tight">
              Testing Intelligence
            </div>
          </div>
        </Link>
        <ThemeToggle />
      </header>

      {/* Main Login Card */}
      <main className="w-full max-w-[420px] mx-auto my-8 p-7 sm:p-8 rounded-2xl border border-border bg-surface shadow-sm space-y-6">
        <div>
          <div className="flex items-center gap-2 mb-2.5">
            <Badge variant="neutral">Sign In</Badge>
            <span className="text-[11px] text-muted">Workspace v0.1</span>
          </div>
          <h1 className="font-serif text-3xl font-normal tracking-[-0.035em] text-text">
            Welcome back
          </h1>
          <p className="text-xs text-muted mt-1.5 leading-relaxed">
            Sign in to access your repositories, test plans, and intelligence reports.
          </p>
        </div>

        {/* 1-Click Fast Demo Pass (Never locked out) */}
        <div className="p-3 rounded-xl bg-soft border border-border/80 flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="text-xs font-semibold text-text">Quick Reviewer Pass</div>
            <div className="text-[11px] text-muted truncate">
              Instant access without credentials
            </div>
          </div>
          <Link
            href="/app"
            className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90 transition-opacity shadow-xs"
          >
            <span>Enter App</span>
            <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        {/* Social Auth Buttons: GitHub & Google */}
        <div className="space-y-2.5">
          <button
            type="button"
            onClick={() => handleOAuthLogin("github")}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2.5 px-4 py-2.5 rounded-lg border border-border bg-surface text-xs font-semibold text-text hover:bg-soft transition-colors cursor-pointer shadow-xs disabled:opacity-60"
          >
            <svg
              className="w-4 h-4 text-text shrink-0"
              viewBox="0 0 24 24"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                clipRule="evenodd"
                d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
              />
            </svg>
            <span>Continue with GitHub</span>
          </button>

          <button
            type="button"
            onClick={() => handleOAuthLogin("google")}
            disabled={loading}
            className="w-full flex items-center justify-center gap-2.5 px-4 py-2.5 rounded-lg border border-border bg-surface text-xs font-semibold text-text hover:bg-soft transition-colors cursor-pointer shadow-xs disabled:opacity-60"
          >
            <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            <span>Continue with Google</span>
          </button>
        </div>

        {/* Divider */}
        <div className="relative flex items-center justify-center">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-border" />
          </div>
          <span className="relative bg-surface px-3 text-[11px] text-muted">
            or continue with email
          </span>
        </div>

        {/* Email & Password Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-text mb-1.5">
              Work Email
            </label>
            <div className="relative">
              <Mail className="w-3.5 h-3.5 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="developer@company.com"
                className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-border bg-bg text-text placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-text"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-medium text-text">
                Password
              </label>
              <Link
                href="/forgot-password"
                className="text-[11px] text-muted hover:text-text transition-colors"
              >
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <KeyRound className="w-3.5 h-3.5 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-3 py-2 text-xs rounded-lg border border-border bg-bg text-text placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-text"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-text text-surface text-xs font-semibold hover:opacity-90 transition-opacity shadow-sm cursor-pointer disabled:opacity-60"
          >
            <Lock className="w-3.5 h-3.5" />
            <span>{loading ? "Signing in..." : "Sign In"}</span>
          </button>
        </form>

        {/* Enterprise SSO Toggle */}
        <div className="pt-2 border-t border-border">
          {!showSsoInput ? (
            <button
              type="button"
              onClick={() => setShowSsoInput(true)}
              className="w-full flex items-center justify-center gap-1.5 text-xs text-muted hover:text-text transition-colors py-1 cursor-pointer"
            >
              <Building2 className="w-3.5 h-3.5" />
              <span>Sign in with Enterprise SSO / SAML</span>
            </button>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-2 mt-2">
              <label className="block text-[11px] font-medium text-muted">
                Company domain or SSO identifier
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={ssoDomain}
                  onChange={(e) => setSsoDomain(e.target.value)}
                  placeholder="company.com"
                  className="flex-1 px-3 py-1.5 text-xs rounded-lg border border-border bg-bg text-text placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-text"
                />
                <button
                  type="submit"
                  className="px-3 py-1.5 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90 transition-opacity"
                >
                  Continue
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Link to Sign Up */}
        <div className="text-center pt-2">
          <p className="text-xs text-muted">
            Don&apos;t have an account?{" "}
            <Link
              href="/sign-up"
              className="text-text font-semibold hover:underline"
            >
              Sign up
            </Link>
          </p>
        </div>
      </main>

      {/* Footer Info */}
      <footer className="text-center text-[11px] text-muted max-w-sm mx-auto space-y-1">
        <div>ATIP · Autonomous Testing Intelligence Platform</div>
        <div className="text-[10px] text-muted/70">
          OAuth and OIDC protocols are fully provisioned in Phase M2.
        </div>
      </footer>
    </div>
  );
}
