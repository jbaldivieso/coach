<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { RouterLink, useRouter } from "vue-router";
import { api } from "@/api/client";
import type { Session, PaginatedSessions } from "@/types/lifting";
import { todayISO, formatDayDate, pluralize } from "@/utils/format";
import { currentPosition, groupUnits, roundCount } from "@/utils/session";
import AppBar from "@/components/ui/AppBar.vue";
import Btn from "@/components/ui/Btn.vue";
import Icon from "@/components/ui/Icon.vue";
import SessionCalendar from "@/components/SessionCalendar.vue";
import SessionRow from "@/components/SessionRow.vue";

const router = useRouter();

const PAGE_SIZE = 10;
const now = new Date();
const year = now.getFullYear();
const month = now.getMonth() + 1;
const monthLabel = now.toLocaleDateString("en-US", { month: "long", year: "numeric" });

const openSessions = ref<Session[]>([]);
const sessions = ref<Session[]>([]);
const hasMore = ref(false);
const loading = ref(true);
const loadingMore = ref(false);
const error = ref<string | null>(null);
const startingId = ref<number | null>(null);

const active = computed(() => openSessions.value.filter((s) => s.status === "active"));
const planned = computed(() => openSessions.value.filter((s) => s.status === "planned"));

function resumeDetail(session: Session): string {
  const parts: string[] = [];
  const position = currentPosition(session.exercises);
  if (position) {
    const unit = groupUnits(session.exercises)[position.unitIndex]!;
    const exercise = session.exercises[position.exerciseIndex]!;
    parts.push(`${exercise.title} · set ${position.round + 1} of ${roundCount(unit)}`);
  } else {
    parts.push("All sets done");
  }
  if (session.started_at) {
    const started = new Date(session.started_at);
    parts.push(`started ${started.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" })}`);
  }
  return parts.join(" · ");
}

function plannedDetail(session: Session): string {
  const when = session.date === todayISO() ? "Today" : formatDayDate(session.date);
  return `${when} · ${pluralize(session.exercises.length, "exercise")}`;
}

async function startPlanned(session: Session) {
  startingId.value = session.id;
  await api.fetchCsrfToken();
  const response = await api.post<Session>(`/api/lifting/sessions/${session.id}/start/`, { date: todayISO() });
  startingId.value = null;
  if (response.data) {
    router.push({ name: "track", params: { id: session.id } });
  } else {
    error.value = response.error || "Couldn't start that session";
  }
}

async function fetchOpen() {
  const response = await api.get<Session[]>("/api/lifting/sessions/open/");
  if (response.data) openSessions.value = response.data;
}

async function fetchSessions(append = false) {
  if (append) loadingMore.value = true;
  error.value = null;
  try {
    const offset = append ? sessions.value.length : 0;
    const response = await api.get<PaginatedSessions>(`/api/lifting/sessions/?offset=${offset}&limit=${PAGE_SIZE}`);
    if (response.data) {
      sessions.value = append ? [...sessions.value, ...response.data.items] : response.data.items;
      hasMore.value = response.data.has_more;
    } else {
      error.value = response.error || "Couldn't load sessions";
    }
  } catch {
    error.value = "Network error. Try again.";
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
}

onMounted(() => {
  fetchOpen();
  fetchSessions();
});
</script>

<template>
  <div class="screen">
    <AppBar title="Coach">
      <template #actions>
        <RouterLink to="/search" class="bar-action" aria-label="Search"><Icon name="search" /></RouterLink>
      </template>
    </AppBar>

    <main class="screen-body">
      <RouterLink
        v-for="s in active"
        :key="s.id"
        :to="{ name: 'track', params: { id: s.id } }"
        class="open-card"
      >
        <Icon name="play" />
        <span class="open-main">
          <b>Resume {{ s.title }}</b>
          <small>{{ resumeDetail(s) }}</small>
        </span>
        <Icon name="right" />
      </RouterLink>

      <div v-for="s in planned" :key="s.id" class="open-card">
        <RouterLink :to="{ name: 'plan-edit', params: { id: s.id } }" class="open-main">
          <b>Planned · {{ s.title }}</b>
          <small>{{ plannedDetail(s) }}</small>
        </RouterLink>
        <Btn variant="primary" size="small" :loading="startingId === s.id" @click="startPlanned(s)">Start</Btn>
      </div>

      <SessionCalendar :year="year" :month="month">
        <template #header="{ count }">
          <div class="cal-head">
            <RouterLink to="/history/year" class="cal-month" aria-label="Open the past year">
              {{ monthLabel }} <Icon name="down" size="sm" />
            </RouterLink>
            <span v-if="count !== null" class="muted small">{{ pluralize(count, "session") }}</span>
          </div>
        </template>
      </SessionCalendar>

      <h2 class="eyebrow">Recent</h2>
      <div v-if="error" class="notice is-error">
        {{ error }}
        <button class="notice-action" @click="fetchSessions()">Retry</button>
      </div>
      <div v-else-if="loading" class="list"><div class="empty">Loading…</div></div>
      <div v-else-if="sessions.length === 0" class="list">
        <div class="empty">No sessions yet. Start one below.</div>
      </div>
      <div v-else class="list">
        <SessionRow
          v-for="s in sessions"
          :key="s.id"
          :title="s.title"
          :date="s.date"
          :exercises="s.exercises"
          :to="{ name: 'session-detail', params: { id: s.id } }"
        />
      </div>
      <Btn v-if="hasMore" class="load-more" :loading="loadingMore" @click="fetchSessions(true)">Load more</Btn>
    </main>

    <footer class="dock">
      <div class="dock-pair">
        <Btn to="/plan/new"><Icon name="plus" />Blank</Btn>
        <Btn to="/start" variant="primary"><Icon name="copy" />Start from…</Btn>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.bar-action {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: var(--r);
}
.open-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--k);
  color: var(--y);
  border-radius: var(--r-lg);
  padding: 12px 14px;
  margin-bottom: 10px;
  min-height: 60px;
}
.open-main {
  flex: 1;
  min-width: 0;
}
.open-main b {
  display: block;
  font-size: 16px;
}
.open-main small {
  display: block;
  color: var(--on-k);
  opacity: 0.85;
  font-size: 12.5px;
}
.cal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 4px 0 8px;
}
.cal-month {
  display: flex;
  align-items: center;
  gap: 4px;
  min-height: 44px;
  font-size: 16px;
  font-weight: 800;
  text-transform: uppercase;
  font-stretch: 85%;
  letter-spacing: 0.04em;
}
.load-more {
  margin-top: 12px;
  width: 100%;
}
</style>
