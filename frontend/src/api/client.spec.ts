import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { api } from "./client";

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function setCsrfCookie(value: string | null) {
  document.cookie = value === null ? "csrftoken=; expires=Thu, 01 Jan 1970 00:00:00 GMT" : `csrftoken=${value}`;
}

function sentToken(call: unknown[]): string | undefined {
  return ((call[1] as RequestInit).headers as Record<string, string>)["X-CSRFToken"];
}

describe("ApiClient", () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    vi.stubGlobal("fetch", fetchMock);
    setCsrfCookie(null);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("writes with the token from the cookie, in one request", async () => {
    setCsrfCookie("from-cookie");
    fetchMock.mockResolvedValue(json({ id: 1 }));

    const response = await api.put("/api/lifting/exercises/1/", { sets: [] });

    expect(response).toEqual({ data: { id: 1 }, error: null });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(sentToken(fetchMock.mock.calls[0]!)).toBe("from-cookie");
  });

  it("reads the cookie again for each write, so a rotated token is picked up", async () => {
    fetchMock.mockImplementation(async () => json({}));
    setCsrfCookie("before-login");
    await api.post("/api/accounts/login/", {});
    setCsrfCookie("after-login");
    await api.post("/api/lifting/sessions/", {});

    expect(fetchMock.mock.calls.map(sentToken)).toEqual(["before-login", "after-login"]);
  });

  it("asks the server for a token when there's no cookie yet", async () => {
    fetchMock.mockImplementation(async (url: string) =>
      url === "/api/accounts/csrf/" ? json({ csrf_token: "from-server" }) : json({}),
    );

    await api.post("/api/accounts/login/", {});

    expect(fetchMock.mock.calls.map((call) => call[0])).toEqual(["/api/accounts/csrf/", "/api/accounts/login/"]);
    expect(sentToken(fetchMock.mock.calls[1]!)).toBe("from-server");
  });

  it("shares one token request between writes that land together", async () => {
    fetchMock.mockImplementation(async (url: string) =>
      url === "/api/accounts/csrf/" ? json({ csrf_token: "from-server" }) : json({}),
    );

    await Promise.all([api.put("/api/lifting/exercises/1/", {}), api.put("/api/lifting/exercises/2/", {})]);

    expect(fetchMock.mock.calls.filter((call) => call[0] === "/api/accounts/csrf/")).toHaveLength(1);
  });

  it("gets a new token and sends once more when a write is refused", async () => {
    setCsrfCookie("stale");
    fetchMock
      .mockResolvedValueOnce(json({ detail: "CSRF check Failed" }, 403))
      .mockResolvedValueOnce(json({ csrf_token: "new" }))
      .mockResolvedValueOnce(json({ id: 1 }));

    const response = await api.put("/api/lifting/exercises/1/", {});

    expect(response.data).toEqual({ id: 1 });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(sentToken(fetchMock.mock.calls[2]!)).toBe("new");
  });

  it("gives up after one more try", async () => {
    setCsrfCookie("stale");
    fetchMock.mockImplementation(async (url: string) =>
      url === "/api/accounts/csrf/" ? json({ csrf_token: "new" }) : json({ detail: "Forbidden" }, 403),
    );

    const response = await api.put("/api/lifting/exercises/1/", {});

    expect(response).toEqual({ data: null, error: "Request failed" });
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("doesn't send a token with reads", async () => {
    fetchMock.mockResolvedValue(json([]));

    await api.get("/api/lifting/sessions/open/");

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(sentToken(fetchMock.mock.calls[0]!)).toBeUndefined();
  });

  it("reports a failure instead of throwing when the network is down", async () => {
    setCsrfCookie("from-cookie");
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));

    await expect(api.put("/api/lifting/exercises/1/", {})).resolves.toEqual({
      data: null,
      error: "Couldn't reach the server. Check your connection.",
    });
    await expect(api.get("/api/accounts/me/")).resolves.toMatchObject({ data: null });
  });

  it("reports a failure when the token request itself can't get through", async () => {
    fetchMock.mockRejectedValue(new TypeError("Failed to fetch"));

    const response = await api.post("/api/lifting/sessions/", {});

    expect(response.data).toBeNull();
    expect(response.error).toBe("Couldn't reach the server. Check your connection.");
  });
});
