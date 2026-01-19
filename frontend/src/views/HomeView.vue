<script setup lang="ts">
import { useAuthStore } from "@/stores/auth";

const authStore = useAuthStore();
</script>

<template>
  <div class="container">
    <section class="section">
      <h1 class="title">Welcome, {{ authStore.user?.username }}</h1>
      <p class="subtitle">You are logged in.</p>
    </section>
  </div>
</template>
