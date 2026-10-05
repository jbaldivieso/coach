<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { api } from "@/api/client";
import type { Session } from "@/types/lifting";
import { formatDayDate, formatClock } from "@/utils/format";
import { groupUnits, memberLetter } from "@/utils/session";
import AppBar from "@/components/ui/AppBar.vue";
import Btn from "@/components/ui/Btn.vue";
import Icon from "@/components/ui/Icon.vue";
import SetChips from "@/components/ui/SetChips.vue";

const route = useRoute();
const router = useRouter();
const sessionId = computed(() => Number(route.params.id));

const session = ref<Session | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

const units = computed(() => groupUnits(session.value?.exercises ?? []));
const barTitle = computed(() => (session.value ? `${formatDayDate(session.value.date)} · ${session.value.title}` : ""));

async function fetchSession() {
  loading.value = true;
  error.value = null;
  const response = await api.get<Session>(`/api/lifting/sessions/${sessionId.value}/`);
  loading.value = false;
  if (!response.data) {
    error.value = response.error || "Couldn't load the session";
    return;
  }
  // Open sessions belong to Plan and Track
  if (response.data.status === "active") return router.replace({ name: "track", params: { id: response.data.id } });
  if (response.data.status === "planned") return router.replace({ name: "plan-edit", params: { id: response.data.id } });
  session.value = response.data;
}

watch(sessionId, fetchSession, { immediate: true });
</script>

<template>
  <div class="screen">
    <AppBar :title="barTitle" small back="/">
      <template #actions>
        <RouterLink
          v-if="session"
          :to="{ name: 'session-edit', params: { id: session.id } }"
          class="bar-action"
          aria-label="Edit session"
        >
          <Icon name="pencil" />
        </RouterLink>
      </template>
    </AppBar>

    <main class="screen-body">
      <p v-if="loading" class="empty">Loading…</p>
      <div v-else-if="error" class="notice is-error">
        {{ error }}
        <button data-testid="retry-button" class="notice-action" @click="fetchSession">Retry</button>
      </div>
      <template v-else-if="session">
        <p v-if="session.comments" class="session-comments comment">{{ session.comments }}</p>
        <p v-if="session.exercises.length === 0" class="empty">No sets were logged.</p>

        <template v-for="unit in units" :key="unit.start">
          <section v-if="unit.isSuperset" class="ss">
            <header class="ss-h">
              <Icon name="link" size="sm" />Superset<span class="small">rest {{ formatClock(unit.items[0]!.rest_seconds) }}</span>
            </header>
            <article v-for="(e, m) in unit.items" :key="e.id" class="sx">
              <div class="t">
                <RouterLink :to="{ name: 'exercise-history', params: { title: e.title } }" class="link caps">
                  {{ memberLetter(m) }} · {{ e.title }}
                </RouterLink>
              </div>
              <SetChips :sets="e.sets" tone="card" size="lg" />
              <p v-if="e.comments" class="c comment">{{ e.comments }}</p>
            </article>
          </section>
          <article v-else class="sx">
            <div class="t">
              <RouterLink :to="{ name: 'exercise-history', params: { title: unit.items[0]!.title } }" class="link caps">
                {{ unit.items[0]!.title }}
              </RouterLink>
              <small>rest {{ formatClock(unit.items[0]!.rest_seconds) }}</small>
            </div>
            <SetChips :sets="unit.items[0]!.sets" tone="card" size="lg" />
            <p v-if="unit.items[0]!.comments" class="c comment">{{ unit.items[0]!.comments }}</p>
          </article>
        </template>
      </template>
    </main>

    <footer v-if="session" class="dock">
      <Btn variant="primary" size="huge" :to="{ name: 'plan-new', query: { from: session.id } }">
        <Icon name="copy" />Start from this
      </Btn>
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
.session-comments {
  padding: 4px 0 10px;
  border-bottom: 1px solid var(--rule);
}
.sx {
  padding: 12px 0;
  border-bottom: 1px solid var(--rule);
}
.t {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 6px;
}
.t small {
  color: var(--muted);
  font-size: 12.5px;
  white-space: nowrap;
}
.link {
  font-size: 16px;
  text-decoration: underline;
  text-decoration-thickness: 2px;
  text-underline-offset: 4px;
}
.c {
  margin-top: 6px;
  font-size: 13.5px;
}
.ss {
  margin: 12px 0 0;
  border-left: 1px dashed var(--muted);
  padding-left: 10px;
}
.ss-h {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 10px 6px;
  margin-left: -10px;
  background: var(--k);
  color: var(--y);
  font-size: 12.5px;
  font-weight: 800;
  text-transform: uppercase;
  font-stretch: 85%;
  letter-spacing: 0.05em;
}
.ss-h::before {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 5px;
  background: var(--hazard);
}
.ss-h .small {
  margin-left: auto;
  color: var(--on-k);
  text-transform: none;
  font-weight: 500;
  letter-spacing: 0;
  font-stretch: 100%;
}
</style>
