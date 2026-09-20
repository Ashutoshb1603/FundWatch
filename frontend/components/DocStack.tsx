"use client";

import DocPage from "./DocPage";

function Tag({ children }: { children: React.ReactNode }) {
  return (
    <span className="absolute -bottom-3 left-3 max-w-[88%] truncate rounded bg-accent px-2 py-0.5 text-xs font-medium text-white shadow">
      {children}
    </span>
  );
}

/** Two factsheet pages fanned out in the top-right corner. They "attach" as files are chosen. */
export default function DocStack({
  previousName,
  currentName,
}: {
  previousName?: string;
  currentName?: string;
}) {
  return (
    <div
      aria-hidden
      className="pointer-events-none absolute -right-16 -top-16 z-0 hidden h-[520px] w-[600px] lg:block xl:-right-8"
    >
      <div className="float-b absolute right-2 top-24 w-[260px] origin-bottom-left">
        <div className="relative">
          <DocPage attached={!!currentName} />
          {currentName && <Tag>{currentName}</Tag>}
        </div>
      </div>
      <div className="float-a absolute right-[250px] top-32 w-[270px] origin-bottom-right">
        <div className="relative">
          <DocPage attached={!!previousName} />
          {previousName && <Tag>{previousName}</Tag>}
        </div>
      </div>
    </div>
  );
}
