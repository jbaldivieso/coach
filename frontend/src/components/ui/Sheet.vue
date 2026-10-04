<script setup lang="ts">
import { watch, onUnmounted, ref, nextTick } from "vue";

const props = defineProps<{ open: boolean; title: string }>();
const emit = defineEmits<{ close: [] }>();

const panel = ref<HTMLElement | null>(null);

function onKeydown(event: KeyboardEvent) {
  if (event.key === "Escape") emit("close");
}

watch(
  () => props.open,
  async (open) => {
    if (open) {
      document.addEventListener("keydown", onKeydown);
      await nextTick();
      // Focus the first field if there is one, else the panel itself
      const field = panel.value?.querySelector<HTMLElement>("input, textarea");
      (field ?? panel.value)?.focus();
    } else {
      document.removeEventListener("keydown", onKeydown);
    }
  },
  { immediate: true },
);

onUnmounted(() => document.removeEventListener("keydown", onKeydown));
</script>

<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="open" class="sheet-root">
        <div class="sheet-dim" @click="emit('close')" />
        <section ref="panel" class="sheet" role="dialog" aria-modal="true" :aria-label="title" tabindex="-1">
          <div class="sheet-grab" />
          <h2 class="sheet-title">{{ title }}</h2>
          <slot />
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.sheet-root {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}
.sheet-dim {
  position: absolute;
  inset: 0;
  background: var(--dim);
}
.sheet {
  position: relative;
  width: 100%;
  max-width: 640px;
  margin: 0 auto;
  max-height: calc(100dvh - 72px);
  overflow-y: auto;
  background: var(--card);
  border-radius: 14px 14px 0 0;
  padding: 8px var(--gutter) calc(16px + env(safe-area-inset-bottom));
  outline: none;
}
.sheet-grab {
  width: 40px;
  height: 5px;
  border-radius: 3px;
  background: var(--rule-strong);
  margin: 0 auto 10px;
}
.sheet-title {
  font-size: 22px;
  font-weight: 800;
  text-transform: uppercase;
  font-stretch: 80%;
  letter-spacing: 0.03em;
  margin-bottom: 10px;
}
.sheet-enter-active,
.sheet-leave-active {
  transition: opacity 0.2s ease-out;
}
.sheet-enter-active .sheet,
.sheet-leave-active .sheet {
  transition: transform 0.22s cubic-bezier(0.2, 0.8, 0.2, 1);
}
.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;
}
.sheet-enter-from .sheet,
.sheet-leave-to .sheet {
  transform: translateY(40px);
}
</style>
