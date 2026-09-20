"use client";

import { ScanResult } from "@/lib/types";
import Logo from "./Logo";
import DocPage from "./DocPage";

function Conf({ label, value }: { label: string; value: string | null }) {
  const v = (value || "unknown").toLowerCase();
  const tone = v === "high" ? "bg-[#6FCF97]" : v === "medium" ? "bg-gold" : "bg-white/50";
  return (
    <span className="inline-flex items-center gap-2 text-sm text-white/75">
      <span className={`h-2 w-2 rounded-full ${tone}`} />
      {label} <span className="capitalize text-white">{v}</span>
    </span>
  );
}

export default function HeroBand({ result, onStartOver }: { result: ScanResult; onStartOver: () => void }) {
  const counts = { HIGH: 0, MEDIUM: 0, LOW: 0 };
  for (const f of result.findings) counts[f.priority] += 1;

  return (
    <header
      className="relative overflow-hidden bg-accent-deep text-white"
      style={{
        backgroundImage:
          "repeating-linear-gradient(0deg, rgba(255,255,255,0.045) 0 1px, transparent 1px 34px), repeating-linear-gradient(90deg, rgba(255,255,255,0.03) 0 1px, transparent 1px 34px)",
      }}
    >
      {/* Document motif, cropped by the band edge */}
      <div aria-hidden className="pointer-events-none absolute -bottom-24 right-4 hidden w-[520px] xl:right-24 xl:block">
        <div className="float-b absolute right-0 top-0 w-[210px] opacity-95">
          <DocPage />
        </div>
        <div className="float-a absolute right-[200px] top-8 w-[220px] opacity-95">
          <DocPage />
        </div>
      </div>

      <div className="relative mx-auto max-w-6xl px-5 pb-28 pt-7 sm:px-8">
        <div className="flex items-center justify-between">
          <Logo tone="light" />
          <button
            onClick={onStartOver}
            className="rounded border border-white/30 px-3.5 py-1.5 text-sm text-white hover:bg-white/10"
          >
            ← New comparison
          </button>
        </div>

        <div className="mt-12 max-w-2xl">
          <div className="flex flex-wrap items-center gap-2.5 text-sm">
            {result.fund.amc && (
              <span className="rounded-full border border-white/25 px-3 py-0.5 text-white/85">{result.fund.amc}</span>
            )}
            <span className="num rounded-full bg-white/10 px-3 py-0.5">
              {result.fund.previous_period || "Previous"} → {result.fund.current_period || "Current"}
            </span>
          </div>
          <h1 className="mt-4 font-serif text-4xl leading-[1.1] tracking-tight sm:text-5xl">
            {result.fund.scheme_name || "Fund comparison"}
          </h1>
        </div>

        <dl className="mt-9 flex flex-wrap items-end gap-x-10 gap-y-5">
          <div>
            <dt className="text-sm text-white/70">Material changes</dt>
            <dd className="num mt-0.5 text-5xl font-medium leading-none">{result.material_change_count}</dd>
          </div>
          {(
            [
              ["High", counts.HIGH, "bg-[#E57C5F]"],
              ["Medium", counts.MEDIUM, "bg-gold"],
              ["Low", counts.LOW, "bg-white/45"],
            ] as const
          ).map(([label, n, dot]) => (
            <div key={label}>
              <dt className="flex items-center gap-2 text-sm text-white/70">
                <span className={`h-2 w-2 rounded-full ${dot}`} />
                {label}
              </dt>
              <dd className="num mt-0.5 text-3xl leading-none">{n}</dd>
            </div>
          ))}
        </dl>

        <div className="mt-7 flex flex-wrap gap-x-6 gap-y-1.5 border-t border-white/15 pt-4">
          <Conf label="Earlier extraction" value={result.extraction.previous_confidence} />
          <Conf label="Later extraction" value={result.extraction.current_confidence} />
        </div>
      </div>
    </header>
  );
}
