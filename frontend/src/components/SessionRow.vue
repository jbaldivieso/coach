<script setup lang="ts">
import { computed } from "vue";
import { RouterLink, type RouteLocationRaw } from "vue-router";
import { parseDate, formatExerciseList } from "@/utils/format";

const props = withDefaults(
  defineProps<{
    title: string;
    date: string;
    exercises?: { title: string }[];
    to: RouteLocationRaw;
    /** Under the day number: the weekday (Wed) or the month (Jan). */
    dateCaption?: "weekday" | "month";
    chevron?: boolean;
  }>(),
  { dateCaption: "weekday", chevron: false },
);

const day = computed(() => parseDate(props.date).getDate());
const caption = computed(() =>
  parseDate(props.date).toLocaleDateString("en-US", props.dateCaption === "weekday" ? { weekday: "short" } : { month: "short" }),
);
</script>

<template>
  <RouterLink :to="to" class="row">
    <div class="row-date"><b>{{ day }}</b>{{ caption }}</div>
    <div class="row-main">
      <div class="row-title">{{ title }}</div>
      <div v-if="exercises?.length" class="row-sub">{{ formatExerciseList(exercises) }}</div>
    </div>
    <slot />
    <svg v-if="chevron" class="chev" viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 7 7-7 7" /></svg>
  </RouterLink>
</template>

<style scoped>
.chev {
  width: 16px;
  height: 16px;
  fill: none;
  stroke: var(--muted);
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
  flex: 0 0 auto;
}
</style>
