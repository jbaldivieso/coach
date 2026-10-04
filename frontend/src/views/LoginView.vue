<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import Btn from "@/components/ui/Btn.vue";

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
  <div class="screen login">
    <header class="brand">
      <h1>Coach</h1>
    </header>
    <main class="screen-body">
      <form class="form" @submit.prevent="handleSubmit">
        <label class="field-label" for="username">Username</label>
        <div class="text-field">
          <input id="username" v-model="username" type="text" required autocomplete="username" autocapitalize="none" />
        </div>

        <label class="field-label" for="password">Password</label>
        <div class="text-field">
          <input id="password" v-model="password" type="password" required autocomplete="current-password" />
        </div>

        <div v-if="authStore.error" class="notice is-error" role="alert">{{ authStore.error }}</div>

        <Btn type="submit" variant="primary" size="huge" class="submit" :loading="authStore.loading">Log in</Btn>
      </form>
    </main>
  </div>
</template>

<style scoped>
.brand {
  background: var(--y);
  padding: calc(48px + env(safe-area-inset-top)) var(--gutter) 28px;
  position: relative;
}
.brand::after {
  content: "";
  position: absolute;
  inset: auto 0 0 0;
  height: 6px;
  background: var(--hazard);
}
.brand h1 {
  max-width: var(--content);
  margin: 0 auto;
  font-size: 56px;
  font-weight: 800;
  line-height: 1;
  text-transform: uppercase;
  font-stretch: 75%;
  letter-spacing: 0.02em;
}
.form {
  display: grid;
  gap: 6px;
  max-width: 420px;
  margin: 16px auto 0;
}
.field-label {
  margin-top: 10px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  font-stretch: 80%;
  letter-spacing: 0.16em;
  color: var(--muted);
}
.submit {
  margin-top: 18px;
}
</style>
