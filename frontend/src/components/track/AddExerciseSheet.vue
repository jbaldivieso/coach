<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { api } from "@/api/client";
import type { TitleSuggestion, TitleSuggestions } from "@/types/lifting";
import { useActiveSessionStore, type Placement } from "@/stores/activeSession";
import { useExerciseHistory } from "@/composables/useExerciseHistory";
import { formatShortDate } from "@/utils/format";
import { unitTitle } from "@/utils/session";
import { DEFAULT_REST, MAX_SETS } from "@/utils/plan";
import Sheet from "@/components/ui/Sheet.vue";
import Autocomplete from "@/components/ui/Autocomplete.vue";
import SetChips from "@/components/ui/SetChips.vue";
import Btn from "@/components/ui/Btn.vue";
import CountControl from "@/components/plan/CountControl.vue";

const props = defineProps<{ open: boolean }>();
const emit = defineEmits<{ close: [] }>();

const store = useActiveSessionStore();
const history = useExerciseHistory({ limit: 1, excludeSession: () => store.session?.id ?? null });

const title = ref("");
const committed = ref("");
const count = ref(3);
const placement = ref<Placement>("next");
const adding = ref(false);

const last = computed(() => history.get(committed.value)?.items[0] ?? null);
const upcoming = computed(() => store.upcomingUnit);
const sets = computed(() => {
  const source = last.value?.sets.length ? last.value.sets : [{ weight: null, reps: 0 }];
  return Array.from({ length: count.value }, (_, i) => {
    const s = source[Math.min(i, source.length - 1)]!;
    return { weight: s.weight, reps: s.reps };
  });
});
const effectiveCount = computed(() =>
  placement.value === "superset" && upcoming.value ? Math.max(...upcoming.value.items.map((e) => e.sets.length)) : count.value,
);

watch(
  () => props.open,
  (open) => {
    if (!open) return;
    title.value = "";
    committed.value = "";
    count.value = 3;
    placement.value = store.currentUnit ? "next" : "end";
  },
);

async function fetchTitles(q: string): Promise<TitleSuggestion[]> {
  const response = await api.get<TitleSuggestions>(`/api/lifting/exercises/autocomplete/?q=${encodeURIComponent(q)}`);
  return response.data?.suggestions ?? [];
}

async function commit(name: string) {
  committed.value = name.trim();
  const entry = await history.load(committed.value);
  const outing = entry?.items[0];
  if (outing && committed.value === name.trim()) count.value = Math.min(MAX_SETS, Math.max(1, outing.sets.length));
}

async function add() {
  if (!committed.value) return;
  adding.value = true;
  const ok = await store.addExercise(
    { title: committed.value, sets: sets.value, rest_seconds: last.value?.rest_seconds ?? DEFAULT_REST },
    placement.value,
  );
  adding.value = false;
  if (ok) emit("close");
}
</script>

<template>
  <Sheet :open="open" title="Add exercise" @close="emit('close')">
    <div class="text-field name">
      <Autocomplete
        v-model="title"
        :fetch="fetchTitles"
        label="Exercise name"
        placeholder="Exercise name"
        suggest-on-focus
        @pick="(s) => commit(s.title)"
        @commit="commit"
      />
    </div>

    <template v-if="committed">
      <p class="sub">{{ last ? `Last time · ${formatShortDate(last.date)}` : "First time" }}</p>
      <SetChips v-if="last" :sets="last.sets" />
      <div class="count-row">
        <span class="sub">Sets</span>
        <CountControl v-if="placement !== 'superset'" :count="count" noun="set" @change="(n) => (count = n)" />
        <span v-else class="small muted">Matches the superset</span>
      </div>
    </template>

    <p class="sub">Put it</p>
    <div class="seg" role="radiogroup" aria-label="Where to put it">
      <button type="button" role="radio" :aria-checked="placement === 'next'" :class="{ on: placement === 'next' }" :disabled="!store.currentUnit" @click="placement = 'next'">
        Next
      </button>
      <button type="button" role="radio" :aria-checked="placement === 'end'" :class="{ on: placement === 'end' }" @click="placement = 'end'">
        At the end
      </button>
      <button
        type="button"
        role="radio"
        :aria-checked="placement === 'superset'"
        :class="{ on: placement === 'superset' }"
        :disabled="!upcoming"
        @click="placement = 'superset'"
      >
        {{ upcoming ? `Superset with ${unitTitle(upcoming)}` : "Superset (nothing up next)" }}
      </button>
    </div>

    <Btn variant="primary" size="huge" class="add" :disabled="!committed" :loading="adding" @click="add">
      Add · {{ effectiveCount }} {{ effectiveCount === 1 ? "set" : "sets" }}
    </Btn>
  </Sheet>
</template>

<style scoped>
.name {
  border-width: 2px;
  border-color: var(--k);
}
.name :deep(input) {
  border: 0;
  outline: none;
  background: transparent;
  font-size: 16px;
  padding: 10px 0;
}
.sub {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  font-stretch: 85%;
  color: var(--muted);
  margin: 14px 0 6px;
}
.count-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.seg {
  display: grid;
  grid-template-columns: 1fr 1fr 1.6fr;
  border: 1.5px solid var(--k);
  border-radius: var(--r);
  overflow: hidden;
}
.seg button {
  min-height: 48px;
  padding: 6px 4px;
  font-size: 12.5px;
  font-weight: 600;
  line-height: 1.2;
  border-right: 1.5px solid var(--k);
}
.seg button:last-child {
  border-right: 0;
}
.seg button.on {
  background: var(--k);
  color: var(--y);
}
.seg button:disabled {
  color: var(--muted);
  opacity: 0.6;
}
.add {
  width: 100%;
  margin-top: 16px;
}
</style>
