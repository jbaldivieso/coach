import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createPinia, setActivePinia } from "pinia";

vi.mock("@/api/client", () => ({
  api: { get: vi.fn(), post: vi.fn() },
}));

import { api } from "@/api/client";

describe("router guard", () => {
  const assign = vi.fn();

  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
    localStorage.clear();
    setActivePinia(createPinia());
    vi.spyOn(window.location, "assign").mockImplementation(assign);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  function signedIn(me: { data: unknown; error: string | null }) {
    localStorage.setItem("coach.user", JSON.stringify({ id: 1, username: "jon" }));
    vi.mocked(api.get).mockResolvedValue(me);
  }

  it("keeps ?next= on the login page when a remembered session has expired", async () => {
    localStorage.setItem("coach.user", JSON.stringify({ id: 1, username: "jon" }));
    vi.mocked(api.get).mockResolvedValue({ data: null, error: "Unauthorized" });
    const { default: router } = await import("./index");

    await router.push("/login?next=%2Foauth%2Fauthorize%2F%3Fstate%3Dxyz");

    expect(router.currentRoute.value.name).toBe("login");
    expect(router.currentRoute.value.query.next).toBe("/oauth/authorize/?state=xyz");
  });

  it("sends a signed-in user on to the OAuth page in ?next=", async () => {
    signedIn({ data: { id: 1, username: "jon" }, error: null });
    const { default: router } = await import("./index");

    await router.push("/login?next=%2Foauth%2Fauthorize%2F%3Fstate%3Dxyz");

    expect(assign).toHaveBeenCalledWith("/oauth/authorize/?state=xyz");
  });

  it("sends a signed-in user on to an app path in ?next=", async () => {
    signedIn({ data: { id: 1, username: "jon" }, error: null });
    const { default: router } = await import("./index");

    await router.push("/login?next=%2Fsearch");

    expect(router.currentRoute.value.name).toBe("search");
  });

  it("shows the login form when the server can't confirm the session", async () => {
    signedIn({ data: null, error: "Server error" });
    const { default: router } = await import("./index");

    await router.push("/login?next=%2Foauth%2Fauthorize%2F");

    expect(router.currentRoute.value.name).toBe("login");
    expect(assign).not.toHaveBeenCalled();
  });
});
