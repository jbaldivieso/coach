<script setup lang="ts">
import { pluralize } from "@/utils/format";
import { MAX_SETS } from "@/utils/plan";

const props = defineProps<{ count: number; noun: string }>();
const emit = defineEmits<{ change: [count: number] }>();
</script>

<template>
  <span class="count">
    <button type="button" class="mini-pm" :aria-label="`One fewer ${noun}`" :disabled="count <= 1" @click="emit('change', props.count - 1)">−</button>
    <b aria-live="polite">{{ pluralize(count, noun) }}</b>
    <button type="button" class="mini-pm" :aria-label="`One more ${noun}`" :disabled="count >= MAX_SETS" @click="emit('change', props.count + 1)">+</button>
  </span>
</template>

<style scoped>
.count {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}
.count b {
  font-weight: 700;
  min-width: 58px;
  text-align: center;
}
.mini-pm {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border: 1.5px solid var(--rule-strong);
  border-radius: 5px;
  font-weight: 700;
  font-size: 18px;
  background: var(--card);
}
.mini-pm:disabled {
  opacity: 0.35;
}
</style>
