"use client";

import { useState } from "react";
import UploadPanel from "@/components/UploadPanel";
import ProcessingView, { STEP_KEYS } from "@/components/ProcessingView";
import Dashboard from "@/components/Dashboard";
import StateNotice from "@/components/StateNotice";
import Logo from "@/components/Logo";
import { analyzeFactsheets, isAwsMode } from "@/lib/api";
import { ScanResult } from "@/lib/types";

type Stage = "upload" | "processing" | "dashboard";

export default function Home() {
  const [stage, setStage] = useState<Stage>("upload");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState<string | null>(null);
  const [names, setNames] = useState<{ previous?: string; current?: string }>({});

  async function handleAnalyze(previous: File, current: File, schemeName?: string) {
    setError(null);
    setNames({ previous: previous.name, current: current.name });
    setStage("processing");
    setActiveStep("extract_text_tables");
    // The local server answers in one request, so it reports no live steps. Pace the step list by
    // estimate (never past the second-to-last step) so the wait is visible; the AWS path reports real steps.
    let pace: ReturnType<typeof setInterval> | undefined;
    if (!isAwsMode()) {
      let i = 0;
      pace = setInterval(() => {
        i = Math.min(i + 1, STEP_KEYS.length - 2);
        setActiveStep(STEP_KEYS[i]);
      }, 3500);
    }
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
    } finally {
      if (pace) clearInterval(pace);
    }
  }

  function startOver() {
    setResult(null);
    setError(null);
    setStage("upload");
  }

  return (
    <main className={`relative min-h-screen overflow-hidden ${stage === "dashboard" && result?.status !== "validation_failed" ? "" : "py-10 sm:py-14"}`}>
      {stage === "upload" && <UploadPanel onAnalyze={handleAnalyze} loading={false} error={error} />}
      {stage === "processing" && <ProcessingView activeStep={activeStep} previousName={names.previous} currentName={names.current} />}
      {stage === "dashboard" && result && result.status !== "validation_failed" && (
        <Dashboard result={result} onStartOver={startOver} />
      )}
      {stage === "dashboard" && result && result.status === "validation_failed" && (
        <div className="fade-up mx-auto max-w-xl px-5 sm:px-8">
          <Logo />
          <h2 className="mt-10 font-serif text-3xl tracking-tight">These documents can&rsquo;t be compared</h2>
          <p className="mt-2 text-muted">
            A comparison is only meaningful for the same scheme across comparable periods.
          </p>
          <div className="mt-6">
            <StateNotice tone="warning" title="What we found">
              <ul className="list-disc space-y-1 pl-5">
                {result.validation?.issues.map((issue, i) => (
                  <li key={i}>{issue}</li>
                ))}
              </ul>
            </StateNotice>
          </div>
          <button onClick={startOver} className="mt-8 rounded bg-accent px-6 py-3 font-medium text-white hover:opacity-90">
            Choose different files
          </button>
        </div>
      )}
    </main>
  );
}
