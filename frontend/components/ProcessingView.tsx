"use client";

const LABELS: Record<string, string> = {
  extract_text_tables: "Extracting text",
  validate_extraction: "Validating extraction",
  normalize_factsheets: "Normalizing data",
  validate_fund_identity: "Validating fund identity",
  compare_data: "Comparing periods",
  detect_material_changes_and_attach_evidence: "Detecting material changes",
  generate_explanations: "Generating explanations",
  generate_analyst_brief: "Generating analyst brief",
};

const ORDER = Object.keys(LABELS);

export default function ProcessingView({ activeStep }: { activeStep: string | null }) {
  const activeIdx = activeStep ? ORDER.indexOf(activeStep) : -1;

  return (
    <div className="mx-auto max-w-md">
      <div className="evidence-tag text-xs uppercase tracking-widest text-gold">FundWatch</div>
      <h2 className="mt-3 font-serif text-2xl text-paper">Reading the disclosures</h2>
      <div className="mt-8 space-y-3">
        {ORDER.map((key, i) => {
          const done = activeIdx > i || activeIdx === -1;
          const active = activeIdx === i;
          return (
            <div key={key} className="flex items-center gap-3 text-sm">
              <span
                className={`evidence-tag flex h-5 w-5 items-center justify-center rounded-full border text-[10px] ${
                  active
                    ? "border-gold text-gold"
                    : done
                    ? "border-teal text-teal"
                    : "border-ink-border text-slate-500"
                }`}
              >
                {done ? "✓" : active ? "●" : "·"}
              </span>
              <span className={active ? "text-paper" : done ? "text-slate-400" : "text-slate-500"}>
                {LABELS[key]}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
