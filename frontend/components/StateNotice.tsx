"use client";

type Tone = "error" | "warning" | "info";

const TONE: Record<Tone, string> = {
  error: "border-down/40 bg-down/5 text-down",
  warning: "border-medium/40 bg-medium/5 text-[#8A5A12]",
  info: "border-rule bg-panel text-muted",
};

export default function StateNotice({
  tone = "info",
  title,
  children,
  action,
}: {
  tone?: Tone;
  title?: string;
  children?: React.ReactNode;
  action?: { label: string; onClick: () => void };
}) {
  return (
    <div role={tone === "error" ? "alert" : "status"} className={`rounded border px-4 py-3 text-sm ${TONE[tone]}`}>
      {title && <div className="font-medium">{title}</div>}
      {children && <div className={title ? "mt-1" : ""}>{children}</div>}
      {action && (
        <button onClick={action.onClick} className="mt-2 font-medium underline underline-offset-2">
          {action.label}
        </button>
      )}
    </div>
  );
}
