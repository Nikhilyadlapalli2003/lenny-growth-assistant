"use client";
import { useState, useCallback } from "react";
import { api, type ChatResponse, type Provider } from "@/lib/api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: ChatResponse["sources"];
  artifactId?: string | null;
}

export function useChatStream(sessionId: string | null, provider: Provider) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const send = useCallback(
    async (text: string, mode: "default" | "ship30" = "default") => {
      if (!sessionId) {
        setError("No active session yet - try again in a moment.");
        return;
      }
      setError(null);
      setMessages((prev) => [...prev, { role: "user", content: text }]);
      setLoading(true);
      try {
        const res = await api.sendChat(sessionId, text, mode, provider);
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: res.content, sources: res.sources, artifactId: res.artifact_id },
        ]);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Something went wrong talking to the assistant.");
      } finally {
        setLoading(false);
      }
    },
    [sessionId, provider]
  );

  return { messages, send, loading, error };
}
