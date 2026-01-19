import { describe, it, expect, beforeEach } from "vitest";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { createRouter, createWebHistory } from "vue-router";
import AppHeader from "./AppHeader.vue";
import { useAuthStore } from "@/stores/auth";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "home", component: { template: "<div>Home</div>" } },
    { path: "/login", name: "login", component: { template: "<div>Login</div>" } },
  ],
});

describe("AppHeader", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it("renders the site title", () => {
    const wrapper = mount(AppHeader, {
      global: {
        plugins: [router],
      },
    });
    expect(wrapper.text()).toContain("Coach");
  });

  it("shows logout button when authenticated", async () => {
    const authStore = useAuthStore();
    authStore.user = { id: 1, username: "testuser" };

    const wrapper = mount(AppHeader, {
      global: {
        plugins: [router],
      },
    });

    expect(wrapper.text()).toContain("Log out");
  });

  it("hides logout button when not authenticated", () => {
    const wrapper = mount(AppHeader, {
      global: {
        plugins: [router],
      },
    });

    expect(wrapper.text()).not.toContain("Log out");
  });
});
