"use client";
import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { SandboxedIframe } from "./SandboxedIframe";
import type { ArtifactResponse } from "@/lib/api";

interface ArtifactViewerProps {
  artifact: ArtifactResponse | null;
  onClose: () => void;
}

export const ArtifactViewer: React.FC<ArtifactViewerProps> = ({ artifact, onClose }) => {
  if (!artifact) {
    return (
      <div className="hidden md:flex flex-col items-center justify-center h-full text-sm text-gray-400 border-l border-gray-200 w-full">
        Generated documents and rendered snippets will appear here.
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full border-l border-gray-200 w-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-white">
        <h2 className="text-sm font-semibold truncate">{artifact.title}</h2>
        <button
          onClick={onClose}
          className="text-xs text-gray-500 hover:text-gray-800"
          aria-label="Close artifact viewer"
        >
          Close ✕
        </button>
      </div>
      <div className="flex-1 overflow-auto p-4 bg-gray-50">
        {artifact.artifact_type === "markdown" ? (
          <div className="prose prose-sm max-w-none bg-white rounded-lg border border-gray-200 p-4">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{artifact.content}</ReactMarkdown>
          </div>
        ) : (
          <SandboxedIframe content={artifact.content} title={artifact.title} />
        )}
      </div>
    </div>
  );
};
