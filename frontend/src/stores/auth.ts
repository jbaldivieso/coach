import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { api } from "@/api/client";

interface User {
  id: number;
  username: string;
}

const USER_KEY = "coach.user";

function readStoredUser(): User | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

function storeUser(user: User | null) {
  try {
    if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
    else localStorage.removeItem(USER_KEY);
  } catch {
    // Without storage the next launch just waits for the server again.
  }
}

export const useAuthStore = defineStore("auth", () => {
  // Whoever was signed in last launch, so the app can render before the server answers.
  const user = ref<User | null>(readStoredUser());
  /** True once the server has confirmed or denied the session this launch. */
  const verified = ref(false);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const isAuthenticated = computed(() => user.value !== null);

  function setUser(value: User | null) {
    user.value = value;
    verified.value = true;
    storeUser(value);
  }

  async function checkAuth() {
    loading.value = true;
    error.value = null;

    try {
      const response = await api.get<User>("/api/accounts/me/");

      if (response.data) {
        setUser(response.data);
      } else if (response.error === "Unauthorized") {
        setUser(null);
      }
      // Any other failure says nothing about the session; keep what we have.
    } catch {
      // Offline or the server is unreachable: same.
    }

    loading.value = false;
  }

  async function login(username: string, password: string): Promise<boolean> {
    loading.value = true;
    error.value = null;

    // Fetch CSRF token before login
    await api.fetchCsrfToken();

    const response = await api.post<User>("/api/accounts/login/", {
      username,
      password,
    });

    if (response.data) {
      setUser(response.data);
      loading.value = false;
      return true;
    }

    error.value = response.error || "Login failed";
    loading.value = false;
    return false;
  }

  async function logout(): Promise<boolean> {
    loading.value = true;
    error.value = null;

    // Fetch CSRF token before logout
    await api.fetchCsrfToken();

    const response = await api.post("/api/accounts/logout/");

    if (response.error) {
      error.value = response.error;
      loading.value = false;
      return false;
    }

    setUser(null);
    loading.value = false;
    return true;
  }

  return {
    user,
    verified,
    loading,
    error,
    isAuthenticated,
    checkAuth,
    login,
    logout,
  };
});
