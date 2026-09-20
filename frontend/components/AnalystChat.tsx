"use client";

import { useEffect, useRef, useState } from "react";
import { askAnalystChat } from "@/lib/api";

interface Msg {
  role: "user" | "assistant";
  text: string;
}

const SUGGESTIONS = [
  "What changed the most this month?",
  "Were there any new or exited holdings?",
  "Did the expense ratio move?",
];

export default function AnalystChat({ scanId }: { scanId: string }) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "nearest" });
  }, [messages, loading]);

  async function send(text?: string) {
    const question = (text ?? input).trim();
    if (!question || loading) return;
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setLoading(true);
    try {
      const resp = await askAnalystChat(scanId, question);
      setMessages((m) => [...m, { role: "assistant", text: resp.answer }]);
    } catch {
      setMessages((m) => [...m, { role: "assistant", text: "The analyst chat could not be reached. Try again." }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="rounded border border-rule bg-panel">
      <div className="border-b border-rule px-5 py-3.5">
        <h2 className="font-serif text-lg font-semibold">Ask about this scan</h2>
        <p className="mt-0.5 text-xs text-muted">Answers use only this scan&rsquo;s findings and evidence.</p>
      </div>

      <div className="max-h-72 space-y-3 overflow-y-auto px-5 py-4">
        {messages.length === 0 && (
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="rounded-full border border-rule px-3 py-1 text-sm text-muted hover:border-accent hover:text-accent"
              >
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "flex justify-end" : ""}>
            <p
              className={`max-w-[85%] whitespace-pre-line rounded px-3 py-2 text-sm leading-relaxed ${
                m.role === "user" ? "bg-accent text-white" : "bg-surface"
              }`}
            >
              {m.text}
            </p>
          </div>
        ))}
        {loading && <p className="text-sm text-muted">Reading the findings…</p>}
        <div ref={endRef} />
      </div>

      <form
        className="flex gap-2 border-t border-rule px-5 py-3"
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          aria-label="Ask a question about this scan"
          placeholder="Ask a question…"
          className="flex-1 rounded border border-rule bg-surface px-3 py-2 text-sm placeholder:text-muted/70"
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          className="rounded bg-accent px-4 py-2 text-sm font-medium text-white disabled:opacity-40"
        >
          Ask
        </button>
      </form>
    </section>
  );
}
