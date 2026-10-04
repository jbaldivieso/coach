<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from "vue";
import { RouterLink, useRoute, useRouter } from "vue-router";
import { useActiveSessionStore } from "@/stores/activeSession";
import { useExerciseHistory } from "@/composables/useExerciseHistory";
import type { SetValues } from "@/types/lifting";
import { formatSet, formatClock, formatShortDate } from "@/utils/format";
import { memberLetter, roundCount, unitTitle } from "@/utils/session";
import { clearUndoHistory } from "@/utils/ios";
import { unlockAudio } from "@/utils/audio";
import AppBar from "@/components/ui/AppBar.vue";
import Btn from "@/components/ui/Btn.vue";
import Icon from "@/components/ui/Icon.vue";
import SetChips from "@/components/ui/SetChips.vue";
import Sheet from "@/components/ui/Sheet.vue";
import Stepper from "@/components/ui/Stepper.vue";
import RestTimer from "@/components/RestTimer.vue";
import AddExerciseSheet from "@/components/track/AddExerciseSheet.vue";

const route = useRoute();
const router = useRouter();
const store = useActiveSessionStore();
const sessionId = computed(() => Number(route.params.id));
const lastTime = useExerciseHistory({ limit: 1, excludeSession: () => sessionId.value });

const restVisible = ref(false);
const addOpen = ref(false);
const noteFor = ref<number | null>(null); // exercise index
const editing = ref<{ exerciseIndex: number; setIndex: number; values: SetValues }[] | null>(null);
const logging = ref(false);
const strip = ref<HTMLElement | null>(null);

// What's on screen now
const position = computed(() => store.position);
const unit = computed(() => store.currentUnit);
const exercise = computed(() => (position.value ? store.exercises[position.value.exerciseIndex]! : null));
const target = computed(() => (position.value && exercise.value ? exercise.value.sets[position.value.round]! : null));
const memberIndex = computed(() => (unit.value && position.value ? position.value.exerciseIndex - unit.value.start : 0));
const rounds = computed(() => (unit.value ? roundCount(unit.value) : 0));
const rest = computed(() => unit.value?.items[0]?.rest_seconds ?? 0);
const undoneCount = computed(() => store.exercises.reduce((n, e) => n + e.sets.filter((s) => !s.done).length, 0));

// The numbers being logged start at the target and are adjusted with the steppers
const weight = ref<number | null>(null);
const reps = ref<number | null>(0);
watch(
  () => (position.value ? `${position.value.exerciseIndex}:${position.value.round}` : ""),
  () => {
    weight.value = target.value?.weight ?? null;
    reps.value = target.value?.reps ?? 0;
  },
  { immediate: true },
);

watch(
  () => exercise.value?.title,
  (title) => title && lastTime.load(title),
  { immediate: true },
);
const lastOuting = computed(() => (exercise.value ? (lastTime.get(exercise.value.title)?.items[0] ?? null) : null));

const isFinalSet = computed(() => undoneCount.value === 1);
const isLastInRound = computed(() => {
  if (!unit.value || !position.value) return true;
  const round = position.value.round;
  return unit.value.items.slice(memberIndex.value + 1).every((e) => !e.sets[round] || e.sets[round]!.done);
});

const doneLabel = computed(() => {
  const values = formatSet({ weight: weight.value, reps: reps.value ?? 0 });
  if (!unit.value?.isSuperset) return isFinalSet.value ? `Done · ${values} · finish` : `Done · ${values}`;
  const letter = memberLetter(memberIndex.value);
  if (isFinalSet.value) return `Done ${letter} · finish`;
  return isLastInRound.value ? `Done ${letter} · start rest` : `Done ${letter}`;
});

const subline = computed(() => {
  if (!position.value) return "";
  const n = position.value.round + 1;
  if (unit.value?.isSuperset) {
    const lastLetter = memberLetter(unit.value.items.length - 1);
    return `Round ${n} of ${rounds.value} · ${formatClock(rest.value)} rest after ${lastLetter}`;
  }
  return `Set ${n} of ${rounds.value} · rest ${formatClock(rest.value)}`;
});

