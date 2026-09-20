"use client";

import { useState } from "react";
import { askAnalystChat } from "@/lib/api";

interface Msg {
  role: "user" | "assistant";
  text: string;
}

export default function AnalystChat({ scanId }: { scanId: string }) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function send() {
    if (!input.trim()) return;
    const question = input.trim();
    setMessages((m) => [...m, { role: "user", text: question }]);
    setInput("");
    setLoading(true);
    try {
      const resp = await askAnalystChat(scanId, question);
      setMessages((m) => [...m, { role: "assistant", text: resp.answer }]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: "Something went wrong reaching the analyst chat." },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="rounded-sm border border-ink-border bg-ink-light/60 p-6">
      <div className="evidence-tag text-xs uppercase tracking-widest text-gold">Analyst Chat</div>
      <p className="mt-2 text-xs text-slate-500">
        Answers are grounded only in this scan&rsquo;s findings and evidence — not general market knowledge.
      </p>

      <div className="mt-4 max-h-64 space-y-3 overflow-y-auto">
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <span
              className={`inline-block rounded-sm px-3 py-2 text-sm ${
                m.role === "user" ? "bg-gold/20 text-paper" : "bg-ink text-slate-300"
              }`}
            >
              {m.text}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-4 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="What changed the most this month?"
          className="flex-1 rounded-sm border border-ink-border bg-ink px-3 py-2 text-sm text-paper placeholder:text-slate-600 focus:border-gold focus:outline-none"
        />
        <button
          onClick={send}
          disabled={loading}
          className="rounded-sm bg-gold px-4 py-2 text-sm font-medium text-ink disabled:opacity-40"
        >
          Ask
        </button>
      </div>
    </div>
  );
}
