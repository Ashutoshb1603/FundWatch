"use client";

import { Brief } from "@/lib/types";

export default function AnalystBriefPanel({ brief }: { brief: Brief }) {
  return (
    <div className="rounded-sm border border-gold/30 bg-ink-light/60 p-6">
      <div className="evidence-tag text-xs uppercase tracking-widest text-gold">Monthly Analyst Brief</div>
      <h3 className="mt-2 font-serif text-2xl text-paper">
        {brief.scheme_name || "Fund"}
      </h3>
      <div className="mt-1 font-mono text-sm text-slate-400">
        {brief.previous_period} → {brief.current_period}
      </div>

      {brief.narrative_available && brief.narrative ? (
        <p className="mt-5 whitespace-pre-line text-sm leading-relaxed text-slate-200">{brief.narrative}</p>
      ) : (
        <p className="mt-5 text-sm text-slate-400">
          Narrative explanation is unavailable right now (Amazon Bedrock could not be reached).
          The ranked findings below are unaffected — they&rsquo;re calculated independently of Bedrock.
        </p>
      )}

      <ol className="mt-6 space-y-2">
        {brief.key_changes.map((f, i) => (
          <li key={i} className="flex items-start gap-3 font-mono text-sm text-slate-300">
            <span className="text-gold">{i + 1}.</span>
            <span>
              {f.label}{" "}
              {f.percentage_point_difference !== null && (
                <span className={f.percentage_point_difference >= 0 ? "text-teal" : "text-rust"}>
                  {f.percentage_point_difference >= 0 ? "↑" : "↓"} {Math.abs(f.percentage_point_difference).toFixed(2)}
                  {f.change_type === "expense_ratio_change" ? " bps" : " pp"}
                </span>
              )}
            </span>
          </li>
        ))}
      </ol>

      <p className="mt-6 border-t border-ink-border pt-4 text-xs text-slate-500">{brief.caveat}</p>
    </div>
  );
}
