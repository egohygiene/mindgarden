import { z } from "zod";

const identifier = z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/);
const digest = z.string().regex(/^[a-f0-9]{64}$/);
const hashRevision = z.string().regex(/^sha256:[a-f0-9]{64}$/);
const revision = z.string().regex(/^(?:git:[a-f0-9]{40}|sha256:[a-f0-9]{64}|version:1\.[0-9]+\.[0-9]+)$/);
const nonnegative = z.number().int().nonnegative();
const positive = z.number().int().positive();
const strings = z.array(z.string());
const reference = z.object({ garden: identifier, id: identifier, revision: revision.nullish() });
const representedReference = reference.extend({ revision });
const representedGardens = z.array(z.object({ garden: identifier, revision }));
const policy = z.object({ id: z.string().min(1), revision: hashRevision });
const scope = z.object({
  schema: z.literal("mindgarden.scope/v1"),
  visibility: z.enum(["public", "organization", "personal", "restricted"]),
  persistence: z.enum(["git-tracked", "machine-local", "encrypted-vault"]),
  execution: z.enum(["networked", "controlled-import", "offline"]),
  publication: z.enum(["publishable", "review-required", "never-exportable"]),
  policy,
});
const review = z.object({
  state: z.enum(["unreviewed", "in-review", "approved", "rejected"]),
  reviewers: z.array(identifier),
  reviewed_at: z.string().nullable(),
  rationale: z.string().nullable(),
});
const sourceCitation = z.object({
  source: reference,
  locator: z.string().min(1),
  content_sha256: digest,
});
const qualifications = z.object({
  epistemic_state: z.string(),
  attribution: z.string(),
  caveats: strings,
  uncertainty: strings,
  contradictions: z.array(reference),
  redactions: z.array(z.object({ source: sourceCitation, rationale: z.string() })).optional(),
});
const selectionReason = z.object({
  term: z.string(),
  score: nonnegative,
  field: z.string().optional(),
  bodyFrequency: nonnegative.optional(),
  title: z.boolean().optional(),
  tag: z.boolean().optional(),
  heading: z.boolean().optional(),
});

const noteSummary = z.object({
  reference: representedReference,
  title: z.string(),
  kind: z.string(),
  record_type: z.enum(["knowledge", "claim"]),
  review,
  scope,
  domains: strings,
  topics: strings,
  tags: strings,
  source_count: nonnegative,
});
const graphEdge = z.object({
  source: z.string(),
  target: z.string(),
  type: z.string(),
  directed: z.boolean(),
  review,
  scope,
});
const gardenOverview = z.object({
  title: z.string(),
  demo: z.boolean(),
  status: z.literal("ready"),
  capabilities: z.object({
    search: z.boolean(),
    graph: z.boolean(),
    backlinks: z.boolean(),
    context: z.boolean(),
    evidence: z.boolean(),
    assistant: z.boolean().optional(),
    booklet: z.boolean().optional(),
  }),
  notes: z.array(noteSummary),
  graph: z.object({ nodes: z.array(noteSummary), edges: z.array(graphEdge) }),
  inputs: representedGardens,
  scope,
  limited: z.boolean(),
});
const noteLink = z.object({ reference: representedReference, title: z.string(), type: z.string(), scope, review });
const noteDetail = z.object({
  note: noteSummary.extend({ content: z.string(), sources: z.array(sourceCitation), qualifications }),
  links: z.array(noteLink.extend({ to: z.string() })),
  backlinks: z.array(noteLink.extend({ from: z.string(), sources: z.array(sourceCitation) })),
  scope,
});
const searchResult = z.object({
  reference: representedReference,
  title: z.string(),
  kind: z.string(),
  review,
  scope,
  sources: z.array(sourceCitation),
  qualifications,
  score: nonnegative,
  selection_reasons: z.array(selectionReason),
  snippet: z.string(),
});
const searchResults = z.object({
  schema: z.literal("mindgarden.search-results/v1"),
  inputs: representedGardens,
  policy,
  scope,
  results: z.array(searchResult),
});
const evidence = sourceCitation.extend({
  schema: z.literal("mindgarden.evidence/v1"),
  trust: z.literal("untrusted-evidence"),
  text: z.string(),
  source_identity: z.string(),
  source_review: review,
  scope,
  origin: z.record(z.string(), z.unknown()),
  lineage: z.array(reference),
  authorized_by: z.array(z.object({ reference: representedReference, review })),
});
const contextPack = z.object({
  schema: z.literal("mindgarden.context/v1"),
  pack: identifier,
  scope,
  policy,
  inputs: representedGardens,
  trust: z.literal("untrusted-evidence"),
  budget: z.object({ max_bytes: positive, max_items: positive, considered_candidates: nonnegative }),
  included: z.array(z.object({
    reference: representedReference,
    review,
    scope,
    qualifications,
    sources: z.array(sourceCitation),
    selection_reason: z.string(),
    selection_score: nonnegative,
    score_contributions: z.array(selectionReason),
    content: z.string(),
  })),
  excluded: z.array(z.object({ reference: representedReference, reason: z.string() })),
});
const connectorSummary = z.object({
  google_drive: z.object({
    state: z.enum(["demo", "captured", "setup-required"]),
    citation_count: nonnegative,
  }),
  local_vault: z.object({
    state: z.enum(["visible-evidence", "no-visible-evidence"]),
    citation_count: nonnegative,
  }),
});

