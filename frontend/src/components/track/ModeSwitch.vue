<script setup lang="ts">
import { RouterLink } from "vue-router";

// Lift (Track) or Edit (the Plan editor) for the live session. Black marks where you are.
defineProps<{ sessionId: number; mode: "lift" | "edit" }>();
</script>

<template>
  <nav class="mode-switch" aria-label="Mode">
    <RouterLink :to="{ name: 'track', params: { id: sessionId } }" replace :aria-current="mode === 'lift' ? 'page' : undefined">
      Lift
    </RouterLink>
    <RouterLink :to="{ name: 'track-edit', params: { id: sessionId } }" replace :aria-current="mode === 'edit' ? 'page' : undefined">
      Edit
    </RouterLink>
  </nav>
</template>

<style scoped>
.mode-switch {
  display: inline-grid;
  grid-template-columns: 1fr 1fr;
  flex: 0 0 auto;
  margin-right: auto;
  border: 1.5px solid var(--k);
  border-radius: var(--r);
  overflow: hidden;
  background: var(--card);
}
.mode-switch a {
  display: grid;
  place-items: center;
  min-height: 41px;
  min-width: 54px;
  padding: 0 10px;
  color: var(--k);
  font-size: 13.5px;
  font-weight: 800;
  text-transform: uppercase;
  font-stretch: 85%;
  letter-spacing: 0.06em;
  text-decoration: none;
}
.mode-switch a + a {
  border-left: 1.5px solid var(--k);
}
.mode-switch a[aria-current="page"] {
  background: var(--k);
  color: var(--y);
}
</style>
