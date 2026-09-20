"use client";

import { useState } from "react";
import UploadPanel from "@/components/UploadPanel";
import ProcessingView from "@/components/ProcessingView";
import Dashboard from "@/components/Dashboard";
import { analyzeFactsheets } from "@/lib/api";
import { ScanResult } from "@/lib/types";

type Stage = "upload" | "processing" | "dashboard";

export default function Home() {
  const [stage, setStage] = useState<Stage>("upload");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState<string | null>(null);

  async function handleAnalyze(previous: File, current: File, schemeName?: string) {
    setError(null);
    setStage("processing");
    setActiveStep("extract_text_tables");
    try {
      const res = await analyzeFactsheets(previous, current, schemeName, setActiveStep);
      for (const entry of res.steps_log ?? []) setActiveStep(entry.step);
      setResult(res);
      if (res.status === "error") {
        setError(res.error || "Analysis failed.");
        setStage("upload");
        return;
      }
      setStage("dashboard");
    } catch (e: any) {
      setError(e.message || "Something went wrong.");
      setStage("upload");
    }
  }

  function startOver() {
    setResult(null);
    setError(null);
    setStage("upload");
  }

  return (
    <main className="min-h-screen px-6 py-16 sm:py-24">
      {stage === "upload" && (
        <UploadPanel onAnalyze={handleAnalyze} loading={false} error={error} />
      )}
      {stage === "processing" && <ProcessingView activeStep={activeStep} />}
      {stage === "dashboard" && result && result.status !== "validation_failed" && (
        <Dashboard result={result} onStartOver={startOver} />
      )}
      {stage === "dashboard" && result && result.status === "validation_failed" && (
        <div className="mx-auto max-w-xl">
          <div className="evidence-tag text-xs uppercase tracking-widest text-rust">Cannot Compare</div>
          <h2 className="mt-3 font-serif text-2xl text-paper">These documents don&rsquo;t look comparable</h2>
          <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-slate-300">
            {result.validation?.issues.map((issue, i) => <li key={i}>{issue}</li>)}
          </ul>
          <button
            onClick={startOver}
            className="mt-8 rounded-sm bg-gold px-6 py-3 font-medium text-ink hover:opacity-90"
          >
            Try again
          </button>
        </div>
      )}
    </main>
  );
}