const assistantLens = z.enum(["garden", "finance"]);
const assistantFocus = z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*\/[a-z0-9]+(?:-[a-z0-9]+)*$/).nullable();
const assistantPreview = z.object({
  preview_sha256: digest,
  provider: z.literal("fixture"),
  lens: assistantLens,
  focus: assistantFocus,
  context_bytes: nonnegative,
  scope,
  records: z.array(z.object({
    reference: representedReference, title: z.string(), review, scope, sources: z.array(sourceCitation),
    content: z.string(), caveats: strings, uncertainty: strings,
  })),
});
const assistantCitation = z.object({ type: z.literal("citation"), reference: representedReference, citation: sourceCitation });
const assistantEvent = z.discriminatedUnion("type", [
  z.object({ type: z.literal("start"), provider: z.literal("fixture") }),
  z.object({ type: z.literal("text"), text: z.string() }),
  assistantCitation,
  z.object({ type: z.literal("done") }),
  z.object({ type: z.literal("error"), code: z.string() }),
]);

const bookletMonth = z.literal("2026-01");
const period = z.object({ start: z.string(), end: z.string() });
const bookletPreview = z.object({
  schema: z.literal("mindgarden.monthly-booklet-preview/v1"),
  month: bookletMonth,
  timezone: z.literal("UTC"),
  scope,
  period,
  totals: z.array(z.object({
    month: bookletMonth,
    currency: z.string().regex(/^[A-Z]{3}$/),
    net_movement: z.string(),
    income: z.string(),
    expense: z.string(),
    refund: z.string(),
    transfer: z.string(),
    uncategorized: z.string(),
  })),
  coverage: z.array(z.object({
    account: z.string(),
    observed_first: z.string().nullable(),
    observed_last: z.string().nullable(),
    missing_declared_intervals: z.array(period),
    status: z.string(),
  })),
  limitations: strings,
  review: review.extend({ state: z.literal("approved") }),
  status: z.literal("current"),
  unresolved_transactions: strings,
  questions: strings,
  transactions: z.array(z.object({
    id: identifier,
    date: z.string(),
    account: identifier,
    currency: z.string().regex(/^[A-Z]{3}$/),
    amount: z.string(),
    classification: z.enum(["income", "expense", "refund", "transfer", "uncategorized"]),
    paired_with: z.string().nullable(),
    citation: z.string().regex(/^E[0-9]{2,}$/),
  })),
  evidence: z.array(sourceCitation),
  plan_sha256: digest,
  pdf_sha256: digest,
});
const bookletEvidence = bookletPreview.extend({
  schema: z.literal("mindgarden.monthly-booklet-evidence/v1"),
});

export type BookletMonth = z.infer<typeof bookletMonth>;
export type BookletPreview = z.infer<typeof bookletPreview>;
export type BookletFormat = "pdf" | "evidence";

export type AssistantLens = z.infer<typeof assistantLens>;
export type AssistantInput = { lens: AssistantLens; question: string; focus: string | null };
export type AssistantPreview = z.infer<typeof assistantPreview>;
export type AssistantCitation = z.infer<typeof assistantCitation>;
export type AssistantDelta = Extract<z.infer<typeof assistantEvent>, { type: "text" | "citation" }>;

