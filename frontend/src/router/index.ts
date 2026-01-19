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
      path: "/sessions/new",
      name: "create-session",
      component: () => import("@/views/CreateSessionView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/sessions/:id/edit",
      name: "edit-session",
      component: () => import("@/views/CreateSessionView.vue"),
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
