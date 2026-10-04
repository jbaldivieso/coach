<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "@/api/client";
import { useActiveSessionStore } from "@/stores/activeSession";
import { clearExerciseHistory } from "@/composables/useExerciseHistory";
import { pluralize } from "@/utils/format";
import { memberLetter } from "@/utils/session";
import AppBar from "@/components/ui/AppBar.vue";
import Btn from "@/components/ui/Btn.vue";
import Icon from "@/components/ui/Icon.vue";
import SetChips from "@/components/ui/SetChips.vue";

const route = useRoute();
const router = useRouter();
const store = useActiveSessionStore();
const sessionId = computed(() => Number(route.params.id));

const comments = ref("");
const finishing = ref(false);

const summary = computed(() =>
  store.units.map((unit) => ({
    isSuperset: unit.isSuperset,
    rows: unit.items.map((e, m) => {
      const done = e.sets.filter((s) => s.done);
      return {
        title: unit.isSuperset ? `${memberLetter(m)} · ${e.title}` : e.title,
        done,
        total: e.sets.length,
      };
    }),
  })),
);

/** "Incline press (4 sets)", "Leg raises on rings, set 3" */
const dropped = computed(() =>
  store.exercises.flatMap((e) => {
    const undone = e.sets.map((s, i) => (s.done ? -1 : i + 1)).filter((n) => n > 0);
    if (undone.length === 0) return [];
    if (undone.length === e.sets.length) return [`${e.title} (${pluralize(e.sets.length, "set")})`];
    return [`${e.title}, ${undone.length === 1 ? "set" : "sets"} ${undone.join(", ")}`];
  }),
);

const nothingDone = computed(() => store.doneSetCount === 0);

async function finish() {
  finishing.value = true;
  const session = await store.finish(comments.value.trim());
  finishing.value = false;
  if (!session) return;
  clearExerciseHistory();
  router.replace({ name: "session-detail", params: { id: session.id } });
}

async function discard() {
  if (!window.confirm("Throw away this session? Nothing was logged.")) return;
  await api.fetchCsrfToken();
  const response = await api.delete(`/api/lifting/sessions/${sessionId.value}/`);
  if (response.error) {
    store.saveError = response.error;
    return;
  }
  store.endRest();
  router.replace({ name: "home" });
}

onMounted(async () => {
  if (store.session?.id !== sessionId.value) {
    const session = await store.load(sessionId.value);
    if (session && session.status !== "active") router.replace({ name: "session-detail", params: { id: session.id } });
  }
  comments.value = store.session?.comments ?? "";
});
</script>

<template>
  <div class="screen">
    <AppBar :title="`Finish ${store.session?.title ?? ''}`" small :back="{ name: 'track', params: { id: sessionId } }" />

    <main class="screen-body">
      <p v-if="!store.session" class="empty">{{ store.error ?? "Loading…" }}</p>
      <template v-else>
        <div v-if="store.saveError" class="notice is-error" role="alert"><b>Not saved</b>{{ store.saveError }}</div>

        <div class="list">
          <template v-for="(unit, u) in summary" :key="u">
            <div v-for="row in unit.rows" :key="row.title" class="row" :class="{ 'in-superset': unit.isSuperset }">
              <Icon v-if="row.done.length" name="check" size="sm" />
              <Icon v-else name="x" size="sm" class="muted" />
              <div class="row-main">
                <div class="row-title caps">{{ row.title }}</div>
                <SetChips v-if="row.done.length" :sets="row.done" />
                <div v-if="row.done.length < row.total" class="row-sub">
                  {{ row.done.length ? `${row.done.length} of ${row.total} done` : "Not done" }}
                </div>
              </div>
            </div>
          </template>
        </div>

        <div v-if="nothingDone" class="notice">
          <b>Nothing logged yet</b>Finishing now saves an empty session. You can throw it away instead.
          <button class="notice-action" @click="discard">Throw it away</button>
        </div>
        <div v-else-if="dropped.length" class="notice">
          <b>Not done, will be dropped</b>{{ dropped.join(" · ") }}
        </div>

        <h2 class="eyebrow">Session comments</h2>
        <label class="text-field">
          <span class="visually-hidden">Session comments</span>
          <textarea v-model="comments" placeholder="How did it go?" />
        </label>
      </template>
    </main>

    <footer v-if="store.session" class="dock">
      <Btn variant="primary" size="huge" :loading="finishing" @click="finish">Finish session</Btn>
      <Btn :to="{ name: 'track', params: { id: sessionId } }">Keep going</Btn>
    </footer>
  </div>
</template>

<style scoped>
.row {
  align-items: flex-start;
}
.row > svg {
  margin-top: 3px;
}
.row.in-superset {
  border-left: 1px dashed var(--muted);
  padding-left: 10px;
}
.row-title {
  font-size: 15px;
  margin-bottom: 4px;
}
.row-sub {
  margin-top: 4px;
}
</style>