/** "Set 4 · 155 × 5", or the next exercise, for the rest screen. */
const nextLine = computed(() => {
  if (!position.value || !target.value || !exercise.value) return "Finish";
  const set = formatSet(target.value);
  if (unit.value?.isSuperset) return `Round ${position.value.round + 1} · ${exercise.value.title} · ${set}`;
  return `${exercise.value.title} · Set ${position.value.round + 1} · ${set}`;
});
const goLabel = computed(() => {
  if (!position.value) return "Finish";
  if (unit.value?.isSuperset) return `Go to round ${position.value.round + 1}`;
  return `Go to set ${position.value.round + 1}`;
});

// ---------- Logging ----------

async function done() {
  if (!position.value || logging.value) return;
  // Inside the tap, so iOS lets the rest-over alarm play later
  unlockAudio();
  clearUndoHistory();
  const { exerciseIndex, round } = position.value;
  const finishing = isFinalSet.value;
  const startsRest = isLastInRound.value;
  const restSeconds = rest.value;
  const label = unit.value ? unitTitle(unit.value) : "";
  logging.value = true;
  const ok = await store.logSet(exerciseIndex, round, { weight: weight.value, reps: reps.value ?? 0 });
  logging.value = false;
  if (finishing && ok) {
    router.push({ name: "track-finish", params: { id: sessionId.value } });
  } else if (startsRest && restSeconds > 0) {
    store.startRest(restSeconds, label);
    restVisible.value = true;
  }
}

function endRest() {
  store.endRest();
  restVisible.value = false;
}

// ---------- Ledger and corrections ----------

interface LedgerRow {
  label: string;
  text: string;
  done: boolean;
  now: boolean;
  round: number;
}

const ledger = computed((): LedgerRow[] => {
  if (!unit.value || !position.value) return [];
  const current = position.value;
  return Array.from({ length: rounds.value }, (_, r) => {
    const parts = unit.value!.items.map((e, m) => {
      const set = e.sets[r];
      if (!set) return "–";
      const live = r === current.round && unit.value!.start + m === current.exerciseIndex;
      return formatSet(live ? { weight: weight.value, reps: reps.value ?? 0 } : set);
    });
    return {
      label: `${unit.value!.isSuperset ? "Round" : "Set"} ${r + 1}`,
      text: parts.join(" · "),
      done: unit.value!.items.every((e) => !e.sets[r] || e.sets[r]!.done),
      now: r === current.round,
      round: r,
    };
  });
});

function openEdit(round: number) {
  if (!unit.value) return;
  editing.value = unit.value.items
    .map((e, m) => ({ e, index: unit.value!.start + m }))
    .filter(({ e }) => e.sets[round]?.done)
    .map(({ e, index }) => ({ exerciseIndex: index, setIndex: round, values: { weight: e.sets[round]!.weight, reps: e.sets[round]!.reps } }));
}

async function saveEdit() {
  const items = editing.value ?? [];
  editing.value = null;
  for (const item of items) await store.editSet(item.exerciseIndex, item.setIndex, item.values);
}

// ---------- Notes ----------

const noteText = computed({
  get: () => (noteFor.value !== null ? (store.exercises[noteFor.value]?.comments ?? "") : ""),
  set: (text: string) => {
    if (noteFor.value !== null) store.saveNote(noteFor.value, text);
  },
});

function openNote(index: number | undefined) {
  if (index !== undefined) noteFor.value = index;
}

// ---------- Progress strip ----------

const stripItems = computed(() =>
  store.units.map((u, i) => ({
    label: u.isSuperset ? u.items.map((e) => e.title).join(" + ") : u.items[0]!.title,
    done: u.items.every((e) => e.sets.every((s) => s.done)),
    current: i === position.value?.unitIndex,
  })),
);

watch(
  () => position.value?.unitIndex,
  async () => {
    await nextTick();
    strip.value?.querySelector(".is-current")?.scrollIntoView({ inline: "center", block: "nearest", behavior: "smooth" });
  },
);

// ---------- Rest banner while the rest screen is hidden ----------

const now = ref(Date.now());
let ticker: number | null = null;
const restLeft = computed(() => formatClock(Math.ceil(store.remaining(now.value))));

onMounted(async () => {
  ticker = window.setInterval(() => (now.value = Date.now()), 500);
  const session = await store.load(sessionId.value);
  if (!session) return;
  if (session.status === "planned") return router.replace({ name: "plan-edit", params: { id: session.id } });
  if (session.status === "done") return router.replace({ name: "session-detail", params: { id: session.id } });
  // Back after iOS killed the app mid-rest
  if (store.rest) restVisible.value = true;
});

