import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "home",
      component: () => import("@/views/HomeView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/start",
      name: "start-from",
      component: () => import("@/views/StartFromView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/plan/new",
      name: "plan-new",
      component: () => import("@/views/PlanView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/plan/:id",
      name: "plan-edit",
      component: () => import("@/views/PlanView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/session/:id/edit",
      name: "session-edit",
      component: () => import("@/views/PlanView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/track/:id",
      name: "track",
      component: () => import("@/views/SessionDetailView.vue"), // TODO(phase 4): TrackView
      meta: { requiresAuth: true },
    },
    // Old URLs, for bookmarks and home-screen history
    { path: "/sessions/new", redirect: { name: "plan-new" } },
    { path: "/sessions/:id/copy", redirect: (to) => ({ name: "plan-new", query: { from: to.params.id } }) },
    { path: "/sessions/:id/edit", redirect: (to) => ({ name: "session-edit", params: { id: to.params.id } }) },
    {
      path: "/session/:id",
      name: "session-detail",
      component: () => import("@/views/SessionDetailView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/search",
      name: "search",
      component: () => import("@/views/SearchView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/changelog",
      name: "changelog",
      component: () => import("@/views/ChangelogView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/login",
      name: "login",
      component: () => import("@/views/LoginView.vue"),
      meta: { guest: true },
    },
  ],
});

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore();

  // Check auth status if not yet known
  if (authStore.user === null && !authStore.loading) {
    await authStore.checkAuth();
  }

  // Redirect to login if auth required but not authenticated
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: "login" });
    return;
  }

  // Redirect to home if guest-only page but authenticated
  if (to.meta.guest && authStore.isAuthenticated) {
    next({ name: "home" });
    return;
  }

  next();
});

export default router;
