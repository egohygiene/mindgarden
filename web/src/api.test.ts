import { afterEach, describe, expect, it, vi } from "vitest";
import { captureGardenAccess, createGardenClient, referenceKey } from "./api";

const access = "a".repeat(43);
const revision = `sha256:${"1".repeat(64)}`;
const reference = { garden: "synthetic-garden", id: "example-note", revision };
const policy = { id: "mindgarden-local-single-user/v1", revision };
const scope = {
  schema: "mindgarden.scope/v1",
  visibility: "personal",
  persistence: "machine-local",
  execution: "offline",
  publication: "never-exportable",
  policy,
};

function jsonResponse(body: string, status = 200): Response {
  return new Response(body, { status, headers: { "Content-Type": "application/json; charset=utf-8" } });
}

function pretendTab(fragment: string, saved?: string) {
  const values = new Map(saved ? [["mindgarden-access", saved]] : []);
  const tab = {
    location: { href: `http://127.0.0.1:8765/${fragment}` },
    history: {
      replaceState(_state: unknown, _title: string, address: URL) {
        tab.location.href = address.href;
      },
    },
    sessionStorage: {
      getItem: (key: string) => values.get(key),
      setItem: (key: string, value: string) => values.set(key, value),
      removeItem: (key: string) => values.delete(key),
    },
  };
  vi.stubGlobal("window", tab);
  return tab;
}

afterEach(() => vi.unstubAllGlobals());

describe("local browser launch authority", () => {
  it("consumes the secret fragment and reads it again only from tab storage", () => {
    const tab = pretendTab(`#access=${access}`);
    expect(captureGardenAccess()).toBe(access);
    expect(tab.location.href).toBe("http://127.0.0.1:8765/");
    expect(captureGardenAccess()).toBe(access);
    pretendTab("");
    expect(captureGardenAccess()).toBeNull();
  });

  it("strips malformed fragments and discards stale access when a new link is malformed", () => {
    const tab = pretendTab(`#access=broken&access=${access}`, access);
    expect(captureGardenAccess()).toBeNull();
    expect(tab.location.href).toBe("http://127.0.0.1:8765/");
    expect(captureGardenAccess()).toBeNull();
  });

  it("works for the current launch if tab storage rejects writes", () => {
    const tab = pretendTab(`#access=${access}`);
    tab.sessionStorage.setItem = () => { throw new Error("Storage unavailable"); };
    expect(captureGardenAccess()).toBe(access);
    expect(tab.location.href).not.toContain(access);
  });
});