onUnmounted(() => {
  if (ticker) clearInterval(ticker);
  store.flushNotes();
});
</script>

<template>
  <div class="screen track">
    <AppBar :title="store.session?.title ?? ''" small back="/">
      <template #actions>
        <Btn size="small" :to="{ name: 'track-finish', params: { id: sessionId } }">Finish</Btn>
      </template>
    </AppBar>

    <main class="screen-body">
      <p v-if="store.loading && !store.session" class="empty">Loading…</p>
      <div v-else-if="store.error" class="notice is-error">
        {{ store.error }}
        <button class="notice-action" @click="store.load(sessionId)">Retry</button>
      </div>

      <template v-else-if="store.session">
        <div v-if="store.saveError" class="notice is-error" role="alert">
          <b>Not saved</b>{{ store.saveError }}
          <button v-if="store.unsaved.length" class="notice-action" @click="store.retry()">
            Retry {{ store.unsaved.length === 1 ? "the set" : `${store.unsaved.length} sets` }}
          </button>
        </div>

        <button v-if="store.rest && !restVisible" type="button" class="rest-pill" @click="restVisible = true">
          <Icon name="clock" size="sm" /><span>Rest {{ restLeft }}</span><b>Show</b>
        </button>

        <div class="prog-wrap">
          <nav ref="strip" class="prog" aria-label="Exercises">
            <button
              v-for="(item, i) in stripItems"
              :key="i"
              type="button"
              class="prog-chip"
              :class="{ 'is-done': item.done, 'is-current': item.current }"
              :aria-current="item.current ? 'step' : undefined"
              @click="store.jumpTo(i)"
            >
              <Icon v-if="item.done" name="check" size="sm" />{{ item.label }}
            </button>
          </nav>
          <button type="button" class="prog-add" aria-label="Add exercise" @click="addOpen = true">
            <Icon name="plus" size="sm" />
          </button>
        </div>

        <div v-if="!position" class="all-done">
          <p class="trk-name">All done</p>
          <p class="trk-sub">Every set is logged.</p>
          <Btn variant="primary" size="huge" :to="{ name: 'track-finish', params: { id: sessionId } }">Finish session</Btn>
          <Btn class="mt" @click="addOpen = true"><Icon name="plus" />Add exercise</Btn>
        </div>

        <template v-else-if="exercise && unit">
          <!-- One exercise -->
          <template v-if="!unit.isSuperset">
            <RouterLink :to="{ name: 'exercise-history', params: { title: exercise.title } }" class="trk-name">
              {{ exercise.title }}
            </RouterLink>
            <p class="trk-sub">{{ subline }}</p>
            <div class="dials">
              <Stepper v-model="weight" label="weight" unit="lb" :step="5" decimal nullable />
              <Stepper v-model="reps" label="reps" unit="reps" :step="1" />
            </div>
          </template>

          <!-- Superset round -->
          <template v-else>
            <p class="trk-name is-small">Superset</p>
            <p class="trk-sub">{{ subline }}</p>
            <div class="round">
              <div
                v-for="(e, m) in unit.items"
                :key="e.id"
                class="rcard"
                :class="{ 'is-current': m === memberIndex }"
              >
                <div class="top">
                  <span class="tag">{{ memberLetter(m) }} · {{ m === memberIndex ? "now" : e.title }}</span>
                  <span v-if="e.sets[position.round]?.done" class="donebadge">
                    <Icon name="check" size="sm" />{{ formatSet(e.sets[position.round]!) }}
                  </span>
                  <span v-else-if="e.sets[position.round]">target {{ formatSet(e.sets[position.round]!) }}</span>
                </div>
                <template v-if="m === memberIndex">
                  <RouterLink :to="{ name: 'exercise-history', params: { title: e.title } }" class="nm">{{ e.title }}</RouterLink>
                  <div class="dials">
                    <Stepper v-model="weight" label="weight" unit="lb" :step="5" decimal nullable />
                    <Stepper v-model="reps" label="reps" unit="reps" :step="1" />
                  </div>
                </template>
              </div>
            </div>
          </template>

          <div class="ledger" role="list">
            <component
              :is="row.done ? 'button' : 'div'"
              v-for="row in ledger"
              :key="row.round"
              role="listitem"
              class="ledger-row"
              :class="{ 'is-now': row.now && !row.done, 'is-done': row.done }"
              :type="row.done ? 'button' : undefined"
              :aria-label="row.done ? `${row.label}: ${row.text}. Tap to correct.` : undefined"
              @click="row.done && openEdit(row.round)"
            >
              <span class="n">{{ row.label }}</span>
              <span class="v">{{ row.text }}</span>
              <Icon v-if="row.done" name="check" size="sm" />
              <span v-else />
            </component>
          </div>
          <button v-if="rounds < 6" type="button" class="add-set" @click="store.addSet(position.exerciseIndex)">
            <Icon name="plus" size="sm" />{{ unit.isSuperset ? "Add a round" : "Add a set" }}
          </button>

          <div v-if="lastOuting" class="lastline">
            <span class="lastline-when">Last<br />{{ formatShortDate(lastOuting.date) }}</span>
            <SetChips :sets="lastOuting.sets" />
          </div>

          <button type="button" class="noterow" :class="{ filled: exercise.comments }" @click="openNote(position.exerciseIndex)">
            <Icon name="pencil" size="sm" />
            <span v-if="exercise.comments"><small>Note on {{ exercise.title }}</small>{{ exercise.comments }}</span>
            <span v-else>Note on {{ exercise.title }}…</span>
          </button>
        </template>
      </template>
    </main>

    <footer v-if="position && store.session" class="dock">
      <Btn variant="primary" size="huge" :loading="logging" @click="done"><Icon name="check" />{{ doneLabel }}</Btn>
    </footer>

    <RestTimer
      v-if="store.rest && restVisible"
      :title="`${store.rest.label || 'Rest'} · Rest`"
      :next="nextLine"
      :go-label="goLabel"
      :note-label="`Note on ${exercise?.title ?? 'this exercise'}`"
      @done="endRest"
      @hide="restVisible = false"
      @note="openNote(position ? position.exerciseIndex : undefined)"
    />

    <Sheet :open="noteFor !== null" :title="`Note · ${store.exercises[noteFor ?? -1]?.title ?? ''}`" @close="noteFor = null">
      <label class="text-field">
        <span class="visually-hidden">Note</span>
        <textarea v-model="noteText" placeholder="How did it feel? Anything to remember next time?" />
      </label>
      <p class="small muted sheet-hint">Saves as you type.</p>
      <Btn variant="primary" class="sheet-btn" @click="noteFor = null">Done</Btn>
    </Sheet>

    <Sheet :open="editing !== null" title="Correct set" @close="editing = null">
      <div v-for="item in editing ?? []" :key="item.exerciseIndex" class="edit-item">
        <p class="edit-name caps">{{ store.exercises[item.exerciseIndex]?.title }} · Set {{ item.setIndex + 1 }}</p>
        <Stepper v-model="item.values.weight" label="weight" unit="lb" :step="5" decimal nullable size="md" />
        <Stepper
          :model-value="item.values.reps"
          label="reps"
          unit="reps"
          size="md"
          @update:model-value="(v) => (item.values.reps = v ?? 0)"
        />
      </div>
      <Btn variant="primary" class="sheet-btn" @click="saveEdit">Save</Btn>
    </Sheet>

    <AddExerciseSheet :open="addOpen" @close="addOpen = false" />
  </div>