export type ArtifactReference = z.infer<typeof reference>;
export type SourceCitation = z.infer<typeof sourceCitation>;
export type Scope = z.infer<typeof scope>;
export type Review = z.infer<typeof review>;
export type NoteSummary = z.infer<typeof noteSummary>;
export type GardenOverview = z.infer<typeof gardenOverview>;
export type GraphEdge = z.infer<typeof graphEdge>;
export type NoteDetail = z.infer<typeof noteDetail>;
export type SearchResult = z.infer<typeof searchResult>;
export type SearchResults = z.infer<typeof searchResults>;
export type Evidence = z.infer<typeof evidence>;
export type ContextPack = z.infer<typeof contextPack>;
export type ConnectorSummary = z.infer<typeof connectorSummary>;
export type ContextResponse = {
  pack: ContextPack;
  bytes: Uint8Array<ArrayBuffer>;
  text: string;
};

const accessKey = "mindgarden-access";
const accessFormat = /^[a-zA-Z0-9_-]{43}$/;
export const QUERY_MAX_LENGTH = 256;

export function captureGardenAccess(): string | null {
  const address = new URL(window.location.href);
  const fragments = new URLSearchParams(address.hash.slice(1));
  if (!fragments.has("access")) {
    try {
      const saved = window.sessionStorage.getItem(accessKey);
      return saved && accessFormat.test(saved) ? saved : null;
    } catch {
      return null;
    }
  }

  const entries = fragments.getAll("access");
  const access = entries.length === 1 && accessFormat.test(entries[0]) ? entries[0] : null;
  address.hash = "";
  window.history.replaceState(null, "", address);
  try {
    if (access) window.sessionStorage.setItem(accessKey, access);
    else window.sessionStorage.removeItem(accessKey);
  } catch {
    // Opening the original launch link also works with tab storage disabled.
  }
  return access;
}

export function referenceKey(value: ArtifactReference | string): string {
  return typeof value === "string" ? value : `${value.garden}/${value.id}`;
}

const diagnostics = {
  WEB_ACCESS: "Open the complete visit link printed by Mindgarden.",
  WEB_ORIGIN: "Open the local address printed by Mindgarden.",
  WEB_QUERY: "Supply a query within the supported length.",
  WEB_NOT_FOUND: "This item is unavailable in the authorized view.",
  WEB_UNAVAILABLE: "The explicit local view could not be verified.",
  SESSION_EXPIRED: "Restart Mindgarden with an active local session.",
  SESSION_REVOKED: "Restart Mindgarden with an active local session.",
  SESSION_STALE: "Restart Mindgarden with the current local session.",
  SESSION_CONFIGURATION: "Restart Mindgarden with the current local session.",
  SESSION_REVISION: "The garden changed. Refresh the local session and restart Mindgarden.",
  WRITE_LOCKED: "Check the garden for a pending write before reopening the visit.",
  QUERY_INTEGRITY: "The authorized records could not be verified. Check the garden locally.",
  QUERY_BUDGET: "This result exceeds the session budget. Try a narrower selection.",
  CONTEXT_BUDGET: "This result exceeds the session budget. Try a narrower selection.",
  PROJECTION_DENIED: "The explicit session does not allow this view.",
  EVIDENCE_FORMAT: "This evidence selection has no text preview.",
  CONNECTION: "Could not reach the local garden. Check that Mindgarden is running.",
  INVALID_RESPONSE: "Mindgarden returned an incompatible response. Check the local app version.",
  ASSISTANT_INVALID: "Enter a question of up to 256 characters and choose a supported lens.",
  ASSISTANT_FOCUS: "The selected note is unavailable for this lens and session.",
  ASSISTANT_APPROVAL: "The approved context changed. Preview it again before running.",
  ASSISTANT_UNAVAILABLE: "The fictional assistant is unavailable in this session.",
  BOOKLET_REVIEW: "The approved booklet changed. Preview and review it again.",
  BOOKLET_UNAVAILABLE: "The fictional booklet is unavailable in this session.",
} as const;

type DiagnosticCode = keyof typeof diagnostics;

export class GardenApiError extends Error {
  constructor(public readonly code: DiagnosticCode, public readonly status: number) {
    super(diagnostics[code]);
    this.name = "GardenApiError";
  }
}

const errorEnvelope = z.object({ error: z.object({ code: z.string() }) });

