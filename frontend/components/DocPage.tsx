"use client";

/**
 * A stylised factsheet page drawn in CSS: title, key figures, a holdings table
 * with one flagged row, and a small bar chart. `progress` (0..1) controls how
 * much of the page has "loaded": unloaded blocks shimmer as skeletons and fill
 * in one by one. Omit it for a fully rendered page.
 */

const ROW_WIDTHS = [86, 70, 78, 62, 74, 56];
const BARS = [46, 68, 38, 82, 55];

const BLOCKS = 6;

export default function DocPage({
  progress = 1,
  scanning = false,
  attached = false,
  className = "",
}: {
  progress?: number;
  scanning?: boolean;
  attached?: boolean;
  className?: string;
}) {
  const on = (block: number) => progress > block / BLOCKS;

  return (
    <div
      aria-hidden
      className={`relative aspect-[3/4] overflow-hidden rounded-sm border bg-panel p-[7%] shadow-[0_18px_40px_-18px_rgba(27,27,24,0.35)] ${
        attached ? "border-accent" : "border-rule"
      } ${className}`}
    >
      {/* 0: title */}
      <div className="flex items-center gap-[4%]">
        <div className={`doc-block h-[13px] w-[13px] shrink-0 rounded-sm ${on(0) ? "bg-accent" : "sk"}`} />
        <div className={`doc-block h-[9px] w-[58%] rounded-sm ${on(0) ? "bg-ink/80" : "sk"}`} />
      </div>

      {/* 1: meta lines */}
      <div className="mt-[6%] space-y-[3%]">
        <div className={`doc-block h-[5px] w-[82%] rounded-sm ${on(1) ? "bg-ink/25" : "sk"}`} />
        <div className={`doc-block h-[5px] w-[64%] rounded-sm ${on(1) ? "bg-ink/25" : "sk"}`} />
      </div>

      {/* 2: key figures */}
      <div className="mt-[7%] grid grid-cols-3 gap-[4%]">
        {[0, 1, 2].map((i) => (
          <div key={i} className={`doc-block rounded-sm border p-[8%] ${on(2) ? "border-rule" : "border-transparent"}`}>
            <div className={`doc-block h-[4px] w-[60%] rounded-sm ${on(2) ? "bg-ink/25" : "sk"}`} />
            <div className={`doc-block mt-[12%] h-[8px] w-[85%] rounded-sm ${on(2) ? "bg-ink/75" : "sk"}`} />
          </div>
        ))}
      </div>

      {/* 3: holdings table, one row flagged */}
      <div className="mt-[7%] space-y-[3.5%]">
        {ROW_WIDTHS.map((w, i) => {
          const flagged = i === 2 && on(3);
          return (
            <div
              key={i}
              className={`doc-block flex items-center justify-between gap-[6%] rounded-sm px-[2%] py-[1.6%] ${
                flagged ? "bg-medium/15" : ""
              }`}
              style={{ transitionDelay: on(3) ? `${i * 70}ms` : "0ms" }}
            >
              <div
                className={`doc-block h-[5px] rounded-sm ${on(3) ? "bg-ink/40" : "sk"}`}
                style={{ width: `${w}%` }}
              />
              <div className={`doc-block h-[5px] w-[14%] rounded-sm ${on(3) ? (flagged ? "bg-medium" : "bg-ink/60") : "sk"}`} />
            </div>
          );
        })}
      </div>

      {/* 4: bar chart */}
      <div className="mt-[7%] flex h-[16%] items-end gap-[4%]">
        {BARS.map((h, i) => (
          <div
            key={i}
            className={`doc-block w-full rounded-t-sm ${on(4) ? (i === 3 ? "bg-down" : "bg-accent/80") : "sk"}`}
            style={{ height: on(4) ? `${h}%` : "30%", transitionDelay: on(4) ? `${i * 60}ms` : "0ms" }}
          />
        ))}
      </div>

      {/* 5: footer */}
      <div className="mt-[6%] space-y-[3%]">
        <div className={`doc-block h-[4px] w-full rounded-sm ${on(5) ? "bg-ink/15" : "sk"}`} />
        <div className={`doc-block h-[4px] w-[70%] rounded-sm ${on(5) ? "bg-ink/15" : "sk"}`} />
      </div>

      {scanning && <div className="scan-line" />}

      {attached && (
        <div className="absolute right-[6%] top-[5%] flex h-[18px] w-[18px] items-center justify-center rounded-full bg-accent text-[10px] text-white">
          ✓
        </div>
      )}
    </div>
  );
}
