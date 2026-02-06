import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createRouter, createMemoryHistory } from "vue-router";
import SessionDetailView from "./SessionDetailView.vue";
import type { Session } from "@/types/lifting";

// Mock the API client
vi.mock("@/api/client", () => ({
  api: {
    get: vi.fn(),
    delete: vi.fn(),
    fetchCsrfToken: vi.fn(),
  },
}));

import { api } from "@/api/client";

const mockSession: Session = {
  id: 1,
  title: "Upper A",
  date: "2024-01-15",
  session_type: "volume",
  comments: "Good session",
  exercises: [
    {
      id: 1,
      title: "Bench Press",
      sets: [
        { weight: 135, reps: 10 },
        { weight: 135, reps: 8 },
      ],
      rest_seconds: 90,
      comments: "Felt strong",
      position: 0,
    },
    {
      id: 2,
      title: "Pull-ups",
      sets: [
        { weight: null, reps: 10 },
        { weight: null, reps: 8 },
      ],
      rest_seconds: 120,
      comments: "",
      position: 1,
    },
  ],
};

// Create a mock router
function createMockRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: { template: "<div/>" } },
      {
        path: "/session/:id",
        name: "session-detail",
        component: SessionDetailView,
      },
      {
        path: "/sessions/:id/edit",
        name: "edit-session",
        component: { template: "<div/>" },
      },
      {
        path: "/sessions/:id/copy",
        name: "copy-session",
        component: { template: "<div/>" },
      },
    ],
  });
}

describe("SessionDetailView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  async function mountComponent(sessionId: number = 1) {
    const router = createMockRouter();
    await router.push({ name: "session-detail", params: { id: sessionId } });
    await router.isReady();

    return mount(SessionDetailView, {
      global: {
        plugins: [router],
      },
    });
  }

  it("shows loading state initially", async () => {
    // Make API hang
    vi.mocked(api.get).mockImplementation(
      () => new Promise(() => {}), // Never resolves
    );

    const wrapper = await mountComponent();

    expect(wrapper.find(".loader").exists()).toBe(true);
    expect(wrapper.text()).toContain("Loading");
  });

  it("fetches session on mount", async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: mockSession,
      error: null,
    });

    await mountComponent(1);
    await flushPromises();

    expect(api.get).toHaveBeenCalledWith("/api/lifting/sessions/1/");
  });

  it("displays session title, date, type, and comments", async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: mockSession,
      error: null,
    });

    const wrapper = await mountComponent();
    await flushPromises();

    expect(wrapper.text()).toContain("Upper A");
    expect(wrapper.text()).toContain("2024-01-15");
    expect(wrapper.text()).toContain("Volume");
    expect(wrapper.text()).toContain("Good session");
  });

  it("displays exercises with sets, rest time, and comments", async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: mockSession,
      error: null,
    });

    const wrapper = await mountComponent();
    await flushPromises();

    // Exercise titles
    expect(wrapper.text()).toContain("Bench Press");
    expect(wrapper.text()).toContain("Pull-ups");

    // Sets displayed inline
    expect(wrapper.text()).toContain("135 lbs x 10");
    expect(wrapper.text()).toContain("135 lbs x 8");
    expect(wrapper.text()).toContain("bodyweight x 10");
    expect(wrapper.text()).toContain("bodyweight x 8");

    // Rest times (formatted as "1m 30s" and "2m")
    expect(wrapper.text()).toContain("1m 30s");
    expect(wrapper.text()).toContain("2m");

    // Exercise comments
    expect(wrapper.text()).toContain("Felt strong");
  });

  it("edit button links to edit-session route", async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: mockSession,
      error: null,
    });

    const wrapper = await mountComponent();
    await flushPromises();

    const editLink = wrapper.find('a[href="/sessions/1/edit"]');
    expect(editLink.exists()).toBe(true);
  });

  it("copy button links to copy-session route", async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: mockSession,
      error: null,
    });

    const wrapper = await mountComponent();
    await flushPromises();

    const copyLink = wrapper.find('a[href="/sessions/1/copy"]');
    expect(copyLink.exists()).toBe(true);
  });

  it("shows delete button", async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: mockSession,
      error: null,
    });

    const wrapper = await mountComponent();
    await flushPromises();

    const deleteButton = wrapper.find('button[data-testid="delete-button"]');
    expect(deleteButton.exists()).toBe(true);
  });

  it("click on delete reveals confirmation", async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: mockSession,
      error: null,
    });

    const wrapper = await mountComponent();
    await flushPromises();

    const deleteButton = wrapper.find('button[data-testid="delete-button"]');
    await deleteButton.trigger("click");

    expect(
      wrapper.find('button[data-testid="confirm-delete"]').exists(),
    ).toBe(true);
    expect(
      wrapper.find('button[data-testid="cancel-delete"]').exists(),
    ).toBe(true);
  });

  it("cancel hides confirmation", async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: mockSession,
      error: null,
    });

    const wrapper = await mountComponent();
    await flushPromises();

    // Show confirmation
    await wrapper.find('button[data-testid="delete-button"]').trigger("click");
    expect(
      wrapper.find('button[data-testid="confirm-delete"]').exists(),
    ).toBe(true);

    // Cancel
    await wrapper.find('button[data-testid="cancel-delete"]').trigger("click");

    // Confirmation should be hidden
    expect(
      wrapper.find('button[data-testid="confirm-delete"]').exists(),
    ).toBe(false);
    expect(
      wrapper.find('button[data-testid="delete-button"]').exists(),
    ).toBe(true);
  });

  it("confirm calls delete API and redirects to home", async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: mockSession,
      error: null,
    });
    vi.mocked(api.fetchCsrfToken).mockResolvedValue();
    vi.mocked(api.delete).mockResolvedValue({
      data: null,
      error: null,
    });

    const router = createMockRouter();
    await router.push({ name: "session-detail", params: { id: 1 } });
    await router.isReady();

    const wrapper = mount(SessionDetailView, {
      global: {
        plugins: [router],
      },
    });
    await flushPromises();

    // Show confirmation and confirm
    await wrapper.find('button[data-testid="delete-button"]').trigger("click");
    await wrapper.find('button[data-testid="confirm-delete"]').trigger("click");
    await flushPromises();

    expect(api.fetchCsrfToken).toHaveBeenCalled();
    expect(api.delete).toHaveBeenCalledWith("/api/lifting/sessions/1/");
    expect(router.currentRoute.value.name).toBe("home");
  });

  it("shows error on API failure with retry button", async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: null,
      error: "Network error",
    });

    const wrapper = await mountComponent();
    await flushPromises();

    expect(wrapper.text()).toContain("Network error");
    expect(wrapper.find('button[data-testid="retry-button"]').exists()).toBe(
      true,
    );
  });

  it("retry button refetches session", async () => {
    // First call fails
    vi.mocked(api.get).mockResolvedValueOnce({
      data: null,
      error: "Network error",
    });

    const wrapper = await mountComponent();
    await flushPromises();

    // Second call succeeds
    vi.mocked(api.get).mockResolvedValueOnce({
      data: mockSession,
      error: null,
    });

    await wrapper.find('button[data-testid="retry-button"]').trigger("click");
    await flushPromises();

    expect(api.get).toHaveBeenCalledTimes(2);
    expect(wrapper.text()).toContain("Upper A");
  });
});