function remoteError(value: unknown, status: number): GardenApiError {
  const parsed = errorEnvelope.safeParse(value);
  const code = parsed.success ? parsed.data.error.code : "WEB_UNAVAILABLE";
  return new GardenApiError(Object.hasOwn(diagnostics, code) ? code as DiagnosticCode : "WEB_UNAVAILABLE", status);
}

type Endpoint = "garden" | "search" | "note" | "evidence" | "context" | "connectors"
  | "assistant/preview" | "assistant/run" | "booklet/preview" | "booklet/artifact";

async function localFetch(
  access: string | null,
  endpoint: Endpoint,
  parameters: Record<string, string>,
  signal?: AbortSignal,
  body?: object,
  accept = "application/json",
) {
  signal?.throwIfAborted();
  if (!access || !accessFormat.test(access)) throw new GardenApiError("WEB_ACCESS", 0);
  const query = new URLSearchParams(parameters).toString();
  const headers: Record<string, string> = { Accept: accept, Authorization: `Bearer ${access}` };
  if (body) headers["Content-Type"] = "application/json";
  try {
    return await fetch(`/api/${endpoint}${query ? `?${query}` : ""}`, {
      method: body ? "POST" : "GET",
      headers,
      ...(body ? { body: JSON.stringify(body) } : {}),
      cache: "no-store",
      credentials: "omit",
      mode: "same-origin",
      redirect: "error",
      referrerPolicy: "no-referrer",
      signal,
    });
  } catch {
    signal?.throwIfAborted();
    throw new GardenApiError("CONNECTION", 0);
  }
}

function mediaType(response: Response) {
  return response.headers.get("content-type")?.split(";", 1)[0].trim().toLowerCase();
}

async function jsonResponse(response: Response, signal?: AbortSignal) {
  if (mediaType(response) !== "application/json") {
    throw new GardenApiError(response.ok ? "INVALID_RESPONSE" : "WEB_UNAVAILABLE", response.status);
  }
  let bytes: Uint8Array<ArrayBuffer>;
  let text: string;
  let value: unknown;
  try {
    bytes = new Uint8Array(await response.arrayBuffer());
    text = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes);
    value = JSON.parse(text);
  } catch {
    signal?.throwIfAborted();
    throw new GardenApiError("INVALID_RESPONSE", response.status);
  }
  signal?.throwIfAborted();
  if (!response.ok) throw remoteError(value, response.status);
  return { bytes, text, value, status: response.status };
}

async function request(
  access: string | null, endpoint: Endpoint, parameters: Record<string, string>, signal?: AbortSignal, body?: object,
) {
  return jsonResponse(await localFetch(access, endpoint, parameters, signal, body), signal);
}

