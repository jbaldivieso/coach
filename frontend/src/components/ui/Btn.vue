<script setup lang="ts">
import { computed } from "vue";
import { RouterLink, type RouteLocationRaw } from "vue-router";

const props = withDefaults(
  defineProps<{
    variant?: "primary" | "secondary" | "dark" | "ghost";
    size?: "huge" | "normal" | "small";
    to?: RouteLocationRaw;
    type?: "button" | "submit";
    disabled?: boolean;
    loading?: boolean;
  }>(),
  { variant: "secondary", size: "normal", type: "button" },
);

const classes = computed(() => [
  "btn",
  `btn-${props.variant}`,
  `btn-${props.size}`,
  { "is-loading": props.loading },
]);
</script>

<template>
  <RouterLink v-if="to && !disabled" :to="to" :class="classes"><slot /></RouterLink>
  <button v-else :type="type" :class="classes" :disabled="disabled || loading" :aria-busy="loading || undefined">
    <slot />
  </button>
</template>

<style scoped>
.btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 48px;
  padding: 0 16px;
  border-radius: var(--r);
  border: 1.5px solid var(--k);
  background: var(--card);
  color: var(--k);
  font-size: 15px;
  font-weight: 700;
  text-align: center;
  transition: transform 0.08s ease-out, background-color 0.12s;
  user-select: none;
}
.btn:active:not(:disabled) {
  transform: scale(0.98);
}
.btn:disabled {
  opacity: 0.45;
}
.btn-primary {
  background: var(--y);
  border: 2px solid var(--k);
}
.btn-dark {
  background: var(--k);
  color: var(--y);
  border: 2px solid var(--k);
}
.btn-ghost {
  border-color: transparent;
  background: transparent;
}
.btn-huge {
  min-height: 64px;
  font-size: 19px;
  font-weight: 800;
  text-transform: uppercase;
  font-stretch: 85%;
  letter-spacing: 0.06em;
}
.btn-small {
  min-height: 44px;
  padding: 0 12px;
  font-size: 13.5px;
  text-transform: uppercase;
  font-stretch: 85%;
  letter-spacing: 0.05em;
}
.is-loading {
  opacity: 0.7;
}
</style>
