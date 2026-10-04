<script setup lang="ts">
import { ref, onMounted } from "vue";
import { RouterLink } from "vue-router";
import { api } from "@/api/client";
import type { CalendarYear } from "@/types/lifting";
import AppBar from "@/components/ui/AppBar.vue";
import MonthCalendar from "@/components/ui/MonthCalendar.vue";

const months = ref<CalendarYear["months"]>([]);
const error = ref<string | null>(null);
const loading = ref(true);
const now = new Date();

function isThisMonth(year: number, month: number) {
  return year === now.getFullYear() && month === now.getMonth() + 1;
}

function shortName(year: number, month: number) {
  return new Date(year, month - 1, 1).toLocaleDateString("en-US", { month: "short" });
}

async function load() {
  loading.value = true;
  const response = await api.get<CalendarYear>("/api/lifting/sessions/calendar/year/");
  loading.value = false;
  if (response.data) months.value = response.data.months;
  else error.value = response.error || "Couldn't load the year";
}

onMounted(load);
</script>

<template>
  <div class="screen">
    <AppBar title="Past year" back="/" />
    <main class="screen-body">
      <p class="muted small">Tap a month to open it.</p>
      <div v-if="error" class="notice is-error">
        {{ error }}
        <button class="notice-action" @click="load">Retry</button>
      </div>
      <p v-else-if="loading" class="empty">Loading…</p>
      <div v-else class="year">
        <RouterLink
          v-for="m in months"
          :key="`${m.year}-${m.month}`"
          :to="{ name: 'month', params: { year: m.year, month: m.month } }"
          class="mo"
          :class="{ sel: isThisMonth(m.year, m.month) }"
        >
          <b>{{ shortName(m.year, m.month) }}<span v-if="m.month === 1"> {{ m.year }}</span></b>
          <MonthCalendar :year="m.year" :month="m.month" :sessions="m.sessions" mini />
          <small>{{ m.sessions.length || "–" }}</small>
        </RouterLink>
      </div>
    </main>
  </div>
</template>

<style scoped>
.year {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px 12px;
  margin-top: 10px;
}
.mo {
  display: block;
  padding: 4px;
  border-radius: var(--r-sm);
}
.mo b {
  display: block;
  margin-bottom: 4px;
  font-size: 12.5px;
  text-transform: uppercase;
  font-stretch: 85%;
  letter-spacing: 0.06em;
}
.mo small {
  display: block;
  margin-top: 3px;
  font-size: 11px;
  color: var(--muted);
}
.mo.sel {
  outline: 2px solid var(--k);
  background: var(--y);
}
.mo.sel small {
  color: var(--k);
}
</style>
