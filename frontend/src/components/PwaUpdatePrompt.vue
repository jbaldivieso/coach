<script setup lang="ts">
import { useRegisterSW } from "virtual:pwa-register/vue";

const { needRefresh, updateServiceWorker } = useRegisterSW();

function update() {
  updateServiceWorker();
}

function dismiss() {
  needRefresh.value = false;
}
</script>

<template>
  <Transition name="slide">
    <div v-if="needRefresh" class="pwa-update-banner">
      <span class="pwa-update-text">A new version is available</span>
      <div class="pwa-update-actions">
        <button class="button is-small is-primary" @click="update">
          Update
        </button>
        <button class="button is-small is-ghost" @click="dismiss">
          Later
        </button>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.pwa-update-banner {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background-color: var(--color4);
  color: white;
  padding: 0.75rem 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  z-index: 1000;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.3);
}

.pwa-update-text {
  font-weight: 500;
}

.pwa-update-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

/* Slide transition */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateY(100%);
}
</style>
