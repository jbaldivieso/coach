<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const authStore = useAuthStore();

const username = ref("");
const password = ref("");

async function handleSubmit() {
  const success = await authStore.login(username.value, password.value);
  if (success) {
    router.push({ name: "home" });
  }
}
</script>

<template>
  <div class="container">
    <div class="columns is-centered">
      <div class="column is-5-tablet is-4-desktop">
        <section class="section">
          <h1 class="title has-text-centered">Coach</h1>

          <form @submit.prevent="handleSubmit">
            <div class="field">
              <label class="label" for="username">Username</label>
              <div class="control">
                <input
                  id="username"
                  v-model="username"
                  class="input"
                  type="text"
                  placeholder="Enter username"
                  required
                  autocomplete="username"
                />
              </div>
            </div>

            <div class="field">
              <label class="label" for="password">Password</label>
              <div class="control">
                <input
                  id="password"
                  v-model="password"
                  class="input"
                  type="password"
                  placeholder="Enter password"
                  required
                  autocomplete="current-password"
                />
              </div>
            </div>

            <div
              v-if="authStore.error"
              class="notification is-danger is-light"
            >
              {{ authStore.error }}
            </div>

            <div class="field">
              <div class="control">
                <button
                  class="button is-primary is-fullwidth"
                  type="submit"
                  :class="{ 'is-loading': authStore.loading }"
                  :disabled="authStore.loading"
                >
                  Log in
                </button>
              </div>
            </div>
          </form>
        </section>
      </div>
    </div>
  </div>
</template>
