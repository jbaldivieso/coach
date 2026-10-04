<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { api } from "@/api/client";
import type { SearchResponse } from "@/types/lifting";
import { formatDayDate, formatShortDate, relativeLong, relativeShort, pluralize } from "@/utils/format";
import AppBar from "@/components/ui/AppBar.vue";
import Icon from "@/components/ui/Icon.vue";
import SessionRow from "@/components/SessionRow.vue";

const route = useRoute();
const router = useRouter();

const query = ref(typeof route.query.q === "string" ? route.query.q : "");
const results = ref<SearchResponse | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);
const input = ref<HTMLInputElement | null>(null);
let debounce: ReturnType<typeof setTimeout> | null = null;
let requestId = 0;

/** The top answer: when a matching session title (or else exercise) was last done. */
const answer = computed(() => {
  const r = results.value;
  if (!r) return null;
  if (r.last_session) {
    return {
      lead: `Last session titled “${query.value.trim()}”`,
      when: relativeLong(r.last_session.date),
      detail: `${formatDayDate(r.last_session.date)} · ${r.last_session.title}`,
      to: { name: "session-detail", params: { id: r.last_session.id } },
    };
  }
  const top = r.exercises[0];
  if (top?.last_date) {
    return {
      lead: `Last ${top.title}`,
      when: relativeLong(top.last_date),
      detail: `${formatDayDate(top.last_date)} · ${pluralize(top.count, "time")} in all`,
      to: { name: "exercise-history", params: { title: top.title } },
    };
  }
  return null;
});

async function search() {
  const q = query.value.trim();
  router.replace({ query: q ? { q } : {} });
  if (!q) {
    results.value = null;
    return;
  }
  const id = ++requestId;
  loading.value = true;
  const response = await api.get<SearchResponse>(`/api/lifting/search/?q=${encodeURIComponent(q)}`);
  if (id !== requestId) return;
  loading.value = false;
  if (response.data) {
    results.value = response.data;
    error.value = null;
  } else {
    error.value = response.error || "Search failed";
  }
}

watch(query, () => {
  if (debounce) clearTimeout(debounce);
  debounce = setTimeout(search, 220);
});

onMounted(() => {
  if (query.value) search();
  else input.value?.focus();
});
</script>

<template>
  <div class="screen">
    <AppBar back="/">
      <template #title>
        <label class="text-field bar-field">
          <Icon name="search" size="sm" />
          <span class="visually-hidden">Search</span>
          <input
            ref="input"
            v-model="query"
            type="search"
            placeholder="Session or exercise"
            autocomplete="off"
            enterkeyhint="search"
          />
        </label>
      </template>
    </AppBar>

    <main class="screen-body">
      <div v-if="error" class="notice is-error">
        {{ error }}
        <button class="notice-action" @click="search">Retry</button>
      </div>
      <p v-else-if="!query.trim()" class="empty">When did I last… Search a session title or an exercise.</p>
      <p v-else-if="loading && !results" class="empty">Searching…</p>
      <template v-else-if="results">
        <RouterLink v-if="answer" :to="answer.to" class="answer">
          <span class="small">{{ answer.lead }}</span>
          <b>{{ answer.when }}</b>
          <span class="small">{{ answer.detail }}</span>
        </RouterLink>
        <p v-if="!results.sessions.length && !results.exercises.length" class="empty">
          Nothing matches “{{ query.trim() }}”.
        </p>

        <template v-if="results.sessions.length">
          <h2 class="eyebrow">Sessions</h2>
          <div class="list">
            <SessionRow
              v-for="s in results.sessions"
              :key="s.id"
              :title="s.title"
              :date="s.date"
              date-caption="month"
              :to="{ name: 'session-detail', params: { id: s.id } }"
            >
              <span class="muted small age">{{ relativeShort(s.date) }}</span>
            </SessionRow>
          </div>
        </template>

        <template v-if="results.exercises.length">
          <h2 class="eyebrow">Exercises</h2>
          <div class="list">
            <RouterLink
              v-for="e in results.exercises"
              :key="e.title"
              :to="{ name: 'exercise-history', params: { title: e.title } }"
              class="row"
            >
              <div class="row-main">
                <div class="row-title">{{ e.title }}</div>
                <div class="row-sub">
                  {{ e.last_date ? `Last ${formatShortDate(e.last_date)} · ` : "" }}{{ pluralize(e.count, "time") }}
                </div>
              </div>
              <Icon name="right" size="sm" class="muted" />
            </RouterLink>
          </div>
        </template>
      </template>
    </main>
  </div>
</template>

<style scoped>
.bar-field {
  flex: 1;
  min-height: 40px;
  border-color: var(--k);
}
.answer {
  display: block;
  background: var(--k);
  color: var(--on-k);
  border-radius: var(--r-lg);
  padding: 12px 14px;
  margin: 4px 0 6px;
}
.answer .small {
  display: block;
  color: var(--on-k-muted);
}
.answer b {
  display: block;
  color: var(--y);
  font-size: 30px;
  font-weight: 800;
  line-height: 1.1;
  text-transform: uppercase;
  font-stretch: 85%;
}
.age {
  white-space: nowrap;
}
</style>
