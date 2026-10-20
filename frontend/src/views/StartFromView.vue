<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { api } from "@/api/client";
import type { Session, PaginatedSessions, Template } from "@/types/lifting";
import AppBar from "@/components/ui/AppBar.vue";
import Btn from "@/components/ui/Btn.vue";
import Icon from "@/components/ui/Icon.vue";
import SessionRow from "@/components/SessionRow.vue";

const PAGE_SIZE = 25;

const query = ref("");
const sessions = ref<Session[]>([]);
const hasMore = ref(false);
const loading = ref(true);
const error = ref<string | null>(null);
const templates = ref<Template[]>([]);
let debounce: ReturnType<typeof setTimeout> | null = null;
let requestId = 0;

async function fetchSessions(append = false) {
  const id = ++requestId;
  const offset = append ? sessions.value.length : 0;
  const q = encodeURIComponent(query.value.trim());
  const response = await api.get<PaginatedSessions>(
    `/api/lifting/sessions/?offset=${offset}&limit=${PAGE_SIZE}&q=${q}`,
  );
  if (id !== requestId) return; // a newer search superseded this one
  loading.value = false;
  if (response.data) {
    error.value = null;
    sessions.value = append ? [...sessions.value, ...response.data.items] : response.data.items;
    hasMore.value = response.data.has_more;
  } else {
    error.value = response.error || "Couldn't load sessions";
  }
}

// Few enough to fetch once and filter here
async function fetchTemplates() {
  const response = await api.get<Template[]>("/api/lifting/templates/");
  if (response.data) templates.value = response.data;
}

const shownTemplates = computed(() => {
  const q = query.value.trim().toLowerCase();
  if (!q) return templates.value;
  return templates.value.filter(
    (t) => t.title.toLowerCase().includes(q) || t.exercises.some((e) => e.title.toLowerCase().includes(q)),
  );
});

watch(query, () => {
  if (debounce) clearTimeout(debounce);
  debounce = setTimeout(() => fetchSessions(), 200);
});

onMounted(() => {
  fetchTemplates();
  fetchSessions();
});
</script>

<template>
  <div class="screen">
    <AppBar title="Start from…" back="/" />
    <main class="screen-body">
      <label class="text-field">
        <Icon name="search" size="sm" />
        <span class="visually-hidden">Filter sessions</span>
        <input v-model="query" type="search" placeholder="Title or exercise" autocomplete="off" />
      </label>

      <template v-if="shownTemplates.length">
        <h2 class="eyebrow">Templates</h2>
        <div class="list templates">
          <SessionRow
            v-for="t in shownTemplates"
            :key="t.id"
            :title="t.title"
            :exercises="t.exercises"
            chevron
            :to="{ name: 'plan-new', query: { template: t.id } }"
          />
        </div>
        <h2 class="eyebrow">Past sessions</h2>
      </template>

      <div v-if="error" class="notice is-error">
        {{ error }}
        <button class="notice-action" @click="fetchSessions()">Retry</button>
      </div>
      <div class="list results">
        <div v-if="loading" class="empty">Loading…</div>
        <div v-else-if="sessions.length === 0" class="empty">
          <template v-if="!query">No past sessions yet.</template>
          <template v-else-if="shownTemplates.length">No past sessions match "{{ query }}".</template>
          <template v-else>Nothing matches "{{ query }}".</template>
        </div>
        <SessionRow
          v-for="s in sessions"
          :key="s.id"
          :title="s.title"
          :date="s.date"
          :exercises="s.exercises"
          date-caption="month"
          chevron
          :to="{ name: 'plan-new', query: { from: s.id } }"
        />
      </div>
      <Btn v-if="hasMore" class="load-more" @click="fetchSessions(true)">Load more</Btn>
    </main>
  </div>
</template>

<style scoped>
.results {
  margin-top: 8px;
}
.load-more {
  margin-top: 12px;
  width: 100%;
}
</style>
