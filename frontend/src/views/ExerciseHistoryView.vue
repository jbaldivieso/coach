<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { RouterLink, useRoute } from "vue-router";
import { api } from "@/api/client";
import type { ExerciseHistory, Outing } from "@/types/lifting";
import { formatDayDate, formatShortDate, formatMonthYear, relativeShort, pluralize } from "@/utils/format";
import AppBar from "@/components/ui/AppBar.vue";
import Btn from "@/components/ui/Btn.vue";
import SetChips from "@/components/ui/SetChips.vue";
import ExerciseChart from "@/components/ExerciseChart.vue";

const PAGE_SIZE = 30;

const route = useRoute();
const title = computed(() => String(route.params.title));

const outings = ref<Outing[]>([]);
const total = ref(0);
const hasMore = ref(false);
const first = ref<Outing | null>(null); // the oldest outing, for "since Oct 2025"
const loading = ref(true);
const loadingMore = ref(false);
const error = ref<string | null>(null);

async function fetchPage(offset: number, limit = PAGE_SIZE): Promise<ExerciseHistory | null> {
  const params = new URLSearchParams({ title: title.value, limit: String(limit), offset: String(offset) });
  const response = await api.get<ExerciseHistory>(`/api/lifting/exercises/history/?${params}`);
  if (!response.data) error.value = response.error || "Couldn't load the history";
  return response.data;
}

async function load() {
  loading.value = true;
  error.value = null;
  outings.value = [];
  first.value = null;
  const page = await fetchPage(0);
  loading.value = false;
  if (!page) return;
  outings.value = page.items;
  total.value = page.total;
  hasMore.value = page.has_more;
  if (page.has_more) {
    const oldest = await fetchPage(page.total - 1, 1);
    first.value = oldest?.items[0] ?? null;
  } else {
    first.value = page.items[page.items.length - 1] ?? null;
  }
}

async function loadMore() {
  loadingMore.value = true;
  const page = await fetchPage(outings.value.length);
  loadingMore.value = false;
  if (!page) return;
  outings.value = [...outings.value, ...page.items];
  hasMore.value = page.has_more;
}

const summary = computed(() => {
  const latest = outings.value[0];
  if (!latest) return "";
  const since = first.value ? ` since ${formatMonthYear(first.value.date)}` : "";
  return `${pluralize(total.value, "time")}${since} · last ${formatShortDate(latest.date)}`;
});

watch(title, load, { immediate: true });
</script>

<template>
  <div class="screen">
    <AppBar :title="title" back="/" />
    <main class="screen-body">
      <p v-if="loading" class="empty">Loading…</p>
      <div v-else-if="error" class="notice is-error">
        {{ error }}
        <button class="notice-action" @click="load">Retry</button>
      </div>
      <p v-else-if="outings.length === 0" class="empty">No finished sessions have “{{ title }}” yet.</p>
      <template v-else>
        <p class="muted small">{{ summary }}</p>
        <ExerciseChart :outings="outings.slice(0, PAGE_SIZE)" />

        <article v-for="o in outings" :key="o.exercise_id" class="outing">
          <RouterLink :to="{ name: 'session-detail', params: { id: o.session_id } }" class="h">
            <span>{{ formatDayDate(o.date) }} · {{ o.session_title }}</span>
            <span class="muted">{{ relativeShort(o.date) }}</span>
          </RouterLink>
          <SetChips :sets="o.sets" tone="card" size="lg" />
          <p v-if="o.comments" class="comment c">{{ o.comments }}</p>
        </article>
        <Btn v-if="hasMore" class="load-more" :loading="loadingMore" @click="loadMore">Older outings</Btn>
      </template>
    </main>
  </div>
</template>

<style scoped>
.outing {
  padding: 10px 0;
  border-bottom: 1px solid var(--rule);
  font-size: 13.5px;
}
.h {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  min-height: 32px;
  align-items: center;
  font-size: 12.5px;
  font-weight: 600;
}
.c {
  margin-top: 4px;
}
.load-more {
  width: 100%;
  margin-top: 12px;
}
</style>
