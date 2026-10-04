<script setup lang="ts">
import { ref, watch } from "vue";
import { api } from "@/api/client";
import type { CalendarMonth } from "@/types/lifting";
import MonthCalendar from "@/components/ui/MonthCalendar.vue";

// Data side of the month calendar: fetches training dates for one month.
const props = defineProps<{ year: number; month: number }>();

const data = ref<CalendarMonth | null>(null);
const loading = ref(false);

async function fetchMonth() {
  loading.value = true;
  try {
    const response = await api.get<CalendarMonth>(
      `/api/lifting/sessions/calendar/?year=${props.year}&month=${props.month}`,
    );
    if (response.data) data.value = response.data;
  } finally {
    loading.value = false;
  }
}

watch(() => [props.year, props.month], fetchMonth, { immediate: true });
</script>

<template>
  <div>
    <slot name="header" :count="data?.sessions.length ?? null" :loading="loading" />
    <MonthCalendar :year="year" :month="month" :sessions="data?.sessions ?? []" :loading="loading" />
  </div>
</template>
