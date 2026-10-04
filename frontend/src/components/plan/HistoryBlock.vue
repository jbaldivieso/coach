<script setup lang="ts">
import { RouterLink } from "vue-router";
import type { HistoryEntry } from "@/composables/useExerciseHistory";
import { formatOuting, formatShortDate } from "@/utils/format";
import SetChips from "@/components/ui/SetChips.vue";

withDefaults(
  defineProps<{
    title: string;
    entry: HistoryEntry | undefined;
    /** Outings to show; superset members show fewer. */
    limit?: number;
    /** Leave out the session title (supersets are tight on space). */
    short?: boolean;
  }>(),
  { limit: 3, short: false },
);
</script>

<template>
  <div class="hist">
    <div class="hist-head">
      <span class="hist-label">{{ limit === 1 ? "Last time" : `Last ${limit} times` }}</span>
      <RouterLink
        v-if="title && entry?.items.length"
        :to="{ name: 'exercise-history', params: { title } }"
        class="hist-all"
      >
        All {{ entry.total }}
      </RouterLink>
    </div>
    <p v-if="!title" class="hist-note">Pick a name to see its last 3 outings and copy its most recent sets as targets.</p>
    <p v-else-if="!entry || entry.loading" class="hist-note">Loading…</p>
    <p v-else-if="entry.error" class="hist-note">{{ entry.error }}</p>
    <p v-else-if="entry.items.length === 0" class="hist-note">First time. No history yet.</p>
    <template v-else>
      <div v-for="o in entry.items.slice(0, limit)" :key="o.exercise_id" class="outing">
        <span class="when">{{ short ? formatShortDate(o.date) : formatOuting(o.date, o.session_title) }}</span>
        <SetChips :sets="o.sets" tone="card" />
        <span v-if="o.comments" class="c">{{ o.comments }}</span>
      </div>
    </template>
  </div>
</template>

<style scoped>
.hist {
  background: var(--concrete);
  border-radius: var(--r);
  padding: 6px 8px 4px;
  margin: 8px 0 4px;
  font-size: 12.5px;
}
.hist-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  min-height: 24px;
}
.hist-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-stretch: 85%;
  color: var(--muted);
}
.hist-all {
  font-size: 12px;
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 3px;
}
.hist-note {
  color: var(--muted);
  padding: 4px 0 6px;
}
.outing {
  display: block;
  padding: 6px 0;
  border-bottom: 1px solid var(--rule);
}
.outing:last-child {
  border-bottom: 0;
}
.when {
  display: block;
  margin-bottom: 3px;
  font-size: 12px;
  font-weight: 600;
  color: var(--muted);
}
.c {
  display: block;
  margin-top: 3px;
  font-style: italic;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
