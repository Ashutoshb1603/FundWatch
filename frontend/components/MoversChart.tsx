"use client";

import { useMemo, useState } from "react";
import { Finding } from "@/lib/types";
import { describe, magnitude } from "@/lib/format";

type Mode = "holdings" | "sectors";

const MODES: { key: Mode; title: string; types: string[] }[] = [
  { key: "holdings", title: "Holdings", types: ["holding_weight_change", "holding_new", "holding_exited"] },
  { key: "sectors", title: "Sectors", types: ["sector_weight_change"] },
];

const MAX_ROWS = 8;

export default function MoversChart({ findings, onOpen }: { findings: Finding[]; onOpen: (f: Finding) => void }) {
  const holdings = useMemo(() => rowsFor(findings, "holdings"), [findings]);
  const sectors = useMemo(() => rowsFor(findings, "sectors"), [findings]);
  const [mode, setMode] = useState<Mode>(holdings.length || !sectors.length ? "holdings" : "sectors");
  const [hover, setHover] = useState<Finding | null>(null);

  const rows = mode === "holdings" ? holdings : sectors;
  const max = Math.max(...rows.map((r) => magnitude(r)), 0.01);

  if (!holdings.length && !sectors.length) return null;

  const readout = hover ? describe(hover) : null;

  return (
    <section className="rounded border border-rule bg-panel">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-rule px-5 py-4">
        <div>
          <h2 className="font-serif text-xl font-semibold">Where the portfolio moved</h2>
          <p className="mt-0.5 text-sm text-muted">Change in portfolio weight, in percentage points.</p>
        </div>
        <div className="inline-flex rounded border border-rule bg-surface p-0.5 text-sm" role="tablist">
          {MODES.map((m) => (
            <button
              key={m.key}
              role="tab"
              aria-selected={mode === m.key}
              onClick={() => {
                setMode(m.key);
                setHover(null);
              }}
              className={`rounded-sm px-3 py-1 ${mode === m.key ? "bg-accent text-white" : "text-muted hover:text-ink"}`}
            >
              {m.title}
            </button>
          ))}
        </div>
      </div>

      <div className="px-5 pb-4 pt-3">
        <div className="flex min-h-[28px] flex-wrap items-center justify-between gap-3 text-sm">
          <div className="flex items-center gap-4 text-muted">
            <span className="inline-flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm bg-down" /> Reduced
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm bg-up" /> Increased
            </span>
          </div>
          <div className="num text-xs text-muted" aria-live="polite">
            {hover && readout ? (
              <>
                <span className="font-sans font-medium text-ink">{hover.label}</span> &nbsp;{readout.previous} →{" "}
                {readout.current} &nbsp;
                <span className={readout.direction === "down" ? "text-down" : "text-up"}>{readout.delta}</span>
              </>
            ) : (
              "Hover a bar for values, click to open the evidence"
            )}
          </div>
        </div>

        {rows.length ? (
          <ul className="mt-2">
            {rows.map((f, i) => {
              const d = f.percentage_point_difference ?? 0;
              const pct = (Math.abs(d) / max) * 40; // leave room for the value label
              const up = d >= 0;
              return (
                <li key={`${f.label}-${i}`}>
                  <button
                    onClick={() => onOpen(f)}
                    onMouseEnter={() => setHover(f)}
                    onMouseLeave={() => setHover(null)}
                    onFocus={() => setHover(f)}
                    onBlur={() => setHover(null)}
                    aria-label={`${f.label}, ${describe(f).delta}`}
                    className="grid w-full grid-cols-[minmax(0,38%)_1fr] items-center gap-3 rounded py-1.5 text-left hover:bg-accent-soft/50"
                  >
                    <span className="truncate pl-1 text-sm">{f.label}</span>
                    <span className="relative block h-[22px]">
                      <span className="absolute bottom-0 left-1/2 top-0 w-px bg-rule" />
                      <span
                        className={`absolute top-1/2 h-[10px] -translate-y-1/2 ${
                          up ? "left-1/2 rounded-r-[4px] bg-up" : "right-1/2 rounded-l-[4px] bg-down"
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                      <span
                        className={`num absolute top-1/2 -translate-y-1/2 whitespace-nowrap text-xs ${
                          up ? "text-up" : "text-down"
                        }`}
                        style={up ? { left: `calc(50% + ${pct}% + 6px)` } : { right: `calc(50% + ${pct}% + 6px)` }}
                      >
                        {describe(f).delta}
                      </span>
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="py-8 text-center text-sm text-muted">No material {mode} moves to chart.</p>
        )}
      </div>
    </section>
  );
}

function rowsFor(findings: Finding[], mode: Mode): Finding[] {
  const types = MODES.find((m) => m.key === mode)!.types;
  return findings
    .filter((f) => types.includes(f.change_type) && f.percentage_point_difference !== null)
    .sort((a, b) => magnitude(b) - magnitude(a))
    .slice(0, MAX_ROWS);
}
