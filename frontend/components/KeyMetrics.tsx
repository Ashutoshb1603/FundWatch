"use client";

import { Finding } from "@/lib/types";
import { describe } from "@/lib/format";

const METRICS: { type: string; title: string; unchanged: string }[] = [
  { type: "aum_change", title: "Assets under management", unchanged: "Within threshold" },
  { type: "expense_ratio_change", title: "Expense ratio", unchanged: "Unchanged" },
  { type: "riskometer_change", title: "Riskometer", unchanged: "Unchanged" },
  { type: "fund_manager_change", title: "Fund manager", unchanged: "Unchanged" },
];

export default function KeyMetrics({ findings, onOpen }: { findings: Finding[]; onOpen: (f: Finding) => void }) {
  return (
    <section aria-label="Key fund metrics" className="relative z-10 -mt-16 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {METRICS.map((m) => {
        const f = findings.find((x) => x.change_type === m.type);
        const d = f ? describe(f) : null;
        const hasEvidence = !!(f && (f.previous_evidence || f.current_evidence));
        const Tag = f && hasEvidence ? "button" : "div";
        return (
          <Tag
            key={m.type}
            onClick={f && hasEvidence ? () => onOpen(f) : undefined}
            className={`rounded border border-rule bg-panel p-5 text-left shadow-[0_14px_30px_-20px_rgba(27,27,24,0.4)] ${
              f && hasEvidence ? "hover:border-accent" : ""
            }`}
          >
            <div className="col-head">{m.title}</div>
            {f && d ? (
              <>
                <div className="num mt-3 truncate text-2xl font-medium">{d.current}</div>
                <div className="mt-2 flex items-center justify-between gap-2 text-sm">
                  <span className="num truncate text-muted">was {d.previous}</span>
                  {d.delta && (
                    <span
                      className={`num shrink-0 rounded px-1.5 py-0.5 text-xs font-medium ${
                        d.direction === "down" ? "bg-down/10 text-down" : "bg-up/10 text-up"
                      }`}
                    >
                      {d.direction === "down" ? "▼" : "▲"} {d.delta}
                    </span>
                  )}
                </div>
              </>
            ) : (
              <div className="mt-3 flex items-center gap-2 text-muted">
                <span aria-hidden className="flex h-5 w-5 items-center justify-center rounded-full bg-accent-soft text-[11px] text-accent">
                  ✓
                </span>
                {m.unchanged}
              </div>
            )}
          </Tag>
        );
      })}
    </section>
  );
}
