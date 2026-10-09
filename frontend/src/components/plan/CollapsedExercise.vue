<script setup lang="ts">
import type { DraftExercise } from "@/utils/plan";
import { formatClock } from "@/utils/format";
import SetChips from "@/components/ui/SetChips.vue";
import Icon from "@/components/ui/Icon.vue";

defineProps<{
  exercise: DraftExercise;
  prefix?: string;
  error?: boolean;
  /** A superset's black header already shows the shared rest. */
  hideRest?: boolean;
  /** Just folded: outlined for a moment so you can find your place. */
  just?: boolean;
}>();
const emit = defineEmits<{ expand: [] }>();
</script>

<template>
  <button
    type="button"
    class="collapsed"
    :class="{ 'is-error': error, 'is-just': just }"
    :aria-label="`Edit ${exercise.title || 'exercise'}`"
    @click="emit('expand')"
  >
    <span class="head">
      <span class="t caps">{{ prefix }}{{ exercise.title || "Unnamed exercise" }}</span>
      <span v-if="!hideRest" class="rest"><Icon name="clock" size="sm" />{{ formatClock(exercise.rest_seconds) }}</span>
      <Icon name="down" size="sm" class="chev" />
    </span>
    <SetChips :sets="exercise.sets" />
  </button>
</template>

<style scoped>
.collapsed {
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
.collapsed.is-just {
  box-shadow: inset 0 0 0 2px var(--k);
}
.head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.t {
  flex: 1;
  min-width: 0;
  font-size: 15.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.rest {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 13px;
  color: var(--muted);
  white-space: nowrap;
}
.chev {
  color: var(--muted);
}
</style>