describe("typed read client", () => {
  it("asks for bounded connector evidence without including paths or token parameters", async () => {
    const body = {
      google_drive: { state: "captured", citation_count: 2 },
      local_vault: { state: "visible-evidence", citation_count: 3 },
    };
    const fetch = vi.fn().mockResolvedValueOnce(jsonResponse(JSON.stringify(body)));
    vi.stubGlobal("fetch", fetch);
    await expect(createGardenClient(access).connectors()).resolves.toEqual(body);
    expect(fetch).toHaveBeenCalledWith("/api/connectors", expect.objectContaining({
      cache: "no-store",
      credentials: "omit",
      headers: { Accept: "application/json", Authorization: `Bearer ${access}` },
    }));
  });

  it("rejects a status that claims a live Drive connection", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(jsonResponse(JSON.stringify({
      google_drive: { state: "connected", citation_count: 0 },
      local_vault: { state: "no-visible-evidence", citation_count: 0 },
    }))));
    await expect(createGardenClient(access).connectors()).rejects.toMatchObject({ code: "INVALID_RESPONSE" });
  });

  it("reads the fixed local diagnostics envelope with the visit bearer", async () => {
    const event = {
      id: 1, source: "server", provider: "chatgpt", operation: "check", outcome: "attention",
      code: "MODEL_CATALOG_EMPTY", at_ms: 1_800_000_000_000, duration_ms: 18,
    };
    const body = { capacity: 80, events: [event] };
    const fetch = vi.fn().mockResolvedValueOnce(jsonResponse(JSON.stringify(body)));
    vi.stubGlobal("fetch", fetch);
    await expect(createGardenClient(access).diagnostics()).resolves.toEqual(body);
    expect(fetch).toHaveBeenCalledWith("/api/diagnostics", expect.objectContaining({
      cache: "no-store",
      credentials: "omit",
      headers: { Accept: "application/json", Authorization: `Bearer ${access}` },
    }));
  });

  it("rejects unexpected diagnostic fields and an oversized history", async () => {
    const event = {
      id: 1, source: "server", provider: "studio", operation: "sources", outcome: "ok",
      code: "SOURCES_OK", at_ms: 1_800_000_000_000, duration_ms: 8,
    };
    const malformed = [
      { capacity: 80, events: [{ ...event, message: "synthetic-private-canary" }] },
      { capacity: 80, events: Array.from({ length: 81 }, () => event) },
    ];
    for (const body of malformed) {
      vi.stubGlobal("fetch", vi.fn().mockResolvedValueOnce(jsonResponse(JSON.stringify(body))));
      await expect(createGardenClient(access).diagnostics()).rejects.toMatchObject({ code: "INVALID_RESPONSE" });
    }
  });

  it("keeps the exact context bytes while sending the bearer only in the header", async () => {
    const qualification = {
      epistemic_state: "unverified", attribution: "quoted", caveats: [], uncertainty: [], contradictions: [],
    };
    const serialized = JSON.stringify({
      schema: "mindgarden.context/v1", pack: "browser-context", trust: "untrusted-evidence", scope, policy,
      inputs: [{ garden: reference.garden, revision }],
      budget: { max_bytes: 16384, max_items: 5, considered_candidates: 1 },
      included: [{
        reference, review: { state: "approved", reviewers: [], reviewed_at: null, rationale: null },
        content: "Café fictional note.", selection_reason: "lexical-query", selection_score: 1,
        score_contributions: [{ term: "caf", score: 1, bodyFrequency: 1, title: false, tag: false, heading: false }],
        sources: [], scope, qualifications: qualification,
      }],
      excluded: [],
    }, null, 3) + "\n";
    const fetchMock = vi.fn(async () => jsonResponse(serialized));
    vi.stubGlobal("fetch", fetchMock);
    const signal = new AbortController().signal;

    const result = await createGardenClient(access).context("cafés? & notes", signal);
    expect(result.text).toBe(serialized);
    expect(result.bytes).toEqual(new TextEncoder().encode(serialized));
    expect(result.pack.included[0].reference).toEqual(reference);
    expect(fetchMock).toHaveBeenCalledExactlyOnceWith("/api/context?q=caf%C3%A9s%3F+%26+notes", {
      method: "GET", headers: { Accept: "application/json", Authorization: `Bearer ${access}` },
      mode: "same-origin", credentials: "omit", redirect: "error", cache: "no-store",
      referrerPolicy: "no-referrer", signal,
    });
    expect(referenceKey(reference)).toBe("synthetic-garden/example-note");
  });

  it("sanitizes unknown or malformed responses", async () => {
    const privateText = "never surface this fictional canary";
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse(JSON.stringify({ error: { code: privateText, message: privateText } }), 403))
      .mockResolvedValueOnce(jsonResponse(JSON.stringify({ error: { code: "SESSION_REVOKED", message: privateText } }), 403))
      .mockResolvedValueOnce(jsonResponse(JSON.stringify({ content: privateText })))
      .mockRejectedValueOnce(new TypeError(privateText));
    vi.stubGlobal("fetch", fetchMock);
    const client = createGardenClient(access);
    for (const [code, status] of [["WEB_UNAVAILABLE", 403], ["SESSION_REVOKED", 403], ["INVALID_RESPONSE", 200], ["CONNECTION", 0]]) {
      const read = client.garden();
      await expect(read).rejects.toMatchObject({ code, status });
      await expect(read).rejects.not.toThrow(privateText);
    }
  });

  it("skips calls with no access and propagates aborts", async () => {
    const fetchMock = vi.fn(async (_path: string, options: RequestInit) => {
      return new Promise<Response>((_, reject) => {
        options.signal?.addEventListener("abort", () => reject(options.signal?.reason), { once: true });
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    await expect(createGardenClient(null).garden()).rejects.toMatchObject({ code: "WEB_ACCESS" });
    expect(fetchMock).not.toHaveBeenCalled();
    const controller = new AbortController();
    const request = createGardenClient(access).evidence(reference, 0, controller.signal);
    controller.abort();
    await expect(request).rejects.toMatchObject({ name: "AbortError" });
    expect(fetchMock.mock.calls[0][0]).toBe("/api/evidence?ref=synthetic-garden%2Fexample-note&citation=0");
  });
});