</template>

<style scoped>
.rest-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  min-height: 44px;
  padding: 0 12px;
  margin-bottom: 10px;
  background: var(--y);
  border: 2px solid var(--k);
  border-radius: var(--r-lg);
  font-weight: 700;
}
.rest-pill span {
  flex: 1;
  text-align: left;
}
.rest-pill b {
  text-decoration: underline;
  text-underline-offset: 3px;
}

.prog-wrap {
  position: relative;
  display: flex;
  align-items: center;
  margin: 0 calc(-1 * var(--gutter)) 14px;
  padding-right: var(--gutter);
}
.prog {
  flex: 1;
  min-width: 0;
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding: 2px 24px 2px var(--gutter);
  scrollbar-width: none;
  /* fade out under the + button */
  mask-image: linear-gradient(90deg, #000 calc(100% - 28px), transparent);
}
.prog::-webkit-scrollbar {
  display: none;
}
.prog-chip {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 4px;
  min-height: 36px;
  padding: 0 10px;
  border: 1.5px solid var(--rule-strong);
  border-radius: var(--r-sm);
  background: var(--card);
  color: var(--muted);
  font-size: 12.5px;
  font-weight: 600;
  white-space: nowrap;
}
.prog-chip.is-done {
  color: var(--k);
}
.prog-chip.is-current {
  background: var(--k);
  border-color: var(--k);
  color: var(--y);
}
.prog-add {
  flex: 0 0 auto;
  width: 44px;
  min-height: 36px;
  display: grid;
  place-items: center;
  background: var(--k);
  color: var(--y);
  border-radius: var(--r-sm);
}

.trk-name {
  display: block;
  margin: 0;
  font-size: 36px;
  font-weight: 800;
  line-height: 1;
  text-transform: uppercase;
  font-stretch: 80%;
  letter-spacing: 0.01em;
}
.trk-name.is-small {
  font-size: 24px;
}
.trk-sub {
  margin: 4px 0 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--muted);
  text-transform: uppercase;
  font-stretch: 85%;
  letter-spacing: 0.06em;
}
.dials {
  display: grid;
  gap: 8px;
}

