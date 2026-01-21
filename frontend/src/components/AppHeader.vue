<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";
import { useRouter } from "vue-router";

const authStore = useAuthStore();
const router = useRouter();

async function handleLogout() {
  const success = await authStore.logout();
  if (success) {
    router.push({ name: "login" });
  }
}
</script>

<template>
  <nav class="navbar" role="navigation" aria-label="main navigation">
    <div class="container">
      <div class="navbar-brand">
        <router-link class="navbar-item has-text-weight-bold" to="/">
          Coach
        </router-link>
      </div>

      <div class="navbar-end" v-if="authStore.isAuthenticated">
        <div class="navbar-item">
          <div class="buttons">
            <button
              class="button logout is-small"
              :class="{ 'is-loading': authStore.loading }"
              :disabled="authStore.loading"
              @click="handleLogout"
            >
              Log out
            </button>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>
