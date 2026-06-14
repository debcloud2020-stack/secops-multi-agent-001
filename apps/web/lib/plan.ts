// Presentation helpers for the incident-response plan / agent findings.
//
// The backend's response_plan (and the Incident Response finding's detail) is a single
// string of the form:
//   Response plan for 'X':
//   1. step…
//   …
//   [memory] <recalled incident title>
//   [synthesis] <full LLM markdown synthesis | offline stub echo>
//
// These helpers strip the internal "[memory]"/"[synthesis]" scaffolding (and the offline
// stub prefix) so only the human-facing plan shows, and produce short per-agent summaries
// for the threat feed — keeping the full rendered plan to the single Response plan panel.

const MEMORY_LINE = /\n?[ \t]*\[memory\][^\n]*/gi;
const STUB_PREFIX = /^\s*\[offline-stub:[^\]]*\]\s*/i;
const SYNTH_TAG = "[synthesis]";

/** The brief part (title + numbered steps), with the [memory] line removed. */
function briefPart(raw: string): string {
  const i = raw.indexOf(SYNTH_TAG);
  const brief = i >= 0 ? raw.slice(0, i) : raw;
  return brief.replace(MEMORY_LINE, "").trim();
}

/** The synthesis body after [synthesis], with the offline-stub prefix stripped. */
function synthPart(raw: string): { body: string; isStub: boolean } {
  const i = raw.indexOf(SYNTH_TAG);
  if (i < 0) return { body: "", isStub: false };
  const after = raw.slice(i + SYNTH_TAG.length);
  const isStub = STUB_PREFIX.test(after);
  return { body: after.replace(STUB_PREFIX, "").trim(), isStub };
}

/** Count the numbered steps in the brief part (1. 2. 3. …). */
export function countPlanSteps(raw: string | null | undefined): number {
  if (!raw) return 0;
  return (briefPart(raw).match(/^[ \t]*\d+\.\s+\S/gm) ?? []).length;
}

/**
 * The single canonical, human-facing plan (markdown). Strips the [memory]/[synthesis]
 * scaffolding; when both a brief summary and a fuller *real* synthesis exist, returns the
 * richer synthesis. The offline-stub echo is not a real synthesis, so we fall back to the
 * brief steps in mock mode.
 */
export function canonicalPlan(raw: string | null | undefined): string | null {
  if (!raw || !raw.trim()) return null;
  const { body, isStub } = synthPart(raw);
  const chosen = body && !isStub ? body : briefPart(raw);
  // Belt-and-suspenders: never leak the internal tags into the rendered output.
  return chosen
    .replace(MEMORY_LINE, "")
    .replace(/\[synthesis\]/gi, "")
    .replace(STUB_PREFIX, "")
    .trim();
}

/** Remove markdown syntax + internal markers for a plain-text one-liner. */
function stripMarkup(s: string): string {
  return s
    .replace(/\[(memory|synthesis)\][^\n]*/gi, "")
    .replace(/\[offline-stub:[^\]]*\]/gi, "")
    .replace(/^#{1,6}\s+/gm, "") // headings
    .replace(/\*\*([^*]+)\*\*/g, "$1") // bold
    .replace(/\*([^*]+)\*/g, "$1") // italic
    .replace(/`([^`]+)`/g, "$1") // inline code
    .replace(/^\s*[-*+]\s+/gm, "") // bullets
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * A concise (≈1–2 line) summary of one agent finding for the threat feed. The Incident
 * Response finding is collapsed to a gist that points at the Response plan panel rather
 * than dumping the full plan.
 */
export function summarizeFinding(agent: string, detail: string): string {
  if (!detail) return "";
  if (agent === "incident_response") {
    if (/\[rejected\]/i.test(detail) || /rejected/i.test(detail)) {
      return "Response plan rejected — the proposed steps were not executed.";
    }
    const n = countPlanSteps(detail);
    return n > 0
      ? `Generated a ${n}-step response plan — see Response plan below.`
      : "Response plan ready — see Response plan below.";
  }
  const clean = stripMarkup(detail);
  const sentence = clean.match(/^(.*?[.!?])(\s|$)/)?.[1] ?? clean;
  if (sentence.length <= 160) return sentence;
  return sentence.slice(0, 160).trimEnd() + "…";
}
