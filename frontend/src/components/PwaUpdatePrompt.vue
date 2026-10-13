<script setup lang="ts">
import { useRegisterSW } from "virtual:pwa-register/vue";
import Btn from "@/components/ui/Btn.vue";

const { needRefresh, updateServiceWorker } = useRegisterSW();

// The worker used to be registered under /static/, where it couldn't control
// the app at /. Drop that copy and its precache now that it has root scope.
const oldScope = new URL(import.meta.env.BASE_URL, location.origin).href;
if (import.meta.env.BASE_URL !== "/" && "serviceWorker" in navigator) {
  navigator.serviceWorker
    .getRegistrations()
    .then((registrations) => {
      for (const registration of registrations) {
        if (registration.scope !== oldScope) continue;
        registration.unregister();
        caches.delete(`workbox-precache-v2-${oldScope}`);
      }
    })
    .catch(() => {
      // Leaving it in place is harmless; it only controls /static/ URLs.
    });
}

function update() {
  updateServiceWorker();
}

function dismiss() {
  needRefresh.value = false;
}
</script>

<template>
  <Transition name="slide">
    <div v-if="needRefresh" class="pwa-update" role="status">
      <span class="text">A new version is ready</span>
      <Btn size="small" variant="primary" @click="update">Update</Btn>
      <Btn size="small" variant="ghost" class="later" @click="dismiss">Later</Btn>
    </div>
  </Transition>
</template>

<style scoped>
.pwa-update {
  position: fixed;
  left: 8px;
  right: 8px;
  top: calc(8px + env(safe-area-inset-top));
  z-index: 60;
  display: flex;
  align-items: center;
  gap: 8px;
  max-width: 560px;
  margin: 0 auto;
  padding: 10px 10px 10px 14px;
  background: var(--k);
  color: var(--on-k);
  border-radius: var(--r-lg);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.3);
}
.text {
  flex: 1;
  font-weight: 600;
}
.later {
  color: var(--on-k);
}
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease, opacity 0.3s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateY(-120%);
  opacity: 0;
}
</style>
