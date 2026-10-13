<script setup lang="ts">
import type { SetValues } from "@/types/lifting";
import { formatWeight, formatSet } from "@/utils/format";

// Six fixed columns (no exercise goes past 6 sets), so set N lines up across rows.
withDefaults(
  defineProps<{
    sets: (SetValues & { done?: boolean })[];
    selectable?: boolean;
    /** Show done sets black and locked (editing a live session). */
    markDone?: boolean;
    selected?: number | null;
    tone?: "chip" | "card";
    size?: "md" | "lg";
  }>(),
  { selectable: false, markDone: false, selected: null, tone: "chip", size: "md" },
);

const emit = defineEmits<{ select: [index: number] }>();
</script>

<template>
  <div class="setchips" :class="[`tone-${tone}`, `size-${size}`]">
    <template v-for="(set, i) in sets" :key="i">
      <button
        v-if="selectable"
        type="button"
        class="chip"
        :class="{ 'is-selected': selected === i, 'is-done': markDone && set.done }"
        :aria-pressed="selected === i"
        :disabled="markDone && set.done"
        :aria-label="`Set ${i + 1}: ${formatSet(set)}${markDone && set.done ? ', done' : ''}`"
        @click="emit('select', i)"
      >
        <em>{{ formatWeight(set.weight) }}</em>
        <span><b>×</b>{{ set.reps || "–" }}</span>
      </button>
      <span v-else class="chip" :class="{ 'is-done': markDone && set.done }" :aria-label="formatSet(set)">
        <em>{{ formatWeight(set.weight) }}</em>
        <span><b>×</b>{{ set.reps }}</span>
      </span>
    </template>
  </div>
</template>

<style scoped>
.setchips {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 4px;
  width: 100%;
}
.chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 0;
  padding: 6px 2px 5px;
  border-radius: 5px;
  background: var(--chip);
  color: var(--k);
  font-size: 13.5px;
  line-height: 1.2;
  font-style: normal;
}
.tone-card .chip {
  background: var(--card);
}
.size-lg .chip {
  font-size: 14.5px;
  padding: 7px 2px 6px;
}
.chip em {
  font-style: normal;
  font-weight: 800;
}
.chip span {
  font-weight: 600;
}
.chip b {
  font-weight: 400;
  color: var(--muted);
  margin-right: 1px;
}
button.chip {
  min-height: 44px;
}
.chip.is-done {
  background: var(--k);
  color: var(--on-k);
}
.chip.is-done b {
  color: var(--on-k-muted);
}
.chip.is-selected {
  background: var(--y);
  box-shadow: inset 0 0 0 2px var(--k);
}
</style>
