"use client";

import { useEffect, useRef, useState } from "react";
import { Finding } from "@/lib/types";
import { describe, evidencePage } from "@/lib/format";

const DOT: Record<string, string> = {
  HIGH: "bg-high",
  MEDIUM: "bg-medium",
  LOW: "bg-low",
};

const ARROW = { up: "▲", down: "▼", flat: "–" } as const;

export default function FindingsTable({
  findings,
  onOpen,
}: {
  findings: Finding[];
  onOpen: (f: Finding) => void;
}) {
  const [cursor, setCursor] = useState(0);
  const rowRefs = useRef<(HTMLTableRowElement | null)[]>([]);

  useEffect(() => setCursor(0), [findings]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      const t = e.target as HTMLElement;
      if (t.tagName === "INPUT" || t.tagName === "TEXTAREA") return;
      if (e.key === "j") setCursor((c) => Math.min(c + 1, findings.length - 1));
      else if (e.key === "k") setCursor((c) => Math.max(c - 1, 0));
      else if (e.key === "Enter" && findings[cursor] && document.activeElement === document.body) {
        onOpen(findings[cursor]);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [findings, cursor, onOpen]);

  useEffect(() => {
    rowRefs.current[cursor]?.scrollIntoView({ block: "nearest" });
  }, [cursor]);

  return (
    <div className="overflow-x-auto rounded border border-rule bg-panel">
      <table className="w-full min-w-[720px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-rule text-left">
            <th className="col-head w-8 py-2.5 pl-4 font-medium" aria-label="Priority" />
            <th className="col-head py-2.5 pr-4 font-medium">Change</th>
            <th className="col-head py-2.5 pr-4 text-right font-medium">Previous</th>
            <th className="col-head py-2.5 pr-4 text-right font-medium">Current</th>
            <th className="col-head py-2.5 pr-4 text-right font-medium">Delta</th>
            <th className="col-head py-2.5 pr-4 font-medium">Source</th>
          </tr>
        </thead>
        <tbody>
          {findings.map((f, i) => {
            const d = describe(f);
            const hasEvidence = f.previous_evidence || f.current_evidence;
            return (
              <tr
                key={`${f.change_type}-${f.label}-${i}`}
                ref={(el) => {
                  rowRefs.current[i] = el;
                }}
                onClick={() => {
                  setCursor(i);
                  if (hasEvidence) onOpen(f);
                }}
                className={`group cursor-pointer border-b border-rule last:border-b-0 hover:bg-accent-soft/60 ${
                  cursor === i ? "bg-accent-soft/40 shadow-[inset_2px_0_0_#1F5C4D]" : ""
                }`}
              >
                <td className="py-3 pl-4 align-top">
                  <span
                    title={`${f.priority} priority`}
                    className={`mt-1.5 inline-block h-2 w-2 rounded-full ${DOT[f.priority]}`}
                  />
                  <span className="sr-only">{f.priority} priority</span>
                </td>
                <td className="max-w-md py-3 pr-4 align-top">
                  <div className="font-medium">{f.label}</div>
                  <div className="mt-0.5 text-xs text-muted">
                    {f.rule_triggered?.replace(/_/g, " ").replace(/>=/g, "≥")}
                  </div>
                  {f.explanation && <p className="mt-1.5 text-sm leading-snug text-muted">{f.explanation}</p>}
                </td>
                <td className="num py-3 pr-4 text-right align-top text-muted">{d.previous}</td>
                <td className="num py-3 pr-4 text-right align-top">{d.current}</td>
                <td
                  className={`num py-3 pr-4 text-right align-top font-medium ${
                    d.direction === "up" ? "text-up" : d.direction === "down" ? "text-down" : "text-muted"
                  }`}
                >
                  {d.delta ? (
                    <>
                      <span aria-hidden className="mr-1 text-[10px]">
                        {ARROW[d.direction ?? "flat"]}
                      </span>
                      {d.delta}
                    </>
                  ) : (
                    "—"
                  )}
                </td>
                <td className="py-3 pr-4 align-top">
                  {hasEvidence ? (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onOpen(f);
                      }}
                      className="num rounded border border-rule px-2 py-0.5 text-xs text-accent hover:border-accent"
                    >
                      {evidencePage(f)}
                    </button>
                  ) : (
                    <span className="text-xs text-muted">—</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
