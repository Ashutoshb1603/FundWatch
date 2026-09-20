"use client";

import { useEffect, useRef, useState } from "react";
import { Evidence, Finding } from "@/lib/types";
import { citation, describe } from "@/lib/format";

function Side({
  title,
  value,
  evidence,
  onCopy,
  copied,
}: {
  title: string;
  value: string;
  evidence?: Evidence;
  onCopy: () => void;
  copied: boolean;
}) {
  return (
    <div className="flex flex-col rounded border border-rule bg-panel p-4">
      <div className="col-head">{title}</div>
      <div className="num mt-2 text-2xl">{value}</div>

      {evidence ? (
        <>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted">
            <span className="num rounded border border-rule px-1.5 py-0.5">
              {evidence.page_number ? `Page ${evidence.page_number}` : "Page not located"}
            </span>
            <span className="capitalize">{evidence.confidence} confidence</span>
          </div>
          {evidence.raw_snippet ? (
            <blockquote className="num mt-3 whitespace-pre-wrap border-l-2 border-accent bg-accent-soft/50 px-3 py-2 text-xs leading-5">
              {evidence.raw_snippet}
            </blockquote>
          ) : (
            <p className="mt-3 text-xs text-muted">No source text was captured for this value.</p>
          )}
          <button onClick={onCopy} className="mt-3 self-start text-xs font-medium text-accent hover:underline">
            {copied ? "Copied" : "Copy citation"}
          </button>
        </>
      ) : (
        <p className="mt-3 text-xs text-muted">Not present in this factsheet.</p>
      )}
    </div>
  );
}

export default function EvidenceDrawer({
  finding,
  position,
  onPrev,
  onNext,
  onClose,
}: {
  finding: Finding | null;
  position: { index: number; total: number } | null;
  onPrev: () => void;
  onNext: () => void;
  onClose: () => void;
}) {
  const [copied, setCopied] = useState<"previous" | "current" | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const opener = useRef<HTMLElement | null>(null);
  const open = finding !== null;

  useEffect(() => {
    if (!open) return;
    opener.current = document.activeElement as HTMLElement | null;
    panelRef.current?.focus();
    return () => opener.current?.focus?.();
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
      else if (e.key === "ArrowLeft") onPrev();
      else if (e.key === "ArrowRight") onNext();
      else if (e.key === "Tab" && panelRef.current) {
        const els = panelRef.current.querySelectorAll<HTMLElement>("button, [href], input, [tabindex]:not([tabindex='-1'])");
        if (!els.length) return;
        const first = els[0];
        const last = els[els.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose, onPrev, onNext]);

  if (!finding) return null;
  const d = describe(finding);

  async function copy(side: "previous" | "current") {
    try {
      await navigator.clipboard.writeText(citation(finding as Finding, side));
      setCopied(side);
      setTimeout(() => setCopied(null), 1500);
    } catch {
      /* clipboard unavailable; ignore */
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-ink/30" onClick={onClose}>
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={`Evidence for ${finding.label}`}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
        className="fade-up h-full w-full max-w-3xl overflow-y-auto border-l border-rule bg-surface p-6 shadow-2xl outline-none sm:p-8"
      >
        <div className="flex items-center justify-between text-sm">
          <div className="col-head">Evidence</div>
          <div className="flex items-center gap-3 text-muted">
            {position && (
              <span className="num text-xs">
                {position.index + 1} / {position.total}
              </span>
            )}
            <button onClick={onPrev} disabled={!position || position.index === 0} aria-label="Previous finding" className="px-1 hover:text-ink disabled:opacity-30">
              ←
            </button>
            <button onClick={onNext} disabled={!position || position.index >= position.total - 1} aria-label="Next finding" className="px-1 hover:text-ink disabled:opacity-30">
              →
            </button>
            <button onClick={onClose} aria-label="Close" className="ml-2 px-1 hover:text-ink">
              ✕
            </button>
          </div>
        </div>

        <h3 className="mt-4 font-serif text-2xl leading-snug">{finding.label}</h3>
        <div className="mt-2 flex flex-wrap items-center gap-3 text-sm">
          <span className="capitalize text-muted">{finding.priority.toLowerCase()} priority</span>
          {d.delta && (
            <span className={`num font-medium ${d.direction === "down" ? "text-down" : "text-up"}`}>{d.delta}</span>
          )}
          {finding.rule_triggered && (
            <span className="text-xs text-muted">{finding.rule_triggered.replace(/_/g, " ").replace(/>=/g, "≥")}</span>
          )}
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2">
          <Side title="Previous factsheet" value={d.previous} evidence={finding.previous_evidence} onCopy={() => copy("previous")} copied={copied === "previous"} />
          <Side title="Current factsheet" value={d.current} evidence={finding.current_evidence} onCopy={() => copy("current")} copied={copied === "current"} />
        </div>

        {finding.explanation && (
          <p className="mt-6 border-t border-rule pt-5 text-sm leading-relaxed">{finding.explanation}</p>
        )}
        <p className="mt-4 text-xs text-muted">
          Values are read directly from the pages shown. Open the source PDF to confirm before acting on any finding.
          Use ← → to move between findings.
        </p>
      </div>
    </div>
  );
}
