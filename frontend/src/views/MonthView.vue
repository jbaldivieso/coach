<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "@/api/client";
import type { PaginatedSessions, Session } from "@/types/lifting";
import { pluralize } from "@/utils/format";
import AppBar from "@/components/ui/AppBar.vue";
import Icon from "@/components/ui/Icon.vue";
import SessionCalendar from "@/components/SessionCalendar.vue";
import SessionRow from "@/components/SessionRow.vue";

const route = useRoute();
const router = useRouter();
const year = computed(() => Number(route.params.year));
const month = computed(() => Number(route.params.month));
const label = computed(() =>
  new Date(year.value, month.value - 1, 1).toLocaleDateString("en-US", { month: "long", year: "numeric" }),
);
const now = new Date();
const isCurrent = computed(() => year.value === now.getFullYear() && month.value === now.getMonth() + 1);

const sessions = ref<Session[]>([]);
const loading = ref(true);
const error = ref<string | null>(null);

async function load() {
  loading.value = true;
  error.value = null;
  const key = `${year.value}-${String(month.value).padStart(2, "0")}`;
  const response = await api.get<PaginatedSessions>(`/api/lifting/sessions/?month=${key}&limit=100`);
  loading.value = false;
  if (response.data) sessions.value = response.data.items;
  else error.value = response.error || "Couldn't load the month";
}

function go(delta: number) {
  const d = new Date(year.value, month.value - 1 + delta, 1);
  router.replace({ name: "month", params: { year: d.getFullYear(), month: d.getMonth() + 1 } });
}

watch([year, month], load, { immediate: true });
</script>

<template>
  <div class="screen">
    <AppBar :title="label" back="/history/year" />
    <main class="screen-body">
      <SessionCalendar :year="year" :month="month">
        <template #header="{ count }">
          <div class="cal-head">
            <button type="button" class="nav" aria-label="Previous month" @click="go(-1)"><Icon name="left" size="sm" /></button>
            <span class="muted small">{{ count === null ? "" : pluralize(count, "session") }}</span>
            <button type="button" class="nav" aria-label="Next month" :disabled="isCurrent" @click="go(1)">
              <Icon name="right" size="sm" />
            </button>
          </div>
        </template>
      </SessionCalendar>

      <h2 class="eyebrow">Sessions</h2>
      <div v-if="error" class="notice is-error">
        {{ error }}
        <button class="notice-action" @click="load">Retry</button>
      </div>
      <div v-else class="list">
        <p v-if="loading" class="empty">Loading…</p>
        <p v-else-if="sessions.length === 0" class="empty">No sessions this month.</p>
        <SessionRow
          v-for="s in sessions"
          :key="s.id"
          :title="s.title"
          :date="s.date"
          :exercises="s.exercises"
          :to="{ name: 'session-detail', params: { id: s.id } }"
        />
      </div>
    </main>
  </div>
</template>

<style scoped>
.cal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 0 8px;
}
.nav {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  background: var(--card);
  border-radius: var(--r);
}
.nav:disabled {
  opacity: 0.3;
}
</style>
