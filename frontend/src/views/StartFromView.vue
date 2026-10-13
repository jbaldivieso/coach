<script setup lang="ts">
import { ref, watch, onMounted } from "vue";
import { api } from "@/api/client";
import type { Session, PaginatedSessions } from "@/types/lifting";
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

watch(query, () => {
  if (debounce) clearTimeout(debounce);
  debounce = setTimeout(() => fetchSessions(), 200);
});

onMounted(() => fetchSessions());
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

      <div v-if="error" class="notice is-error">
        {{ error }}
        <button class="notice-action" @click="fetchSessions()">Retry</button>
      </div>
      <div class="list results">
        <div v-if="loading" class="empty">Loading…</div>
        <div v-else-if="sessions.length === 0" class="empty">
          {{ query ? `Nothing matches "${query}".` : "No past sessions yet." }}
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
