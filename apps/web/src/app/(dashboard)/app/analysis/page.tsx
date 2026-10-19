"use client";

import React, { useState } from "react";
import { AppShell } from "@/components/shell/app-shell";
import { Badge } from "@/components/ui/badge";
import { DEMO_AI_INVESTIGATION } from "@/lib/fixtures";
import {
  Sparkles,
  Send,
  FileCode,
  ShieldAlert,
  ArrowRight,
  GitPullRequest,
  CheckCircle2,
} from "lucide-react";

export default function AIAnalysisPage() {
  const [selectedInvestigation, setSelectedInvestigation] = useState("inv-1");
  const [messages, setMessages] = useState(DEMO_AI_INVESTIGATION.messages);
  const [inputVal, setInputVal] = useState("");
  const [prModalOpen, setPrModalOpen] = useState(false);

  const investigations = [
    {
      id: "inv-1",
      title: "RUN-1041 · Session middleware failure",
      timestamp: "1 hour ago",
      status: "Investigated",
    },
    {
      id: "inv-2",
      title: "RUN-1037 · Payment gateway timeout",
      timestamp: "Yesterday",
      status: "Closed",
    },
    {
      id: "inv-3",
      title: "RUN-1033 · Flaky DB connection pool",
      timestamp: "3 days ago",
      status: "Closed",
    },
  ];

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputVal.trim()) return;

    const userMsg = { sender: "user" as const, text: inputVal };
    const botMsg = {
      sender: "atip" as const,
      text: `Based on sandbox logs and AST analysis for query "${inputVal}", the failed assertion correlates with an edge-case branch in session timestamp comparisons.\n\nThis finding is categorized as an evidence-grounded HYPOTHESIS.`,
      isHypothesis: true,
      citations: [
        "Sandbox execution trace #RUN-1041:L142",
        "AST Branch target: src/auth/session.ts",
      ],
    };

    setMessages([...messages, userMsg, botMsg]);
    setInputVal("");
  };

  return (
    <AppShell breadcrumbs={["AI Analysis"]}>
      {/* Header */}
      <div className="pt-2 pb-6 border-b border-border">
        <h1 className="font-serif text-3xl sm:text-4xl font-normal tracking-tight text-text">
          AI Failure Analysis
        </h1>
        <p className="mt-1 text-xs sm:text-sm text-muted">
          Grounded failure triage from actual run logs, code diffs, and coverage
          evidence.
        </p>
      </div>

      {/* Split-pane Claude-like Layout */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-12 rounded-xl border border-border bg-surface overflow-hidden shadow-sm min-h-[560px]">
        {/* Left Aside: Investigation History */}
        <aside className="md:col-span-4 border-r border-border bg-soft/40 p-4 space-y-3">
          <div className="text-xs font-semibold text-text px-2 pb-1">
            Recent Investigations
          </div>

          <div className="space-y-1.5">
            {investigations.map((inv) => (
              <button
                key={inv.id}
                onClick={() => setSelectedInvestigation(inv.id)}
                className={`w-full text-left p-3 rounded-lg border transition-all cursor-pointer ${
                  selectedInvestigation === inv.id
                    ? "bg-surface border-border shadow-xs"
                    : "border-transparent hover:bg-soft text-muted hover:text-text"
                }`}
              >
                <div className="text-xs font-semibold text-text truncate">
                  {inv.title}
                </div>
                <div className="flex items-center justify-between mt-1 text-[11px] text-muted">
                  <span>{inv.timestamp}</span>
                  <Badge variant="neutral">{inv.status}</Badge>
                </div>
              </button>
            ))}
          </div>

          <div className="pt-4 border-t border-border px-2 text-[11px] text-muted">
            Model Gateway: <span className="font-mono text-text">Gemini 1.5 Pro</span> (deterministic grounding enabled)
          </div>
        </aside>

        {/* Right Pane: Conversation & Evidence */}
        <div className="md:col-span-8 flex flex-col justify-between p-6">
          {/* Chat Messages */}
          <div className="space-y-5 overflow-y-auto max-h-[460px] pr-2">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex flex-col ${
                  msg.sender === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`max-w-xl rounded-xl p-4 text-xs leading-relaxed ${
                    msg.sender === "user"
                      ? "bg-text text-surface font-medium"
                      : "bg-soft border border-border text-text shadow-xs"
                  }`}
                >
                  {msg.sender === "atip" && (
                    <div className="flex items-center gap-2 pb-2 mb-2 border-b border-border/80">
                      <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                      <span className="font-semibold text-text">
                        ATIP Grounded Triage
                      </span>
                      {msg.isHypothesis && (
                        <Badge variant="warning" className="text-[10px]">
                          Hypothesis
                        </Badge>
                      )}
                    </div>
                  )}

                  <div className="whitespace-pre-line">{msg.text}</div>

                  {msg.citations && msg.citations.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-border/80 space-y-1.5">
                      <div className="text-[11px] font-semibold text-muted uppercase tracking-wider">
                        Evidence Citations
                      </div>
                      {msg.citations.map((c, ci) => (
                        <div
                          key={ci}
                          className="flex items-center gap-1.5 font-mono text-[11px] text-muted"
                        >
                          <FileCode className="w-3 h-3 text-text shrink-0" />
                          <span>{c}</span>
                        </div>
                      ))}

                      <div className="pt-2 flex items-center gap-2">
                        <button
                          onClick={() => setPrModalOpen(true)}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface border border-border text-xs font-medium text-text hover:bg-soft transition-colors shadow-xs cursor-pointer"
                        >
                          <GitPullRequest className="w-3.5 h-3.5 text-muted" />
                          <span>Suggest Remediation PR</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Chat Input */}
          <form onSubmit={handleSend} className="mt-6 flex items-center gap-2">
            <input
              type="text"
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              placeholder="Ask about test failures, coverage gaps, or error logs..."
              className="flex-1 px-4 py-2.5 rounded-lg border border-border bg-surface text-xs text-text placeholder:text-muted focus:outline-none focus:ring-1 focus:ring-text"
            />
            <button
              type="submit"
              className="p-2.5 rounded-lg bg-text text-surface hover:opacity-90 transition-opacity cursor-pointer shadow-sm"
              aria-label="Send message"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>

      {/* Suggest Remediation PR Approval Modal */}
      {prModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs">
          <div className="w-full max-w-md rounded-xl border border-border bg-surface p-6 shadow-2xl">
            <div className="flex items-center gap-2 pb-2">
              <ShieldAlert className="w-4 h-4 text-amber-500" />
              <h3 className="text-sm font-semibold text-text">
                Human Approval Gate Required
              </h3>
            </div>
            <p className="text-xs text-muted leading-relaxed pb-4">
              Per security policy, AI agents cannot approve or directly execute
              pull request creation or code modifications without verified human
              server-side authorization.
            </p>
            <div className="p-3 rounded-lg border border-border bg-soft font-mono text-[11px] text-text mb-4">
              Proposed Branch: atip/fix-session-timezone
              <br />
              Target Repository: jaweria/nextjs-dashboard
              <br />
              Modified Files: 1 (src/auth/session.ts)
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setPrModalOpen(false)}
                className="px-3 py-1.5 rounded-lg border border-border bg-surface text-xs font-medium text-text hover:bg-soft"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  alert("PR suggestion queued for human review.");
                  setPrModalOpen(false);
                }}
                className="px-3.5 py-1.5 rounded-lg bg-text text-surface text-xs font-medium hover:opacity-90"
              >
                Authorize PR Proposal
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
