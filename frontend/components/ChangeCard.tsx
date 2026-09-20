"use client";

import { Finding } from "@/lib/types";

const PRIORITY_STYLE: Record<string, string> = {
  HIGH: "text-rust border-rust/50",
  MEDIUM: "text-gold border-gold/50",
  LOW: "text-slate-400 border-ink-border",
};

function formatValue(v: number | string | null, isPercent: boolean) {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return isPercent ? `${v.toFixed(2)}%` : v.toLocaleString("en-IN");
  return v;
}

export default function ChangeCard({
  finding,
  onViewEvidence,
}: {
  finding: Finding;
  onViewEvidence: (f: Finding) => void;
}) {
  const isPercentMetric = ![
    "riskometer_change",
    "fund_manager_change",
    "holding_new",
    "holding_exited",
    "top10_entry",
    "top10_exit",
  ].includes(finding.change_type) || finding.change_type === "holding_new" || finding.change_type === "holding_exited";

  const hasEvidence = finding.previous_evidence || finding.current_evidence;

  return (
    <div className="rounded-sm border border-ink-border bg-ink-light/60 p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="font-serif text-lg text-paper">{finding.label}</div>
          <div className="evidence-tag mt-1 text-xs text-slate-500">
            {finding.rule_triggered?.replace(/_/g, " ")}
          </div>
        </div>
        <span className={`evidence-tag rounded-sm border px-2 py-0.5 text-[10px] uppercase tracking-widest ${PRIORITY_STYLE[finding.priority]}`}>
          {finding.priority}
        </span>
      </div>

      <div className="mt-4 flex items-center gap-3 font-mono text-sm">
        <span className="text-slate-400">{formatValue(finding.previous_value, isPercentMetric && typeof finding.previous_value === "number")}</span>
        <span className="text-slate-600">→</span>
        <span className="text-paper">{formatValue(finding.current_value, isPercentMetric && typeof finding.current_value === "number")}</span>
        {finding.percentage_point_difference !== null && (
          <span className={finding.percentage_point_difference >= 0 ? "text-teal" : "text-rust"}>
            {finding.percentage_point_difference >= 0 ? "+" : ""}
            {finding.percentage_point_difference.toFixed(2)}
            {finding.change_type === "expense_ratio_change" ? " bps" : finding.change_type === "aum_change" ? "%" : " pp"}
          </span>
        )}
      </div>

      {finding.explanation && (
        <p className="mt-3 text-sm leading-relaxed text-slate-300">{finding.explanation}</p>
      )}

      {hasEvidence && (
        <button
          onClick={() => onViewEvidence(finding)}
          className="mt-4 evidence-tag text-xs uppercase tracking-widest text-gold hover:underline"
        >
          View Evidence
        </button>
      )}
    </div>
  );
}
