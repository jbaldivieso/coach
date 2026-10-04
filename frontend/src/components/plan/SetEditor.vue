<script setup lang="ts">
import { ref } from "vue";
import type { DraftSet } from "@/utils/plan";
import Stepper from "@/components/ui/Stepper.vue";

const props = defineProps<{ set: DraftSet; index: number; label?: string }>();
const emit = defineEmits<{
  "update:weight": [value: number | null];
  "update:reps": [value: number];
  copyToAll: [];
}>();

// Remember the last real weight so toggling BW off restores it.
const lastWeight = ref<number>(props.set.weight ?? 0);

function setWeight(value: number | null) {
  if (value !== null) lastWeight.value = value;
  emit("update:weight", value);
}

function toggleBodyweight() {
  setWeight(props.set.weight === null ? lastWeight.value : null);
}
</script>

<template>
  <div class="editor">
    <div class="ed-head">
      <span class="ed-label">{{ label ?? `Set ${index + 1}` }}</span>
      <button
        type="button"
        class="bw"
        :class="{ 'is-on': set.weight === null }"
        :aria-pressed="set.weight === null"
        @click="toggleBodyweight"
      >
        BW
      </button>
    </div>
    <Stepper
      :model-value="set.weight"
      label="weight"
      unit="lb"
      :step="5"
      decimal
      nullable
      size="md"
      @update:model-value="setWeight"
    />
    <Stepper
      :model-value="set.reps"
      label="reps"
      unit="reps"
      :step="1"
      size="md"
      @update:model-value="(v) => emit('update:reps', v ?? 0)"
    />
    <button type="button" class="copydown" @click="emit('copyToAll')">Copy set 1 to all</button>
  </div>
</template>

<style scoped>
.editor {
  display: grid;
  gap: 6px;
  margin: 8px 0 12px;
  padding: 10px;
  border: 2px solid var(--k);
  border-radius: var(--r-lg);
}
.ed-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.ed-label {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-stretch: 85%;
}
.bw {
  min-width: 48px;
  min-height: 32px;
  padding: 0 10px;
  border: 1.5px solid var(--rule-strong);
  border-radius: var(--r);
  font-size: 12.5px;
  font-weight: 800;
  letter-spacing: 0.06em;
}
.bw.is-on {
  background: var(--k);
  color: var(--y);
  border-color: var(--k);
}
.copydown {
  justify-self: start;
  min-height: 36px;
  font-size: 12.5px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-stretch: 85%;
  text-decoration: underline;
  text-underline-offset: 3px;
}
</style>
