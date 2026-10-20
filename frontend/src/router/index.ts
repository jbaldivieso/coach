import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { followNext } from "@/utils/next";

// Django serves the app at /, with only its assets under BASE_URL (/static/).
// `vite preview` serves the whole app under BASE_URL, so follow it there.
const base = location.pathname.startsWith(import.meta.env.BASE_URL) ? import.meta.env.BASE_URL : "/";

const router = createRouter({
  history: createWebHistory(base),
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
      component: () => import("@/views/TrackView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/track/:id/edit",
      name: "track-edit",
      component: () => import("@/views/PlanView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/track/:id/finish",
      name: "track-finish",
      component: () => import("@/views/FinishView.vue"),
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
      path: "/exercise/:title",
      name: "exercise-history",
      component: () => import("@/views/ExerciseHistoryView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/history/year",
      name: "year",
      component: () => import("@/views/YearView.vue"),
      meta: { requiresAuth: true },
    },
    {
      path: "/history/:year(\\d+)/:month(\\d+)",
      name: "month",
      component: () => import("@/views/MonthView.vue"),
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

  if (!authStore.verified && !authStore.loading) {
    if (authStore.user && !to.meta.guest) {
      // Signed in last launch: show the app now and let the server confirm
      // in the background, so a slow server doesn't hold up the first screen.
      // Guest pages wait, so an expired session keeps /login?next= intact.
      authStore.checkAuth().then(() => {
        if (!authStore.isAuthenticated) router.replace({ name: "login" });
      });
    } else {
      await authStore.checkAuth();
    }
  }

  // Redirect to login if auth required but not authenticated
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next({ name: "login" });
    return;
  }

  // Already signed in: go on to ?next= (an OAuth sign-in, say), or home.
  // Only once the server has confirmed it, though: Django would send a
  // session it doesn't know straight back here, round and round.
  if (to.meta.guest && authStore.isAuthenticated) {
    if (to.query.next !== undefined && !authStore.verified) {
      next();
      return;
    }
    const target = followNext(to.query.next);
    if (target) next(target);
    else next(false);
    return;
  }

  next();
});

export default router;
