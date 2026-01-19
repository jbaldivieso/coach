import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { api } from "@/api/client";

interface User {
  id: number;
  username: string;
}

export const useAuthStore = defineStore("auth", () => {
  const user = ref<User | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const isAuthenticated = computed(() => user.value !== null);

  async function checkAuth() {
    loading.value = true;
    error.value = null;

    const response = await api.get<User>("/api/accounts/me/");

    if (response.data) {
      user.value = response.data;
    } else {
      user.value = null;
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
      user.value = response.data;
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

    user.value = null;
    loading.value = false;
    return true;
  }

  return {
    user,
    loading,
    error,
    isAuthenticated,
    checkAuth,
    login,
    logout,
  };
});