async function readAssistantStream(response: Response, onDelta: (delta: AssistantDelta) => void, signal?: AbortSignal) {
  if (!response.ok) await jsonResponse(response, signal);
  if (mediaType(response) !== "application/x-ndjson" || !response.body) {
    throw new GardenApiError("INVALID_RESPONSE", response.status);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8", { fatal: true });
  let buffer = "";
  let received = 0;
  let started = false;
  let finished = false;
  try {
    while (true) {
      const chunk = await reader.read();
      signal?.throwIfAborted();
      if (chunk.done) break;
      received += chunk.value.byteLength;
      if (received > 128 * 1024) throw new GardenApiError("QUERY_BUDGET", response.status);
      buffer += decoder.decode(chunk.value, { stream: true });
      let newline = buffer.indexOf("\n");
      while (newline >= 0) {
        const event = assistantEvent.parse(JSON.parse(buffer.slice(0, newline)));
        buffer = buffer.slice(newline + 1);
        if (finished || (!started && event.type !== "start")) throw new GardenApiError("INVALID_RESPONSE", response.status);
        switch (event.type) {
          case "start":
            if (started) throw new GardenApiError("INVALID_RESPONSE", response.status);
            started = true;
            break;
          case "done":
            finished = true;
            break;
          case "error":
            throw remoteError({ error: { code: event.code } }, response.status);
          default:
            onDelta(event);
        }
        newline = buffer.indexOf("\n");
      }
    }
    if (buffer || decoder.decode() || !finished) throw new GardenApiError("INVALID_RESPONSE", response.status);
  } catch (error) {
    signal?.throwIfAborted();
    if (error instanceof GardenApiError) throw error;
    throw new GardenApiError("INVALID_RESPONSE", response.status);
  } finally {
    await reader.cancel().catch(() => {});
    reader.releaseLock();
  }
}

function readValue<Schema extends z.ZodType>(schema: Schema, response: { value: unknown; status: number }): z.output<Schema> {
  const result = schema.safeParse(response.value);
  if (!result.success) throw new GardenApiError("INVALID_RESPONSE", response.status);
  return result.data;
}

export function createGardenClient(access: string | null) {
  return {
    async garden(signal?: AbortSignal): Promise<GardenOverview> {
      return readValue(gardenOverview, await request(access, "garden", {}, signal));
    },
    async connectors(signal?: AbortSignal): Promise<ConnectorSummary> {
      return readValue(connectorSummary, await request(access, "connectors", {}, signal));
    },
    async search(query: string, signal?: AbortSignal): Promise<SearchResults> {
      return readValue(searchResults, await request(access, "search", { q: query }, signal));
    },
    async note(ref: ArtifactReference | string, signal?: AbortSignal): Promise<NoteDetail> {
      return readValue(noteDetail, await request(access, "note", { ref: referenceKey(ref) }, signal));
    },
    async evidence(ref: ArtifactReference | string, citation: number, signal?: AbortSignal): Promise<Evidence> {
      const parameters = { ref: referenceKey(ref), citation: String(citation) };
      return readValue(evidence, await request(access, "evidence", parameters, signal));
    },
    async assistantPreview(input: AssistantInput, signal?: AbortSignal): Promise<AssistantPreview> {
      return readValue(assistantPreview, await request(access, "assistant/preview", {}, signal, input));
    },
    async assistantRun(
      input: AssistantInput, previewSha256: string, onDelta: (delta: AssistantDelta) => void, signal?: AbortSignal,
    ) {
      const response = await localFetch(access, "assistant/run", {}, signal, {
        ...input, preview_sha256: previewSha256,
      }, "application/x-ndjson");
      await readAssistantStream(response, onDelta, signal);
    },
    async bookletPreview(month: BookletMonth, signal?: AbortSignal): Promise<BookletPreview> {
      return readValue(bookletPreview, await request(access, "booklet/preview", {}, signal, { month }));
    },
    async bookletArtifact(preview: BookletPreview, format: BookletFormat, signal?: AbortSignal) {
      const expectedType = format === "pdf" ? "application/pdf" : "application/json";
      const response = await localFetch(access, "booklet/artifact", {}, signal, {
        month: preview.month, plan_sha256: preview.plan_sha256, format,
      }, expectedType);
      if (!response.ok) await jsonResponse(response, signal);
      if (mediaType(response) !== expectedType) throw new GardenApiError("INVALID_RESPONSE", response.status);
      try {
        const bytes = new Uint8Array(await response.arrayBuffer());
        signal?.throwIfAborted();
        if (!bytes.length || bytes.length > 1024 * 1024) throw new GardenApiError("QUERY_BUDGET", response.status);
        if (format === "pdf") {
          const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
          const hex = Array.from(digest, (value) => value.toString(16).padStart(2, "0")).join("");
          if (hex !== preview.pdf_sha256 || new TextDecoder().decode(bytes.subarray(0, 5)) !== "%PDF-") {
            throw new GardenApiError("INVALID_RESPONSE", response.status);
          }
        } else {
          const json = bookletEvidence.parse(JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes)));
          if (json.plan_sha256 !== preview.plan_sha256 || json.pdf_sha256 !== preview.pdf_sha256) {
            throw new GardenApiError("INVALID_RESPONSE", response.status);
          }
        }
        signal?.throwIfAborted();
        return new Blob([bytes], { type: expectedType });
      } catch (error) {
        signal?.throwIfAborted();
        if (error instanceof GardenApiError) throw error;
        throw new GardenApiError("INVALID_RESPONSE", response.status);
      }
    },
    async context(query: string, signal?: AbortSignal): Promise<ContextResponse> {
      const response = await request(access, "context", { q: query }, signal);
      const pack = readValue(contextPack, response);
      if (response.bytes.length > pack.budget.max_bytes || pack.included.length > pack.budget.max_items) {
        throw new GardenApiError("INVALID_RESPONSE", response.status);
      }
      return { pack, bytes: response.bytes, text: response.text };
    },
  };
}

export type GardenClient = ReturnType<typeof createGardenClient>;
