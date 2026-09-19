"use client";
import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { SourceCitation } from "@/lib/api";

interface MessageItemProps {
  role: "user" | "assistant";
  content: string;
  sources?: SourceCitation[];
  onOpenArtifact?: () => void;
  hasArtifact?: boolean;
}

export const MessageItem: React.FC<MessageItemProps> = ({ role, content, sources, onOpenArtifact, hasArtifact }) => {
  const isUser = role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isUser ? "bg-gray-900 text-white" : "bg-white border border-gray-200"
        }`}
      >
        <div className="prose prose-sm max-w-none prose-p:my-1">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>

        {hasArtifact && (
          <button
            onClick={onOpenArtifact}
            className="mt-2 text-xs font-medium text-blue-600 hover:underline"
          >
            View generated artifact →
          </button>
        )}

        {sources && sources.length > 0 && (
          <div className="mt-2 pt-2 border-t border-gray-100 flex flex-wrap gap-1">
            {sources.map((s, i) => (
              <span
                key={i}
                title={`similarity ${s.score.toFixed(2)}`}
                className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded"
              >
                {s.episode}{s.guest ? ` · ${s.guest}` : ""}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
