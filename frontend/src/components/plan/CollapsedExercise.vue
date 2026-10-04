<script setup lang="ts">
import type { DraftExercise } from "@/utils/plan";
import type { HistoryEntry } from "@/composables/useExerciseHistory";
import { formatShortDate } from "@/utils/format";
import SetChips from "@/components/ui/SetChips.vue";
import Icon from "@/components/ui/Icon.vue";

defineProps<{ exercise: DraftExercise; entry: HistoryEntry | undefined; prefix?: string; error?: boolean }>();
const emit = defineEmits<{ expand: [] }>();
</script>

<template>
  <button type="button" class="collapsed" :class="{ 'is-error': error }" :aria-label="`Edit ${exercise.title || 'exercise'}`" @click="emit('expand')">
    <span class="t caps">{{ prefix }}{{ exercise.title || "Unnamed exercise" }}</span>
    <Icon name="down" size="sm" class="chev" />
    <span class="lbl"><span class="lbl-name">Plan</span><SetChips :sets="exercise.sets" /></span>
    <span v-if="entry?.items[0]" class="lbl">
      <span class="lbl-name">{{ formatShortDate(entry.items[0].date) }}</span>
      <SetChips :sets="entry.items[0].sets" />
    </span>
  </button>
</template>

<style scoped>
.collapsed {
  position: relative;
  display: block;
  width: 100%;
  text-align: left;
  background: var(--card);
  border-radius: var(--r-lg);
  padding: 10px 12px;
  margin-bottom: 8px;
}
.collapsed.is-error {
  box-shadow: inset 0 0 0 2px var(--alert);
}
.t {
  display: block;
  font-size: 15.5px;
  margin: 0 28px 6px 0;
}
.chev {
  position: absolute;
  top: 13px;
  right: 12px;
  color: var(--muted);
}
.lbl {
  display: flex;
  align-items: center;
  gap: 8px;
}
.lbl + .lbl {
  margin-top: 4px;
}
.lbl-name {
  width: 42px;
  flex: 0 0 auto;
  font-size: 11.5px;
  font-weight: 600;
  color: var(--muted);
}
</style>
