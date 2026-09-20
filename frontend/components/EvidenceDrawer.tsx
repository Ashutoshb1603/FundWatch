"use client";

import { Finding } from "@/lib/types";

export default function EvidenceDrawer({ finding, onClose }: { finding: Finding | null; onClose: () => void }) {
  if (!finding) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60" onClick={onClose}>
      <div
        className="h-full w-full max-w-md overflow-y-auto border-l border-ink-border bg-ink p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <div className="evidence-tag text-xs uppercase tracking-widest text-gold">Evidence</div>
          <button onClick={onClose} className="text-slate-400 hover:text-paper">
            ✕
          </button>
        </div>
        <h3 className="mt-3 font-serif text-2xl text-paper">{finding.label}</h3>

        <div className="mt-6 space-y-4">
          {finding.previous_evidence && (
            <div className="rounded-sm border border-ink-border p-4">
              <div className="evidence-tag text-xs uppercase tracking-widest text-slate-500">
                Previous factsheet
              </div>
              <div className="mt-2 font-mono text-sm text-paper">
                {finding.previous_evidence.page_number
                  ? `Page ${finding.previous_evidence.page_number}`
                  : "Page not located"}
              </div>
              <div className="mt-1 text-xs text-slate-500">
                Extraction confidence: {finding.previous_evidence.confidence}
              </div>
              <div className="mt-3 font-mono text-lg text-slate-300">
                {String(finding.previous_value ?? "—")}
              </div>
              {finding.previous_evidence.raw_snippet && (
                <div className="mt-3 rounded-sm bg-ink-light p-3 text-xs leading-5 text-slate-400">
                  {finding.previous_evidence.raw_snippet}
                </div>
              )}
            </div>
          )}
          {finding.current_evidence && (
            <div className="rounded-sm border border-ink-border p-4">
              <div className="evidence-tag text-xs uppercase tracking-widest text-slate-500">
                Current factsheet
              </div>
              <div className="mt-2 font-mono text-sm text-paper">
                {finding.current_evidence.page_number
                  ? `Page ${finding.current_evidence.page_number}`
                  : "Page not located"}
              </div>
              <div className="mt-1 text-xs text-slate-500">
                Extraction confidence: {finding.current_evidence.confidence}
              </div>
              <div className="mt-3 font-mono text-lg text-paper">
                {String(finding.current_value ?? "—")}
              </div>
              {finding.current_evidence.raw_snippet && (
                <div className="mt-3 rounded-sm bg-ink-light p-3 text-xs leading-5 text-slate-400">
                  {finding.current_evidence.raw_snippet}
                </div>
              )}
            </div>
          )}
        </div>

        <p className="mt-6 text-xs text-slate-500">
          This panel shows the exact page each value was read from, so you can verify the
          finding against the source document yourself.
        </p>
      </div>
    </div>
  );
}
