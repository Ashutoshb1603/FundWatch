"use client";

import { useRef, useState } from "react";

function FileSlot({
  label,
  periodHint,
  file,
  onSelect,
}: {
  label: string;
  periodHint: string;
  file: File | null;
  onSelect: (f: File) => void;
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
      onClick={() => inputRef.current?.click()}
      className={`cursor-pointer rounded-sm border ${
        dragging ? "border-gold" : "border-ink-border"
      } bg-ink-light/60 p-8 transition-colors hover:border-gold/60`}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) onSelect(f);
        }}
      />
      <div className="evidence-tag text-xs uppercase tracking-widest text-slate-400">{periodHint}</div>
      <div className="mt-2 font-serif text-xl text-paper">{label}</div>
      <div className="mt-4 text-sm text-slate-400">
        {file ? (
          <span className="text-teal">{file.name}</span>
        ) : (
          "Drop a PDF here, or click to browse"
        )}
      </div>
    </div>
  );
}

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

  return (
    <div className="mx-auto max-w-3xl">
      <div className="evidence-tag text-xs uppercase tracking-widest text-gold">FundWatch</div>
      <h1 className="mt-3 font-serif text-4xl leading-tight text-paper sm:text-5xl">
        Understand what changed in your mutual fund&rsquo;s latest disclosure.
      </h1>
      <p className="mt-4 max-w-xl text-slate-400">
        Upload two monthly factsheets for the same scheme. FundWatch extracts the numbers,
        compares them deterministically, and shows you exactly where in each document a
        finding came from — before any AI explains a word of it.
      </p>

      <div className="mt-10 grid gap-4 sm:grid-cols-2">
        <FileSlot label="Previous factsheet" periodHint="Period A" file={previous} onSelect={setPrevious} />
        <FileSlot label="Current factsheet" periodHint="Period B" file={current} onSelect={setCurrent} />
      </div>

      {error && (
        <div className="mt-6 rounded-sm border border-rust/50 bg-rust/10 px-4 py-3 text-sm text-rust">
          {error}
        </div>
      )}

      <div className="mt-6">
        <label className="evidence-tag text-xs uppercase tracking-widest text-slate-500">Scheme name (recommended for multi-scheme AMC factsheets)</label>
        <input
          value={schemeName}
          onChange={(e) => setSchemeName(e.target.value)}
          placeholder="e.g. HDFC Flexi Cap Fund"
          className="mt-2 w-full rounded-sm border border-ink-border bg-ink px-3 py-3 text-sm text-paper placeholder:text-slate-600 focus:border-gold focus:outline-none"
        />
      </div>

      <button
        disabled={!previous || !current || loading}
        onClick={() => previous && current && onAnalyze(previous, current, schemeName.trim() || undefined)}
        className="mt-8 rounded-sm bg-gold px-6 py-3 font-medium text-ink transition-opacity disabled:cursor-not-allowed disabled:opacity-30 hover:opacity-90"
      >
        {loading ? "Analyzing…" : "Analyze Changes"}
      </button>
    </div>
  );
}
