"use client";
import React, { useMemo } from "react";
import DOMPurify from "dompurify";

interface SandboxedIframeProps {
  content: string;
  title: string;
}

/**
 * Renders untrusted model-generated HTML inside a sandboxed iframe.
 * - sandbox="allow-scripts" (NO allow-same-origin): the iframe gets its own
 *   opaque origin, so it cannot read/write the parent's cookies, localStorage,
 *   or DOM even if a script slips through sanitization.
 * - DOMPurify strips dangerous tags/attributes as a second layer of defense
 *   before the markup is ever handed to the iframe.
 */
export const SandboxedIframe: React.FC<SandboxedIframeProps> = ({ content, title }) => {
  const cleanHtml = useMemo(
    () =>
      DOMPurify.sanitize(content, {
        WHOLE_DOCUMENT: false,
        FORBID_TAGS: ["iframe", "object", "embed", "form"],
        FORBID_ATTR: ["onerror", "onload", "onclick"],
      }),
    [content]
  );

  return (
    <div className="flex flex-col h-full border border-gray-200 rounded-lg overflow-hidden bg-white shadow-sm">
      <div className="bg-gray-50 border-b border-gray-200 px-4 py-2 flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-700 tracking-wide uppercase">
          Artifact: {title}
        </span>
        <span className="text-xs text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
          Sandboxed preview
        </span>
      </div>
      <iframe
        title={title}
        srcDoc={cleanHtml}
        sandbox="allow-scripts"
        className="w-full h-full border-none flex-1"
      />
    </div>
  );
};
