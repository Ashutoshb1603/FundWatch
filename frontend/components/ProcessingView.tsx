"use client";

import { useEffect, useRef, useState } from "react";
import DocPage from "./DocPage";
import Logo from "./Logo";

const STEPS: { key: string; label: string; detail: string }[] = [
  { key: "extract_text_tables", label: "Extracting text and tables", detail: "Reading each page of both PDFs" },
  { key: "validate_extraction", label: "Checking extraction quality", detail: "Scoring how complete the read was" },
  { key: "normalize_factsheets", label: "Structuring the data", detail: "Holdings, sectors, AUM, costs, risk level" },
  { key: "validate_fund_identity", label: "Confirming same scheme", detail: "Matching fund and reporting periods" },
  { key: "compare_data", label: "Comparing periods", detail: "Deterministic diff, no language model involved" },
  { key: "detect_material_changes_and_attach_evidence", label: "Flagging material changes", detail: "Applying thresholds and linking source pages" },
  { key: "generate_explanations", label: "Writing explanations", detail: "Amazon Bedrock, from the computed findings only" },
  { key: "generate_analyst_brief", label: "Assembling the brief", detail: "Ranking findings for review" },
];

export const STEP_KEYS = STEPS.map((s) => s.key);

export default function ProcessingView({
  activeStep,
  previousName,
  currentName,
}: {
  activeStep: string | null;
  previousName?: string;
  currentName?: string;
}) {
  const activeIdx = activeStep ? STEPS.findIndex((s) => s.key === activeStep) : -1;
  const startedAt = useRef<Record<string, number>>({});
  const [durations, setDurations] = useState<Record<string, number>>({});
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 300);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (!activeStep) return;
    const ts = Date.now();
    startedAt.current[activeStep] ??= ts;
    setDurations((d) => {
      const next = { ...d };
      for (const s of STEPS) {
        const started = startedAt.current[s.key];
        if (started && s.key !== activeStep && next[s.key] === undefined) next[s.key] = ts - started;
      }
      return next;
    });
  }, [activeStep]);

  // Page "load" progress: completed steps plus an easing creep inside the current one,
  // so the pages keep filling in even while a single slow step is running.
  const inStep = activeStep && startedAt.current[activeStep] ? (now - startedAt.current[activeStep]) / 1000 : 0;
  const creep = 1 - Math.exp(-inStep / 5);
  const base = activeIdx === -1 ? 0 : activeIdx + creep * 0.9;
  const progress = Math.min(0.97, base / STEPS.length + 0.04);

  const secs = (ms: number) => `${(ms / 1000).toFixed(1)}s`;

  return (
    <div className="fade-up mx-auto max-w-6xl px-5 pt-2 sm:px-8">
      <Logo />

      <div className="mt-10 grid items-center gap-12 lg:grid-cols-[1fr_1.15fr]">
        <div>
          <h2 className="font-serif text-4xl leading-tight tracking-tight">Reading the disclosures</h2>
          <p className="mt-3 text-lg text-muted">
            This usually takes under a minute. Both factsheets are read in parallel and checked page by page.
          </p>

          <ol className="mt-8 border-t border-rule" aria-live="polite">
            {STEPS.map((s, i) => {
              const done = durations[s.key] !== undefined || (activeIdx !== -1 && i < activeIdx);
              const active = i === activeIdx;
              return (
                <li key={s.key} className="flex items-start gap-4 border-b border-rule py-3">
                  <span
                    aria-hidden
                    className={`num mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] ${
                      done ? "bg-accent text-white" : active ? "border-2 border-accent" : "border border-rule"
                    } ${active ? "animate-pulse" : ""}`}
                  >
                    {done ? "✓" : ""}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className={`text-[15px] ${active ? "font-medium" : done ? "" : "text-muted"}`}>{s.label}</div>
                    {active && <div className="mt-0.5 text-sm text-muted">{s.detail}</div>}
                  </div>
                  <span className="num text-xs text-muted">
                    {active && startedAt.current[s.key]
                      ? secs(now - startedAt.current[s.key])
                      : durations[s.key] !== undefined
                      ? secs(durations[s.key])
                      : ""}
                  </span>
                </li>
              );
            })}
          </ol>
        </div>

        <div className="relative mx-auto flex w-full max-w-[560px] items-center justify-center gap-6 py-6">
          <figure className="w-1/2 -rotate-2">
            <DocPage progress={progress} scanning />
            <figcaption className="mt-3 truncate text-center text-sm text-muted">
              <span className="num mr-1.5 text-xs">A</span>
              {previousName || "Earlier factsheet"}
            </figcaption>
          </figure>
          <span aria-hidden className="text-2xl text-muted">
            →
          </span>
          <figure className="w-1/2 rotate-2">
            <DocPage progress={Math.max(0, progress - 0.12)} scanning />
            <figcaption className="mt-3 truncate text-center text-sm text-muted">
              <span className="num mr-1.5 text-xs">B</span>
              {currentName || "Later factsheet"}
            </figcaption>
          </figure>
        </div>
      </div>
    </div>
  );
}
