"use client";

import { useMemo, useState } from "react";
import { Finding, Priority, ScanResult } from "@/lib/types";
import { CATEGORIES, PRIORITY_RANK, categoryOf, magnitude } from "@/lib/format";
import HeroBand from "./HeroBand";
import KeyMetrics from "./KeyMetrics";
import MoversChart from "./MoversChart";
import FilterRail, { SortKey } from "./FilterRail";
import FindingsTable from "./FindingsTable";
import EvidenceDrawer from "./EvidenceDrawer";
import AnalystBriefPanel from "./AnalystBriefPanel";
import AnalystChat from "./AnalystChat";
import StateNotice from "./StateNotice";

export default function Dashboard({ result, onStartOver }: { result: ScanResult; onStartOver: () => void }) {
  const [category, setCategory] = useState("all");
  const [priorities, setPriorities] = useState<Set<Priority>>(new Set(["HIGH", "MEDIUM", "LOW"]));
  const [sort, setSort] = useState<SortKey>("priority");
  const [openFinding, setOpenFinding] = useState<Finding | null>(null);
  const [dismissed, setDismissed] = useState(false);

  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const f of result.findings) c[categoryOf(f)] = (c[categoryOf(f)] ?? 0) + 1;
    return c;
  }, [result.findings]);

  const visible = useMemo(() => {
    const list = result.findings.filter(
      (f) => (category === "all" || categoryOf(f) === category) && priorities.has(f.priority)
    );
    return [...list].sort((a, b) =>
      sort === "priority"
        ? PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority] || magnitude(b) - magnitude(a)
        : magnitude(b) - magnitude(a)
    );
  }, [result.findings, category, priorities, sort]);

  function togglePriority(p: Priority) {
    setPriorities((prev) => {
      const next = new Set(prev);
      if (next.has(p)) next.delete(p);
      else next.add(p);
      return next;
    });
  }

  // Evidence navigation follows the visible table; a finding opened from elsewhere (KPI card, chart) stands alone.
  const evidenceList = openFinding && visible.includes(openFinding) ? visible : openFinding ? [openFinding] : [];
  const openIdx = openFinding ? evidenceList.indexOf(openFinding) : -1;

  const issues = result.validation?.issues ?? [];
  const extractionWarnings = [...(result.extraction.previous_warnings ?? []), ...(result.extraction.current_warnings ?? [])];
  const activeTitle = category === "all" ? "All changes" : CATEGORIES.find((c) => c.key === category)?.title;

  return (
    <div className="fade-up pb-24">
      <HeroBand result={result} onStartOver={onStartOver} />
      <div className="mx-auto max-w-6xl px-5 sm:px-8">
      <KeyMetrics findings={result.findings} onOpen={setOpenFinding} />

      {!dismissed && (issues.length > 0 || extractionWarnings.length > 0) && (
        <div className="mt-6">
          <StateNotice
            tone="warning"
            title="Check before relying on these results"
            action={{ label: "Dismiss", onClick: () => setDismissed(true) }}
          >
            <ul className="list-disc space-y-0.5 pl-5">
              {[...issues, ...extractionWarnings].map((m, i) => (
                <li key={i}>{m}</li>
              ))}
            </ul>
          </StateNotice>
        </div>
      )}

      {result.brief && (
        <div className="mt-6">
          <AnalystBriefPanel brief={result.brief} />
        </div>
      )}

      <div className="mt-10 grid gap-8 lg:grid-cols-[210px_1fr]">
        <FilterRail
          counts={counts}
          total={result.findings.length}
          category={category}
          onCategory={setCategory}
          priorities={priorities}
          onTogglePriority={togglePriority}
          sort={sort}
          onSort={setSort}
        />

        <div className="min-w-0">
          <MoversChart findings={result.findings} onOpen={setOpenFinding} />

          <div className="mb-3 mt-10 flex items-baseline justify-between">
            <h2 className="font-serif text-xl font-semibold">{activeTitle}</h2>
            <span className="num text-xs text-muted">{visible.length} shown</span>
          </div>

          {visible.length ? (
            <FindingsTable findings={visible} onOpen={setOpenFinding} />
          ) : (
            <div className="rounded border border-dashed border-rule bg-panel px-6 py-12 text-center">
              <p className="font-medium">No material changes here</p>
              <p className="mt-1 text-sm text-muted">
                {result.findings.length
                  ? "Nothing matches the current filters. Try widening the priority filter."
                  : "Nothing crossed the materiality thresholds between these two factsheets."}
              </p>
            </div>
          )}

          <div className="mt-10">
            <AnalystChat scanId={result.scan_id} />
          </div>
        </div>
      </div>

      <EvidenceDrawer
        finding={openFinding}
        position={openFinding ? { index: openIdx, total: evidenceList.length } : null}
        onPrev={() => openIdx > 0 && setOpenFinding(evidenceList[openIdx - 1])}
        onNext={() => openIdx < evidenceList.length - 1 && setOpenFinding(evidenceList[openIdx + 1])}
        onClose={() => setOpenFinding(null)}
      />
      </div>
    </div>
  );
}
