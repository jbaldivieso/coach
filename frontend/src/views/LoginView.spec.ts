import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createRouter, createMemoryHistory } from "vue-router";
import { createPinia, setActivePinia } from "pinia";
import LoginView from "./LoginView.vue";

vi.mock("@/api/client", () => ({
  api: { get: vi.fn(), post: vi.fn() },
}));

import { api } from "@/api/client";

const placeholder = { template: "<div/>" };

async function logInAt(url: string) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: placeholder },
      { path: "/history", name: "history", component: placeholder },
      { path: "/login", name: "login", component: LoginView },
    ],
  });
  await router.push(url);
  await router.isReady();
  const wrapper = mount(LoginView, { global: { plugins: [router] } });
  await wrapper.find("#username").setValue("jon");
  await wrapper.find("#password").setValue("secret");
  await wrapper.find("form").trigger("submit");
  await flushPromises();
  return router;
}

describe("LoginView", () => {
  const assign = vi.fn();

  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.mocked(api.post).mockResolvedValue({ data: { id: 1, username: "jon" }, error: null });
    vi.stubGlobal("location", { ...window.location, assign });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("goes home after logging in", async () => {
    const router = await logInAt("/login");
    expect(router.currentRoute.value.name).toBe("home");
    expect(assign).not.toHaveBeenCalled();
  });

  it("returns to an app path from ?next=", async () => {
    const router = await logInAt("/login?next=%2Fhistory%3Fq%3Dx");
    expect(router.currentRoute.value.fullPath).toBe("/history?q=x");
    expect(assign).not.toHaveBeenCalled();
  });

  it("loads OAuth pages from Django with a full page load", async () => {
    const next = "/oauth/authorize/?client_id=abc&state=xyz";
    const router = await logInAt(`/login?next=${encodeURIComponent(next)}`);
    expect(assign).toHaveBeenCalledWith(next);
    expect(router.currentRoute.value.name).toBe("login");
  });

  it.each(["//evil.example/x", "/\\evil.example", "https://evil.example/", "history"])(
    "ignores a next that isn't a same-origin path: %s",
    async (next) => {
      const router = await logInAt(`/login?next=${encodeURIComponent(next)}`);
      expect(router.currentRoute.value.name).toBe("home");
      expect(assign).not.toHaveBeenCalled();
    },
  );

  it("stays put when the login fails", async () => {
    vi.mocked(api.post).mockResolvedValue({ data: null, error: "Invalid credentials" });
    const router = await logInAt("/login?next=%2Fhistory");
    expect(router.currentRoute.value.name).toBe("login");
  });
});
