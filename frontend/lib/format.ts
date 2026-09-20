import { Finding, Priority } from "./types";

export const CATEGORIES: { key: string; title: string; types: string[] }[] = [
  {
    key: "portfolio",
    title: "Portfolio",
    types: ["holding_new", "holding_exited", "holding_weight_change", "top10_entry", "top10_exit"],
  },
  { key: "sectors", title: "Sectors", types: ["sector_weight_change"] },
  { key: "fund", title: "Fund metrics", types: ["aum_change", "expense_ratio_change"] },
  { key: "risk", title: "Risk & management", types: ["riskometer_change", "fund_manager_change"] },
];

export const PRIORITY_RANK: Record<Priority, number> = { HIGH: 0, MEDIUM: 1, LOW: 2 };

export function categoryOf(f: Finding): string {
  return CATEGORIES.find((c) => c.types.includes(f.change_type))?.key ?? "other";
}

type Unit = "pct" | "crore" | "text";

function unitOf(f: Finding): Unit {
  switch (f.change_type) {
    case "aum_change":
      return "crore";
    case "riskometer_change":
    case "fund_manager_change":
      return "text";
    default:
      return "pct";
  }
}

function fmtValue(v: number | string | null, unit: Unit): string {
  if (v === null || v === undefined || v === "") return "—";
  if (typeof v === "string") return v;
  if (unit === "crore") return `₹${v.toLocaleString("en-IN", { maximumFractionDigits: 0 })} cr`;
  return `${v.toFixed(2)}%`;
}

export interface Display {
  previous: string;
  current: string;
  delta: string | null;
  direction: "up" | "down" | "flat" | null;
}

export function describe(f: Finding): Display {
  const unit = unitOf(f);
  const d = f.percentage_point_difference;
  let delta: string | null = null;
  let direction: Display["direction"] = null;

  if (d !== null && d !== undefined) {
    direction = d > 0 ? "up" : d < 0 ? "down" : "flat";
    const sign = d > 0 ? "+" : d < 0 ? "−" : "";
    const abs = Math.abs(d).toFixed(2);
    const suffix =
      f.change_type === "expense_ratio_change" ? " bps" : f.change_type === "aum_change" ? "%" : " pp";
    delta = `${sign}${abs}${suffix}`;
  }

  return { previous: fmtValue(f.previous_value, unit), current: fmtValue(f.current_value, unit), delta, direction };
}

export function magnitude(f: Finding): number {
  return f.percentage_point_difference === null ? 0 : Math.abs(f.percentage_point_difference);
}

export function evidencePage(f: Finding): string {
  const pages = [f.previous_evidence?.page_number, f.current_evidence?.page_number];
  if (!pages[0] && !pages[1]) return "—";
  return `p.${pages[0] ?? "?"} → p.${pages[1] ?? "?"}`;
}

export function citation(f: Finding, side: "previous" | "current"): string {
  const ev = side === "previous" ? f.previous_evidence : f.current_evidence;
  const value = side === "previous" ? f.previous_value : f.current_value;
  return `${f.label}: ${value ?? "—"} (${side} factsheet, ${ev?.page_number ? `page ${ev.page_number}` : "page not located"}, ${ev?.confidence ?? "unknown"} confidence)`;
}
