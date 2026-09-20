"use client";

import { useRef, useState } from "react";
import StateNotice from "./StateNotice";
import DocStack from "./DocStack";
import Logo from "./Logo";
import { loadSample } from "@/lib/sample";

const MAX_BYTES = 25 * 1024 * 1024;

function size(n: number) {
  return n > 1024 * 1024 ? `${(n / 1024 / 1024).toFixed(1)} MB` : `${Math.round(n / 1024)} KB`;
}

function FileSlot({
  step,
  label,
  file,
  onSelect,
  onClear,
}: {
  step: string;
  label: string;
  file: File | null;
  onSelect: (f: File) => void;
  onClear: () => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        const f = e.dataTransfer.files?.[0];
        if (f) onSelect(f);
      }}
      className={`flex items-center gap-4 rounded border bg-panel px-4 py-4 transition-colors ${
        dragging ? "border-accent bg-accent-soft" : file ? "border-accent/50" : "border-dashed border-rule"
      }`}
    >
      <span className="num flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-rule text-xs text-muted">
        {step}
      </span>
      <div className="min-w-0 flex-1">
        <div className="text-sm font-medium">{label}</div>
        {file ? (
          <div className="mt-0.5 truncate text-sm text-muted">
            {file.name} <span className="num text-xs">· {size(file.size)}</span>
          </div>
        ) : (
          <div className="mt-0.5 text-sm text-muted">Drop a PDF here</div>
        )}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        aria-label={label}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onSelect(f);
          e.target.value = "";
        }}
      />
      {file ? (
        <button onClick={onClear} className="text-sm text-muted hover:text-ink">
          Remove
        </button>
      ) : (
        <button onClick={() => inputRef.current?.click()} className="text-sm font-medium text-accent hover:underline">
          Browse
        </button>
      )}
    </div>
  );
}

const STEPS = [
  ["Extract", "Text and tables are read from both PDFs. Scanned pages fall back to OCR."],
  ["Compare", "Plain code, not a language model, diffs holdings, sectors, AUM, costs and risk."],
  ["Verify", "Every finding links to the source page in each document."],
];

export default function UploadPanel({
  onAnalyze,
  loading,
  error,
}: {
  onAnalyze: (previous: File, current: File, schemeName?: string) => void;
  loading: boolean;
  error: string | null;
}) {
  const [previous, setPrevious] = useState<File | null>(null);
  const [current, setCurrent] = useState<File | null>(null);
  const [schemeName, setSchemeName] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const [loadingSample, setLoadingSample] = useState(false);

  function accept(setter: (f: File) => void) {
    return (f: File) => {
      if (f.type !== "application/pdf" && !f.name.toLowerCase().endsWith(".pdf")) {
        setLocalError("Only PDF files are supported.");
        return;
      }
      if (f.size > MAX_BYTES) {
        setLocalError("Each PDF must be 25 MB or smaller.");
        return;
      }
      setLocalError(null);
      setter(f);
    };
  }

  async function useSample() {
    setLoadingSample(true);
    setLocalError(null);
    try {
      const s = await loadSample();
      setPrevious(s.previous);
      setCurrent(s.current);
    } catch (e: any) {
      setLocalError(e.message || "Could not load the sample factsheets.");
    } finally {
      setLoadingSample(false);
    }
  }

  const shownError = localError || error;
  const ready = !!previous && !!current && !loading;

  return (
    <>
    <DocStack previousName={previous?.name} currentName={current?.name} />
    <div className="fade-up relative z-10 mx-auto grid min-h-[calc(100vh-8rem)] max-w-6xl items-center gap-14 px-5 sm:px-8 lg:grid-cols-[1.05fr_1fr]">
      <div>
        <Logo />
        <h1 className="mt-10 font-serif text-4xl leading-[1.1] tracking-tight sm:text-5xl">
          What changed in this fund&rsquo;s latest disclosure?
        </h1>
        <p className="mt-5 max-w-lg text-lg leading-relaxed text-muted">
          Compare two monthly factsheets for one scheme. You get a ranked list of material changes, each tied to the
          page it came from.
        </p>

        <ol className="mt-10 max-w-lg divide-y divide-rule border-y border-rule">
          {STEPS.map(([title, body], i) => (
            <li key={title} className="flex gap-4 py-3.5">
              <span className="num w-5 pt-0.5 text-sm text-muted">{i + 1}</span>
              <div>
                <div className="text-sm font-medium">{title}</div>
                <div className="text-sm text-muted">{body}</div>
              </div>
            </li>
          ))}
        </ol>
        <p className="mt-6 max-w-lg text-sm text-muted">
          FundWatch reports what changed. It never suggests buying, selling or holding.
        </p>
      </div>

      <div className="mt-40 rounded-lg border border-rule bg-panel p-6 shadow-[0_24px_50px_-28px_rgba(27,27,24,0.35)] sm:p-8 lg:mt-56">
        <div className="flex items-baseline justify-between">
          <h2 className="font-serif text-xl font-semibold">New comparison</h2>
          <button
            onClick={useSample}
            disabled={loadingSample || loading}
            className="text-sm font-medium text-accent hover:underline disabled:opacity-50"
          >
            {loadingSample ? "Loading…" : "Use sample (HDFC, Jul → Aug 2026)"}
          </button>
        </div>

        <div className="mt-5 space-y-3">
          <FileSlot step="A" label="Earlier factsheet" file={previous} onSelect={accept(setPrevious)} onClear={() => setPrevious(null)} />
          <FileSlot step="B" label="Later factsheet" file={current} onSelect={accept(setCurrent)} onClear={() => setCurrent(null)} />
        </div>

        <div className="mt-6">
          <label htmlFor="scheme" className="text-sm font-medium">
            Scheme name <span className="font-normal text-muted">(optional)</span>
          </label>
          <input
            id="scheme"
            value={schemeName}
            onChange={(e) => setSchemeName(e.target.value)}
            placeholder="HDFC Flexi Cap Fund"
            className="mt-1.5 w-full rounded border border-rule bg-panel px-3 py-2.5 text-sm placeholder:text-muted/60"
          />
          <p className="mt-1.5 text-xs text-muted">
            Recommended when the PDF covers several schemes, so extraction focuses on the right pages.
          </p>
        </div>

        {shownError && (
          <div className="mt-5">
            <StateNotice tone="error" title="Couldn’t start the comparison">
              {shownError}
            </StateNotice>
          </div>
        )}

        <button
          disabled={!ready}
          onClick={() => previous && current && onAnalyze(previous, current, schemeName.trim() || undefined)}
          className="mt-6 w-full rounded bg-accent px-6 py-3 font-medium text-white transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {loading ? "Analyzing…" : "Compare factsheets"}
        </button>
        {!ready && !loading && (
          <p className="mt-2 text-center text-xs text-muted">Add both factsheets to continue.</p>
        )}
      </div>
    </div>
    </>
  );
}
