"use client";

import React, { useState } from "react";
import Link from "next/link";
import { ThemeToggle } from "@/components/theme-toggle";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, ArrowRight, Mail, CheckCircle2, ShieldCheck } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setSent(true);
    }, 500);
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

      {/* Card */}
      <main className="w-full max-w-[420px] mx-auto my-8 p-7 sm:p-8 rounded-2xl border border-border bg-surface shadow-sm space-y-6">
        <div>
          <div className="flex items-center gap-2 mb-2.5">
            <Badge variant="neutral">Password Reset</Badge>
          </div>
          <h1 className="font-serif text-3xl font-normal tracking-[-0.035em] text-text">
            Reset your password
          </h1>
          <p className="text-xs text-muted mt-1.5 leading-relaxed">
            Enter your work email address and we&apos;ll send you instructions to
            reset your password.
          </p>
        </div>

        {!sent ? (
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

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-text text-surface text-xs font-semibold hover:opacity-90 transition-opacity shadow-sm cursor-pointer disabled:opacity-60"
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>{loading ? "Sending link..." : "Send Reset Instructions"}</span>
            </button>
          </form>
        ) : (
          <div className="p-4 rounded-xl bg-soft border border-border space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold text-text">
              <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" />
              <span>Instructions sent</span>
            </div>
            <p className="text-xs text-muted leading-relaxed">
              We&apos;ve sent an email to{" "}
              <strong className="text-text">{email}</strong> with a secure link to
              reset your password.
            </p>
            <div className="pt-2">
              <Link
                href="/app"
                className="w-full inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90 transition-opacity shadow-xs"
              >
                <span>Enter Demo Workspace</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </div>
          </div>
        )}

        <div className="pt-2 border-t border-border flex items-center justify-between text-xs">
          <Link
            href="/sign-in"
            className="inline-flex items-center gap-1.5 text-muted hover:text-text transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to sign in</span>
          </Link>

          <Link
            href="/app"
            className="text-muted hover:text-text transition-colors"
          >
            Enter workspace directly
          </Link>
        </div>
      </main>

      {/* Footer Info */}
      <footer className="text-center text-[11px] text-muted max-w-sm mx-auto space-y-1">
        <div>ATIP · Autonomous Testing Intelligence Platform</div>
        <div className="text-[10px] text-muted/70">
          Transactional email delivery is provisioned in Phase M2.
        </div>
      </footer>
    </div>
  );
}
