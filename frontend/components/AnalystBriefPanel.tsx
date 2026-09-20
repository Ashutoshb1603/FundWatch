"use client";

import { useState } from "react";
import { Brief } from "@/lib/types";
import { describe } from "@/lib/format";

export default function AnalystBriefPanel({ brief }: { brief: Brief }) {
  const [open, setOpen] = useState(true);

  return (
    <section className="rounded border border-rule bg-panel">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="flex w-full items-center justify-between px-5 py-3.5 text-left"
      >
        <span className="font-serif text-lg font-semibold">Analyst brief</span>
        <span className="text-xs text-muted">{open ? "Hide" : "Show"}</span>
      </button>

      {open && (
        <div className="grid gap-8 border-t border-rule px-5 py-5 md:grid-cols-[1.4fr_1fr]">
          <div>
            {brief.narrative_available && brief.narrative ? (
              <p className="whitespace-pre-line font-serif text-[17px] leading-relaxed">{brief.narrative}</p>
            ) : (
              <p className="text-sm leading-relaxed text-muted">
                Written summary is unavailable because Amazon Bedrock could not be reached. Every figure in the
                table is calculated separately and is unaffected.
              </p>
            )}
          </div>

          <div>
            <div className="col-head mb-2">Top changes</div>
            <ol className="divide-y divide-rule">
              {brief.key_changes.slice(0, 5).map((f, i) => {
                const d = describe(f);
                return (
                  <li key={i} className="flex items-baseline justify-between gap-4 py-2 text-sm">
                    <span>
                      <span className="num mr-2 text-muted">{i + 1}</span>
                      {f.label}
                    </span>
                    {d.delta && (
                      <span className={`num shrink-0 ${d.direction === "down" ? "text-down" : "text-up"}`}>
                        {d.delta}
                      </span>
                    )}
                  </li>
                );
              })}
            </ol>
          </div>

          <p className="border-t border-rule pt-4 text-xs leading-relaxed text-muted md:col-span-2">{brief.caveat}</p>
        </div>
      )}
    </section>
  );
}
