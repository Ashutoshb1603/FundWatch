"use client";

import { CATEGORIES } from "@/lib/format";
import { Priority } from "@/lib/types";

export type SortKey = "priority" | "magnitude";

interface Props {
  counts: Record<string, number>;
  total: number;
  category: string;
  onCategory: (k: string) => void;
  priorities: Set<Priority>;
  onTogglePriority: (p: Priority) => void;
  sort: SortKey;
  onSort: (s: SortKey) => void;
}

const PRIORITY_DOT: Record<Priority, string> = { HIGH: "bg-high", MEDIUM: "bg-medium", LOW: "bg-low" };

export default function FilterRail(p: Props) {
  const items = [{ key: "all", title: "All changes", count: p.total }].concat(
    CATEGORIES.map((c) => ({ key: c.key, title: c.title, count: p.counts[c.key] ?? 0 }))
  );

  return (
    <aside className="space-y-8 text-sm">
      {/* Small screens: compact select instead of a rail */}
      <div className="lg:hidden">
        <label className="col-head" htmlFor="cat">
          Category
        </label>
        <select
          id="cat"
          value={p.category}
          onChange={(e) => p.onCategory(e.target.value)}
          className="mt-1.5 w-full rounded border border-rule bg-panel px-3 py-2"
        >
          {items.map((i) => (
            <option key={i.key} value={i.key}>
              {i.title} ({i.count})
            </option>
          ))}
        </select>
      </div>

      <nav className="hidden lg:block" aria-label="Categories">
        <div className="col-head mb-2">Category</div>
        <ul className="space-y-0.5">
          {items.map((i) => (
            <li key={i.key}>
              <button
                onClick={() => p.onCategory(i.key)}
                aria-current={p.category === i.key}
                className={`flex w-full items-center justify-between rounded px-2.5 py-1.5 text-left ${
                  p.category === i.key ? "bg-accent-soft font-medium text-accent" : "text-muted hover:text-ink"
                }`}
              >
                {i.title}
                <span className="num text-xs">{i.count}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>

      <div>
        <div className="col-head mb-2">Priority</div>
        <div className="space-y-1.5">
          {(["HIGH", "MEDIUM", "LOW"] as Priority[]).map((pr) => (
            <label key={pr} className="flex cursor-pointer items-center gap-2.5 px-2.5 text-muted">
              <input
                type="checkbox"
                checked={p.priorities.has(pr)}
                onChange={() => p.onTogglePriority(pr)}
                className="accent-[#1F5C4D]"
              />
              <span className={`h-2 w-2 rounded-full ${PRIORITY_DOT[pr]}`} />
              <span className="capitalize">{pr.toLowerCase()}</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <div className="col-head mb-2">Sort by</div>
        <div className="inline-flex rounded border border-rule bg-panel p-0.5">
          {(["priority", "magnitude"] as SortKey[]).map((s) => (
            <button
              key={s}
              onClick={() => p.onSort(s)}
              className={`rounded-sm px-3 py-1 capitalize ${
                p.sort === s ? "bg-accent text-white" : "text-muted hover:text-ink"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      <p className="hidden text-xs leading-relaxed text-muted lg:block">
        Keyboard: <kbd className="num rounded border border-rule px-1">j</kbd>{" "}
        <kbd className="num rounded border border-rule px-1">k</kbd> to move,{" "}
        <kbd className="num rounded border border-rule px-1">Enter</kbd> to open evidence.
      </p>
    </aside>
  );
}
