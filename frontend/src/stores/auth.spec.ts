import { describe, it, expect, beforeEach, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useAuthStore } from "./auth";

// Mock the api client
vi.mock("@/api/client", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    fetchCsrfToken: vi.fn(),
  },
}));

import { api } from "@/api/client";

describe("Auth Store", () => {
  beforeEach(() => {
    localStorage.clear();
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("starts with no user", () => {
    const store = useAuthStore();
    expect(store.user).toBeNull();
    expect(store.isAuthenticated).toBe(false);
  });

  it("sets user on successful login", async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: { id: 1, username: "testuser" },
      error: null,
    });

    const store = useAuthStore();
    const success = await store.login("testuser", "password");

    expect(success).toBe(true);
    expect(store.user).toEqual({ id: 1, username: "testuser" });
    expect(store.isAuthenticated).toBe(true);
  });

  it("sets error on failed login", async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: null,
      error: "Invalid credentials",
    });

    const store = useAuthStore();
    const success = await store.login("testuser", "wrongpassword");

    expect(success).toBe(false);
    expect(store.user).toBeNull();
    expect(store.error).toBe("Invalid credentials");
  });

  it("clears user on successful logout", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: {}, error: null });

    const store = useAuthStore();
    store.user = { id: 1, username: "testuser" };

    const success = await store.logout();

    expect(success).toBe(true);
    expect(api.fetchCsrfToken).toHaveBeenCalled();
    expect(store.user).toBeNull();
    expect(store.isAuthenticated).toBe(false);
  });

  it("sets error on failed logout", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: null, error: "CSRF failed" });

    const store = useAuthStore();
    store.user = { id: 1, username: "testuser" };

    const success = await store.logout();

    expect(success).toBe(false);
    expect(store.error).toBe("CSRF failed");
    expect(store.user).toEqual({ id: 1, username: "testuser" });
  });

  it("checks auth status and sets user if authenticated", async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: { id: 1, username: "testuser" },
      error: null,
    });

    const store = useAuthStore();
    await store.checkAuth();

    expect(store.user).toEqual({ id: 1, username: "testuser" });
  });

  it("checks auth status and clears user if not authenticated", async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: null,
      error: "Unauthorized",
    });

    const store = useAuthStore();
    store.user = { id: 1, username: "testuser" };

    await store.checkAuth();

    expect(store.user).toBeNull();
  });

  it("starts with the user remembered from the last launch, unverified", () => {
    localStorage.setItem("coach.user", JSON.stringify({ id: 1, username: "testuser" }));

    const store = useAuthStore();

    expect(store.user).toEqual({ id: 1, username: "testuser" });
    expect(store.isAuthenticated).toBe(true);
    expect(store.verified).toBe(false);
  });

  it("remembers the user on login and forgets them on logout", async () => {
    vi.mocked(api.post).mockResolvedValue({
      data: { id: 1, username: "testuser" },
      error: null,
    });

    const store = useAuthStore();
    await store.login("testuser", "password");

    expect(JSON.parse(localStorage.getItem("coach.user")!)).toEqual({ id: 1, username: "testuser" });
    expect(store.verified).toBe(true);

    await store.logout();

    expect(localStorage.getItem("coach.user")).toBeNull();
  });

  it("forgets a remembered user when the server says the session is gone", async () => {
    localStorage.setItem("coach.user", JSON.stringify({ id: 1, username: "testuser" }));
    vi.mocked(api.get).mockResolvedValue({ data: null, error: "Unauthorized" });

    const store = useAuthStore();
    await store.checkAuth();

    expect(store.user).toBeNull();
    expect(store.verified).toBe(true);
    expect(localStorage.getItem("coach.user")).toBeNull();
  });

  it("keeps a remembered user when the server can't be reached", async () => {
    localStorage.setItem("coach.user", JSON.stringify({ id: 1, username: "testuser" }));
    vi.mocked(api.get).mockRejectedValue(new TypeError("Load failed"));

    const store = useAuthStore();
    await store.checkAuth();

    expect(store.user).toEqual({ id: 1, username: "testuser" });
    expect(store.verified).toBe(false);
    expect(store.loading).toBe(false);
  });

  it("keeps a remembered user when the server errors", async () => {
    localStorage.setItem("coach.user", JSON.stringify({ id: 1, username: "testuser" }));
    vi.mocked(api.get).mockResolvedValue({ data: null, error: "Request failed" });

    const store = useAuthStore();
    await store.checkAuth();

    expect(store.user).toEqual({ id: 1, username: "testuser" });
    expect(store.verified).toBe(false);
  });
});
