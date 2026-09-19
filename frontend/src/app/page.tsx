"use client";
import React, { useEffect, useState } from "react";
import { api, type ArtifactResponse, type Provider } from "@/lib/api";
import { useChatStream } from "@/hooks/useChatStream";
import { MessageItem } from "@/components/Chat/MessageItem";
import { ModelSelector } from "@/components/Chat/ModelSelector";
import { ArtifactViewer } from "@/components/Artifact/ArtifactViewer";

export default function HomePage() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [provider, setProvider] = useState<Provider>("ollama");
  const [input, setInput] = useState("");
  const [artifact, setArtifact] = useState<ArtifactResponse | null>(null);
  const { messages, send, loading, error } = useChatStream(sessionId, provider);

  useEffect(() => {
    api.createSession(provider).then((s) => setSessionId(s.id)).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSend = (mode: "default" | "ship30" = "default") => {
    if (!input.trim()) return;
    send(input.trim(), mode);
    setInput("");
  };

  const openArtifact = async (artifactId: string) => {
    try {
      const a = await api.getArtifact(artifactId);
      setArtifact(a);
    } catch {
      // swallow - the user still sees the reply text even if artifact fetch fails
    }
  };

  return (
    <main className="flex h-screen w-screen overflow-hidden">
      {/* Left pane: chat */}
      <section className="flex flex-col flex-1 min-w-0">
        <header className="flex items-center justify-between px-5 py-3 border-b border-gray-200 bg-white">
          <h1 className="text-sm font-semibold">Lenny Growth Assistant</h1>
          <ModelSelector provider={provider} onChange={setProvider} />
        </header>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3">
          {messages.length === 0 && (
            <p className="text-sm text-gray-400">
              Ask a product or growth question grounded in Lenny&apos;s Podcast transcripts.
            </p>
          )}
          {messages.map((m, i) => (
            <MessageItem
              key={i}
              role={m.role}
              content={m.content}
              sources={m.sources}
              hasArtifact={!!m.artifactId}
              onOpenArtifact={() => m.artifactId && openArtifact(m.artifactId)}
            />
          ))}
          {loading && <p className="text-xs text-gray-400">Thinking…</p>}
          {error && <p className="text-xs text-red-500">{error}</p>}
        </div>

        <div className="border-t border-gray-200 bg-white p-3 flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Ask about onboarding, retention, pricing…"
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm"
          />
          <button
            onClick={() => handleSend("default")}
            className="bg-gray-900 text-white text-sm px-4 py-2 rounded-lg"
          >
            Send
          </button>
          <button
            onClick={() => handleSend("ship30")}
            className="border border-gray-300 text-sm px-3 py-2 rounded-lg"
            title="Turn this into a Ship 30 for 30-style essay"
          >
            Ship 30 essay
          </button>
        </div>
      </section>

      {/* Right pane: artifact viewer */}
      <aside className="hidden md:block w-[38%] max-w-xl bg-white">
        <ArtifactViewer artifact={artifact} onClose={() => setArtifact(null)} />
      </aside>
    </main>
  );
}
