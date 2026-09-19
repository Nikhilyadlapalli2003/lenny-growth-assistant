"use client";
import React from "react";
import type { Provider } from "@/lib/api";

interface ModelSelectorProps {
  provider: Provider;
  onChange: (p: Provider) => void;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({ provider, onChange }) => (
  <div className="flex items-center gap-2 text-xs">
    <span className="text-gray-500">Model:</span>
    <select
      value={provider}
      onChange={(e) => onChange(e.target.value as Provider)}
      className="border border-gray-300 rounded px-2 py-1 bg-white"
      aria-label="LLM provider"
    >
      <option value="ollama">Ollama (local)</option>
      <option value="anthropic">Claude (cloud)</option>
    </select>
    <span
      className={`px-2 py-0.5 rounded-full text-[10px] font-medium ${
        provider === "ollama" ? "bg-blue-50 text-blue-700" : "bg-purple-50 text-purple-700"
      }`}
    >
      {provider === "ollama" ? "LOCAL" : "CLOUD"}
    </span>
  </div>
);
