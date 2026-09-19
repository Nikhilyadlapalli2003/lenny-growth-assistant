# Design — The Lenny Growth Assistant

## 1. UI/UX principles
- **Split focus, not split attention.** The two-pane layout keeps the conversation (left) and its
  tangible output (right) visually adjacent, mirroring the mental model of "I asked, here's the
  thing I asked for" rather than a modal or separate page.
- **Provenance is always visible.** Every grounded answer shows its source chips inline instead of
  in a hidden tooltip or footnote — trust is the product's core value proposition.
- **No silent failure.** Provider errors, empty retrieval, and blocked artifacts all render as
  visible, specific messages in the transcript rather than blank states or generic "error" toasts.

## 2. Information architecture
- Single-page app: header (title + model selector) → scrollable message list → composer.
- Right pane is a secondary, collapsible surface — it never blocks the primary chat flow and starts
  empty with a one-line explainer rather than an empty box.
- Two send actions in the composer ("Send" vs. "Ship 30 essay") make the skill boundary a visible,
  deliberate user choice instead of an inferred intent — reduces ambiguity about which prompt
  contract is being invoked.

## 3. Key interaction states
| State | Treatment |
|---|---|
| No session yet | Composer is present but send is a no-op with an inline "no active session" note (handled in `useChatStream`) |
| Streaming/loading | "Thinking…" text under the last message; composer stays enabled (no blocking spinner) |
| Grounded answer with sources | Small gray chips under the bubble, one per citation, `title` attribute shows similarity score |
| Insufficient context | Same bubble styling as any assistant message — no special "error" chrome, since this is a valid, expected answer, not a failure |
| Artifact generated | "View generated artifact →" link appears under that specific message, not just globally, so history stays traceable to which turn produced it |
| Provider error (e.g., Ollama down) | Assistant bubble contains the human-readable error from the provider layer; user can switch providers via the dropdown and retry |

## 4. Responsive behavior
- Right pane (`aside`) is hidden below the `md` breakpoint — on mobile, artifacts are reachable via
  the inline "View generated artifact" link, which (documented next step) would push to a full-screen
  route rather than a side panel.
- Chat pane uses `flex-1 min-w-0` so long unbroken tokens (URLs, code) don't blow out the layout.
- Composer buttons wrap acceptably down to ~360px width; no horizontal scroll introduced.

## 5. Accessibility considerations
- All interactive controls (`select`, buttons, text input) have visible text labels or `aria-label`s
  (e.g., "LLM provider", "Close artifact viewer").
- Color is never the only signal: the LOCAL/CLOUD badge pairs color with text, not color alone.
- Iframe artifact has an explicit `title` attribute for screen readers.
- Contrast: body text uses `gray-900` on `gray-50`/white surfaces, meeting WCAG AA for normal text.
- Enter-to-send is supported alongside the explicit Send button (keyboard-only users aren't forced to
  tab to a button).

## 6. Design decisions & trade-offs
- **Plain Tailwind utility classes over a component library** — keeps the artifact-viewer boundary
  (the security-sensitive part of the UI) easy to audit without hunting through abstracted component
  internals.
- **No streaming token-by-token render on the frontend in this submission** — the backend streams
  from the provider internally but returns a single consolidated response to keep the take-home's
  scope bounded; true SSE-to-frontend streaming is a documented, straightforward extension
  (`StreamingResponse` + `EventSource` on the client) noted in README.md's "Next steps."
- **Markdown rendered via `react-markdown`, HTML via sandboxed iframe** — two different artifact
  types get two different renderers rather than one generic "innerHTML for everything," because that
  distinction is exactly what keeps Markdown output safe by construction while containing the
  genuinely risky HTML path.
