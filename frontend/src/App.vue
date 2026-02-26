<script setup lang="ts">
import AppHeader from "@/components/AppHeader.vue";
import PwaUpdatePrompt from "@/components/PwaUpdatePrompt.vue";
</script>

<template>
  <AppHeader />
  <main class="main-content">
    <router-view />
  </main>
  <PwaUpdatePrompt />
</template>