.round {
  display: grid;
  gap: 8px;
}
.rcard {
  background: var(--card);
  border: 1.5px solid var(--rule-strong);
  border-radius: var(--r-lg);
  padding: 10px 12px;
}
.rcard.is-current {
  border: 2px solid var(--k);
}
.top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  font-size: 13px;
  color: var(--muted);
}
.rcard.is-current .tag {
  background: var(--y);
  color: var(--k);
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 3px;
}
.donebadge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-weight: 600;
  color: var(--k);
  white-space: nowrap;
}
.nm {
  display: block;
  margin: 2px 0 8px;
  font-size: 18px;
  font-weight: 800;
  text-transform: uppercase;
  font-stretch: 85%;
  letter-spacing: 0.02em;
}

.ledger {
  margin-top: 10px;
  border-top: 2px solid var(--k);
}
.ledger-row {
  display: grid;
  grid-template-columns: 70px 1fr 24px;
  align-items: center;
  width: 100%;
  min-height: 40px;
  padding: 6px 2px;
  border-bottom: 1px solid var(--rule);
  font-size: 14px;
  text-align: left;
}
.ledger-row .n {
  font-size: 12.5px;
  text-transform: uppercase;
  font-stretch: 85%;
  letter-spacing: 0.06em;
  color: var(--muted);
}
.ledger-row:not(.is-done):not(.is-now) .v {
  color: var(--target);
}
.ledger-row.is-now {
  background: var(--y);
  margin: 0 calc(-1 * var(--gutter));
  width: calc(100% + 2 * var(--gutter));
  padding-inline: calc(var(--gutter) + 2px);
  font-weight: 800;
}
.ledger-row.is-now .n {
  color: var(--k);
}
.add-set {
  display: flex;
  align-items: center;
  gap: 4px;
  min-height: 40px;
  font-size: 12.5px;
  font-weight: 700;
  text-transform: uppercase;
  font-stretch: 85%;
  letter-spacing: 0.06em;
  color: var(--muted);
}
.lastline {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
  font-size: 12.5px;
  color: var(--muted);
}
.lastline-when {
  flex: 0 0 auto;
  width: 44px;
  line-height: 1.2;
}
.noterow {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  width: 100%;
  min-height: 44px;
  margin-top: 10px;
  padding: 10px 12px;
  border: 1.5px dashed #b4b6b2;
  border-radius: var(--r);
  color: var(--muted);
  font-size: 14px;
  text-align: left;
}
.noterow.filled {
  border: 1.5px solid var(--k);
  background: var(--card);
  color: var(--k);
}
.noterow small {
  display: block;
  color: var(--muted);
  font-size: 12px;
}
.all-done {
  display: grid;
  gap: 8px;
}
.sheet-hint {
  margin-top: 6px;
}
.sheet-btn {
  width: 100%;
  margin-top: 14px;
}
.edit-item {
  display: grid;
  gap: 6px;
  margin-bottom: 12px;
}
.edit-name {
  font-size: 15px;
}
</style>
