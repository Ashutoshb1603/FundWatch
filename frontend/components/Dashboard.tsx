"use client";

import { useMemo, useState } from "react";
import { Finding, ScanResult } from "@/lib/types";
import ChangeCard from "./ChangeCard";
import EvidenceDrawer from "./EvidenceDrawer";
import AnalystBriefPanel from "./AnalystBriefPanel";
import AnalystChat from "./AnalystChat";

const SECTIONS: { key: string; title: string; types: string[] }[] = [
  {
    key: "portfolio",
    title: "Portfolio",
    types: ["holding_new", "holding_exited", "holding_weight_change", "top10_entry", "top10_exit"],
  },
  { key: "sectors", title: "Sectors", types: ["sector_weight_change"] },
  { key: "fund", title: "Fund-level metrics", types: ["aum_change", "expense_ratio_change"] },
  { key: "risk", title: "Risk / management", types: ["riskometer_change", "fund_manager_change"] },
];

export default function Dashboard({ result, onStartOver }: { result: ScanResult; onStartOver: () => void }) {
  const [activeEvidence, setActiveEvidence] = useState<Finding | null>(null);
  const [tab, setTab] = useState<string>("portfolio");

  const grouped = useMemo(() => {
    const map: Record<string, Finding[]> = {};
    for (const s of SECTIONS) map[s.key] = [];
    for (const f of result.findings) {
      const section = SECTIONS.find((s) => s.types.includes(f.change_type));
      if (section) map[section.key].push(f);
    }
    return map;
  }, [result.findings]);

  return (
    <div className="mx-auto max-w-5xl pb-20">
      <div className="flex items-start justify-between">
        <div>
          <div className="evidence-tag text-xs uppercase tracking-widest text-gold">FundWatch</div>
          <h1 className="mt-2 font-serif text-3xl text-paper">
            {result.fund.scheme_name || "Fund comparison"}
          </h1>
          <div className="mt-1 font-mono text-sm text-slate-400">
            {result.fund.previous_period || "Previous period"} → {result.fund.current_period || "Current period"}
          </div>
        </div>
        <div className="text-right">
          <div className="font-mono text-3xl text-gold">{result.material_change_count}</div>
          <div className="evidence-tag text-xs uppercase tracking-widest text-slate-500">Material Changes</div>
        </div>
      </div>

      {result.validation && result.validation.issues.length > 0 && (
        <div className="mt-6 rounded-sm border border-gold/40 bg-gold/5 px-4 py-3 text-sm text-gold">
          {result.validation.issues.map((issue, i) => (
            <div key={i}>{issue}</div>
          ))}
        </div>
      )}

      <div className="mt-8 flex flex-wrap gap-2 border-b border-ink-border pb-1">
        {SECTIONS.map((s) => (
          <button
            key={s.key}
            onClick={() => setTab(s.key)}
            className={`evidence-tag rounded-sm px-3 py-2 text-xs uppercase tracking-widest ${
              tab === s.key ? "border-b-2 border-gold text-paper" : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {s.title} ({grouped[s.key]?.length ?? 0})
          </button>
        ))}
        <button
          onClick={() => setTab("brief")}
          className={`evidence-tag rounded-sm px-3 py-2 text-xs uppercase tracking-widest ${
            tab === "brief" ? "border-b-2 border-gold text-paper" : "text-slate-500 hover:text-slate-300"
          }`}
        >
          Analyst Brief
        </button>
      </div>

      <div className="mt-6">
        {tab !== "brief" ? (
          grouped[tab]?.length ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {grouped[tab].map((f, i) => (
                <ChangeCard key={i} finding={f} onViewEvidence={setActiveEvidence} />
              ))}
            </div>
          ) : (
            <div className="rounded-sm border border-dashed border-ink-border p-8 text-center text-sm text-slate-500">
              No material changes detected in this category.
            </div>
          )
        ) : result.brief ? (
          <div className="space-y-6">
            <AnalystBriefPanel brief={result.brief} />
            <AnalystChat scanId={result.scan_id} />
          </div>
        ) : (
          <div className="text-sm text-slate-500">Brief not available.</div>
        )}
      </div>

      <button
        onClick={onStartOver}
        className="mt-10 evidence-tag text-xs uppercase tracking-widest text-slate-500 hover:text-gold"
      >
        ← Analyze another pair
      </button>

      <EvidenceDrawer finding={activeEvidence} onClose={() => setActiveEvidence(null)} />
    </div>
  );
}
