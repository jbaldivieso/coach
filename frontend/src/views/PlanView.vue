<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { api } from "@/api/client";
import type { Session, TitleSuggestion, TitleSuggestions } from "@/types/lifting";
import { todayISO, formatDayDate, formatShortDate, formatClock, parseClock, formatSet } from "@/utils/format";
import { groupUnits, memberLetter, type Unit } from "@/utils/session";
import {
  type DraftExercise,
  blankExercise,
  draftFromExercise,
  copySets,
  hasOnlyBlankSets,
  resizeSets,
  setSetCount,
  copyFirstSetToAll,
  canLinkWithNext,
  linkWithNext,
  unlink,
  removeExercise,
  canMove,
  move,
  setRest,
  normalizeGroups,
  validatePlan,
  toPayload,
} from "@/utils/plan";
import { useExerciseHistory } from "@/composables/useExerciseHistory";
import AppBar from "@/components/ui/AppBar.vue";
import Autocomplete from "@/components/ui/Autocomplete.vue";
import Btn from "@/components/ui/Btn.vue";
import Icon from "@/components/ui/Icon.vue";
import SetChips from "@/components/ui/SetChips.vue";
import Sheet from "@/components/ui/Sheet.vue";
import Stepper from "@/components/ui/Stepper.vue";
import SetEditor from "@/components/plan/SetEditor.vue";
import CountControl from "@/components/plan/CountControl.vue";
import HistoryBlock from "@/components/plan/HistoryBlock.vue";
import CollapsedExercise from "@/components/plan/CollapsedExercise.vue";

const route = useRoute();
const router = useRouter();

// "new": a fresh plan (optionally started from a past session)
// "planned": editing a plan saved for later
// "done": editing a finished session
const mode = computed<"new" | "planned" | "done">(() => {
  if (route.name === "session-edit") return "done";
  if (route.name === "plan-edit") return "planned";
  return "new";
});
const sessionId = computed(() => (mode.value === "new" ? null : Number(route.params.id)));
const fromId = computed(() => (mode.value === "new" && route.query.from ? Number(route.query.from) : null));

const title = ref("");
const date = ref(todayISO());
const comments = ref("");
const exercises = ref<DraftExercise[]>([]);
const fromLabel = ref<string | null>(null);

const loading = ref(true);
const saving = ref<"start" | "later" | "save" | "delete" | null>(null);
const error = ref<string | null>(null);
const errors = ref<Record<string, string>>({});
const dirty = ref(false);

const expandedKey = ref<number | null>(null);
const selected = ref<{ key: number; index: number } | null>(null);
const menuFor = ref<DraftExercise | null>(null);
const restFor = ref<DraftExercise | null>(null);

const titleInput = ref<InstanceType<typeof Autocomplete> | null>(null);
const nameInputs = new Map<number, InstanceType<typeof Autocomplete>>();

const history = useExerciseHistory({ excludeSession: () => sessionId.value });
const units = computed(() => groupUnits(exercises.value));

const barTitle = computed(() => `${mode.value === "done" ? "Edit" : "Plan"} · ${formatDayDate(date.value || todayISO())}`);

// ---------- Loading ----------

async function fetchSession(id: number): Promise<Session | null> {
  const response = await api.get<Session>(`/api/lifting/sessions/${id}/`);
  if (!response.data) error.value = response.error || "Couldn't load that session";
  return response.data;
}

async function load() {
  loading.value = true;
  error.value = null;
  if (sessionId.value) {
    const session = await fetchSession(sessionId.value);
    if (!session) return finishLoading();
    // Send each status to the screen that owns it
    if (session.status === "active") return router.replace({ name: "track", params: { id: session.id } });
    if (session.status === "done" && mode.value === "planned")
      return router.replace({ name: "session-edit", params: { id: session.id } });
    if (session.status === "planned" && mode.value === "done")
      return router.replace({ name: "plan-edit", params: { id: session.id } });
    title.value = session.title;
    date.value = session.date;
    comments.value = session.comments;
    exercises.value = session.exercises.map((e) => draftFromExercise(e, true));
  } else if (fromId.value) {
    const source = await fetchSession(fromId.value);
    if (!source) return finishLoading();
    title.value = source.title;
    fromLabel.value = `from ${formatShortDate(source.date)}`;
    exercises.value = source.exercises.map((e) => draftFromExercise(e, false));
  } else {
    exercises.value = [blankExercise()];
  }
  normalizeGroups(exercises.value);
  expandedKey.value = exercises.value[0]?.key ?? null;
  finishLoading();
  if (mode.value === "new" && !fromId.value) {
    await nextTick();
    titleInput.value?.focus();
  }
}

async function finishLoading() {
  loading.value = false;
  await nextTick();
  dirty.value = false;
}

watch([title, date, comments, exercises], () => (dirty.value = true), { deep: true });

watch(
  () => exercises.value.map((e) => e.historyTitle),
  (titles) => titles.forEach((t) => history.load(t)),
  { immediate: true },
);

// ---------- Autocomplete ----------

async function fetchSessionTitles(q: string): Promise<TitleSuggestion[]> {
  if (!q.trim()) return [];
  const response = await api.get<TitleSuggestions>(`/api/lifting/sessions/autocomplete/?q=${encodeURIComponent(q)}`);
  return response.data?.suggestions ?? [];
}

async function fetchExerciseTitles(q: string): Promise<TitleSuggestion[]> {
  const response = await api.get<TitleSuggestions>(`/api/lifting/exercises/autocomplete/?q=${encodeURIComponent(q)}`);
  return response.data?.suggestions ?? [];
}

/** A name is settled: show its history, and if the exercise is still blank, fill in last time's sets. */
async function commitName(exercise: DraftExercise, name: string) {
  exercise.title = name;
  exercise.historyTitle = name;
  if (!name || !hasOnlyBlankSets(exercise)) return;
  const entry = await history.load(name);
  const last = entry?.items[0];
  if (!last || !hasOnlyBlankSets(exercise)) return;
  const groupSize = unitOf(exercise).items.length;
  if (groupSize > 1) {
    const rounds = Math.max(...unitOf(exercise).items.filter((e) => e !== exercise).map((e) => e.sets.length));
    exercise.sets = copySets(last.sets);
    resizeSets(exercise, rounds);
  } else {
    exercise.sets = copySets(last.sets);
    exercise.rest_seconds = last.rest_seconds;
  }
}

function setNameRef(key: number, el: unknown) {
  if (el) nameInputs.set(key, el as InstanceType<typeof Autocomplete>);
  else nameInputs.delete(key);
}

// ---------- Structure ----------

function indexOf(exercise: DraftExercise): number {
  return exercises.value.indexOf(exercise);
}

function unitOf(exercise: DraftExercise): Unit<DraftExercise> {
  return units.value.find((u) => u.items.includes(exercise))!;
}

function isExpanded(unit: Unit<DraftExercise>): boolean {
  return unit.items.some((e) => e.key === expandedKey.value);
}

function expand(exercise: DraftExercise) {
  expandedKey.value = exercise.key;
  selected.value = null;
}

function select(exercise: DraftExercise, index: number) {
  const same = selected.value?.key === exercise.key && selected.value.index === index;
  selected.value = same ? null : { key: exercise.key, index };
}

function selectedSetIn(unit: Unit<DraftExercise>) {
  const sel = selected.value;
  if (!sel) return null;
  const memberIndex = unit.items.findIndex((e) => e.key === sel.key);
  const exercise = unit.items[memberIndex];
  const set = exercise?.sets[sel.index];
  return exercise && set ? { exercise, set, memberIndex, index: sel.index } : null;
}

function changeCount(exercise: DraftExercise, count: number) {
  setSetCount(exercises.value, indexOf(exercise), count);
  if (selected.value && selected.value.index >= count) selected.value = null;
}

async function addExercise() {
  const exercise = blankExercise();
  exercises.value.push(exercise);
  expand(exercise);
  await nextTick();
  nameInputs.get(exercise.key)?.focus();
}

const menuIndex = computed(() => (menuFor.value ? indexOf(menuFor.value) : -1));
const nextTitle = computed(() => {
  if (menuIndex.value < 0) return "";
  return exercises.value[menuIndex.value + 1]?.title || "next";
});

function menuAction(action: "up" | "down" | "link" | "unlink" | "remove") {
  const exercise = menuFor.value;
  const index = menuIndex.value;
  menuFor.value = null;
  if (!exercise || index < 0) return;
  const list = exercises.value;
  if (action === "up") move(list, index, -1);
  else if (action === "down") move(list, index, 1);
  else if (action === "link") linkWithNext(list, index);
  else if (action === "unlink") unlink(list, index);
  else if (action === "remove") {
    removeExercise(list, index);
    if (expandedKey.value === exercise.key) expandedKey.value = list[Math.min(index, list.length - 1)]?.key ?? null;
    return;
  }
  expandedKey.value = exercise.key;
}

function updateRest(seconds: number | null) {
  if (restFor.value && seconds !== null) setRest(exercises.value, indexOf(restFor.value), seconds);
}

// ---------- Saving ----------

async function scrollToFirstError() {
  const keys = Object.keys(errors.value);
  const firstExercise = exercises.value.find((e) => keys.some((k) => k.startsWith(`exercise.${e.key}.`)));
  if (firstExercise && !keys.includes("title")) expand(firstExercise);
  await nextTick();
  document.querySelector(".is-error")?.scrollIntoView({ behavior: "smooth", block: "center" });
}

async function save(action: "start" | "later" | "save") {
  error.value = null;
  errors.value = validatePlan(
    { title: title.value, date: date.value, exercises: exercises.value },
    { allowFuture: mode.value !== "done", today: todayISO() },
  );
  if (Object.keys(errors.value).length) return scrollToFirstError();

  saving.value = action;
  await api.fetchCsrfToken();
  const today = todayISO();
  const body = {
    title: title.value.trim(),
    // Starting means it's happening today, whatever date was planned
    date: action === "start" ? today : date.value,
    comments: comments.value.trim(),
    exercises: toPayload(exercises.value, mode.value === "done"),
  };

  let saved: Session | null = null;
  if (mode.value === "new") {
    const status = action === "start" ? "active" : "planned";
    const response = await api.post<Session>("/api/lifting/sessions/with-exercises/", { ...body, status });
    saved = response.data;
    if (!saved) error.value = response.error || "Couldn't save";
  } else {
    const response = await api.put<Session>(`/api/lifting/sessions/${sessionId.value}/with-exercises/`, body);
    saved = response.data;
    if (!saved) error.value = response.error || "Couldn't save";
    if (saved && action === "start") {
      const started = await api.post<Session>(`/api/lifting/sessions/${saved.id}/start/`, { date: today });
      if (!started.data) {
        error.value = started.error || "Saved, but couldn't start it";
        saved = null;
      }
    }
  }
  saving.value = null;
  if (!saved) return;

  dirty.value = false;
  if (action === "start") router.replace({ name: "track", params: { id: saved.id } });
  else if (action === "save") router.replace({ name: "session-detail", params: { id: saved.id } });
  else router.push({ name: "home" });
}

async function deleteSession() {
  const what = mode.value === "planned" ? "this plan" : "this session and every set in it";
  if (!sessionId.value || !window.confirm(`Delete ${what}?`)) return;
  saving.value = "delete";
  await api.fetchCsrfToken();
  const response = await api.delete(`/api/lifting/sessions/${sessionId.value}/`);
  saving.value = null;
  if (response.error) {
    error.value = response.error;
    return;
  }
  dirty.value = false;
  router.replace({ name: "home" });
}

function close() {
  if (dirty.value && !window.confirm("Discard your changes?")) return;
  if (window.history.state?.back) router.back();
  else router.push(mode.value === "done" && sessionId.value ? { name: "session-detail", params: { id: sessionId.value } } : "/");
}

onMounted(load);
</script>

<template>
  <div class="screen">
    <AppBar :title="barTitle" small :close="close" />

    <main class="screen-body">
      <p v-if="loading" class="empty">Loading…</p>
      <template v-else>
        <div v-if="error" class="notice is-error" role="alert"><b>Not saved</b>{{ error }}</div>

        <div class="text-field title-field" :class="{ 'is-error': errors.title }">
          <Autocomplete
            ref="titleInput"
            v-model="title"
            :fetch="fetchSessionTitles"
            label="Session title"
            placeholder="Session title"
            input-class="title-input"
            :invalid="!!errors.title"
          />
          <span v-if="fromLabel" class="from small muted">{{ fromLabel }}</span>
        </div>
        <p v-if="errors.title" class="field-error">{{ errors.title }}</p>

        <label class="text-field date-field" :class="{ 'is-error': errors.date }">
          <span class="date-label">Date</span>
          <input v-model="date" type="date" :max="mode === 'done' ? todayISO() : undefined" required />
        </label>
        <p v-if="errors.date" class="field-error">{{ errors.date }}</p>

        <template v-for="unit in units" :key="unit.items[0]!.key">
          <!-- Single exercise -->
          <template v-if="!unit.isSuperset">
            <section v-if="isExpanded(unit)" class="ex">
              <div class="ex-h">
                <Autocomplete
                  :ref="(el) => setNameRef(unit.items[0]!.key, el)"
                  v-model="unit.items[0]!.title"
                  :fetch="fetchExerciseTitles"
                  label="Exercise name"
                  placeholder="Exercise name"
                  input-class="name-input"
                  suggest-on-focus
                  :invalid="!!errors[`exercise.${unit.items[0]!.key}.title`]"
                  @pick="(s) => commitName(unit.items[0]!, s.title)"
                  @commit="(v) => commitName(unit.items[0]!, v)"
                />
                <button type="button" class="rest" :aria-label="`Rest ${formatClock(unit.items[0]!.rest_seconds)}. Change.`" @click="restFor = unit.items[0]!">
                  <Icon name="clock" size="sm" />{{ formatClock(unit.items[0]!.rest_seconds) }}
                </button>
                <button type="button" class="ex-menu" aria-label="Exercise options" @click="menuFor = unit.items[0]!">
                  <Icon name="more" />
                </button>
              </div>
              <p v-if="errors[`exercise.${unit.items[0]!.key}.title`]" class="field-error is-error">
                {{ errors[`exercise.${unit.items[0]!.key}.title`] }}
              </p>

              <div class="plan-head">
                <span class="sub-label">Today · tap a set</span>
                <CountControl :count="unit.items[0]!.sets.length" noun="set" @change="(n) => changeCount(unit.items[0]!, n)" />
              </div>
              <SetChips
                :sets="unit.items[0]!.sets"
                selectable
                :selected="selected?.key === unit.items[0]!.key ? selected.index : null"
                @select="(i) => select(unit.items[0]!, i)"
              />
              <p v-if="errors[`exercise.${unit.items[0]!.key}.sets`]" class="field-error is-error">
                {{ errors[`exercise.${unit.items[0]!.key}.sets`] }}
              </p>
              <SetEditor
                v-if="selectedSetIn(unit)"
                :key="`${selected!.key}-${selected!.index}`"
                :set="selectedSetIn(unit)!.set"
                :index="selectedSetIn(unit)!.index"
                @update:weight="(v) => (selectedSetIn(unit)!.set.weight = v)"
                @update:reps="(v) => (selectedSetIn(unit)!.set.reps = v)"
                @copy-to-all="copyFirstSetToAll(unit.items[0]!)"
              />

              <HistoryBlock :title="unit.items[0]!.historyTitle" :entry="history.get(unit.items[0]!.historyTitle)" />

              <label class="text-field note-field">
                <Icon name="pencil" size="sm" />
                <span class="visually-hidden">Note</span>
                <input v-model="unit.items[0]!.comments" :placeholder="`Note on ${unit.items[0]!.title || 'this exercise'}`" />
              </label>
            </section>
            <CollapsedExercise
              v-else
              :exercise="unit.items[0]!"
              :entry="history.get(unit.items[0]!.historyTitle)"
              :error="Object.keys(errors).some((k) => k.startsWith(`exercise.${unit.items[0]!.key}.`))"
              @expand="expand(unit.items[0]!)"
            />
          </template>

          <!-- Superset -->
          <section v-else class="ss" :class="{ 'is-collapsed': !isExpanded(unit) }">
            <header class="ss-h">
              <Icon name="link" size="sm" />
              <span class="ss-title">Superset · {{ unit.items[0]!.sets.length }} rounds</span>
              <button type="button" class="ss-rest" @click="restFor = unit.items[0]!">
                <Icon name="clock" size="sm" />{{ formatClock(unit.items[0]!.rest_seconds) }} after each round
              </button>
            </header>

            <template v-if="isExpanded(unit)">
              <div v-for="(e, m) in unit.items" :key="e.key" class="ss-member">
                <div class="ex-h">
                  <span class="letter caps">{{ memberLetter(m) }} ·</span>
                  <Autocomplete
                    :ref="(el) => setNameRef(e.key, el)"
                    v-model="e.title"
                    :fetch="fetchExerciseTitles"
                    label="Exercise name"
                    placeholder="Exercise name"
                    input-class="name-input"
                    suggest-on-focus
                    :invalid="!!errors[`exercise.${e.key}.title`]"
                    @pick="(s) => commitName(e, s.title)"
                    @commit="(v) => commitName(e, v)"
                  />
                  <button type="button" class="ex-menu" :aria-label="`${e.title || 'Exercise'} options`" @click="menuFor = e">
                    <Icon name="more" />
                  </button>
                </div>
                <p v-if="errors[`exercise.${e.key}.title`]" class="field-error is-error">{{ errors[`exercise.${e.key}.title`] }}</p>
                <HistoryBlock :title="e.historyTitle" :entry="history.get(e.historyTitle)" short />
                <label class="text-field note-field">
                  <Icon name="pencil" size="sm" />
                  <span class="visually-hidden">Note</span>
                  <input v-model="e.comments" :placeholder="`Note on ${e.title || 'this exercise'}`" />
                </label>
              </div>

              <div class="plan-head rounds-head">
                <span class="sub-label">Rounds · tap a set</span>
                <CountControl :count="unit.items[0]!.sets.length" noun="round" @change="(n) => changeCount(unit.items[0]!, n)" />
              </div>
              <div class="rounds" :style="{ '--members': unit.items.length }">
                <span />
                <span v-for="(e, m) in unit.items" :key="e.key" class="rounds-name">{{ memberLetter(m) }} · {{ e.title || "?" }}</span>
                <template v-for="(_, r) in unit.items[0]!.sets" :key="r">
                  <span class="rounds-n">{{ r + 1 }}</span>
                  <button
                    v-for="e in unit.items"
                    :key="e.key"
                    type="button"
                    class="round-cell"
                    :class="{ 'is-selected': selected?.key === e.key && selected.index === r }"
                    :aria-pressed="selected?.key === e.key && selected.index === r"
                    @click="select(e, r)"
                  >
                    {{ e.sets[r] ? formatSet(e.sets[r]!) : "–" }}
                  </button>
                </template>
              </div>
              <p v-for="e in unit.items.filter((x) => errors[`exercise.${x.key}.sets`])" :key="e.key" class="field-error is-error">
                {{ e.title || "An exercise" }}: {{ errors[`exercise.${e.key}.sets`] }}
              </p>
              <SetEditor
                v-if="selectedSetIn(unit)"
                :key="`${selected!.key}-${selected!.index}`"
                :set="selectedSetIn(unit)!.set"
                :index="selectedSetIn(unit)!.index"
                :label="`${memberLetter(selectedSetIn(unit)!.memberIndex)} · ${selectedSetIn(unit)!.exercise.title || 'Set'} · Round ${selectedSetIn(unit)!.index + 1}`"
                @update:weight="(v) => (selectedSetIn(unit)!.set.weight = v)"
                @update:reps="(v) => (selectedSetIn(unit)!.set.reps = v)"
                @copy-to-all="copyFirstSetToAll(selectedSetIn(unit)!.exercise)"
              />
            </template>
            <template v-else>
              <CollapsedExercise
                v-for="(e, m) in unit.items"
                :key="e.key"
                :exercise="e"
                :entry="history.get(e.historyTitle)"
                :prefix="`${memberLetter(m)} · `"
                :error="Object.keys(errors).some((k) => k.startsWith(`exercise.${e.key}.`))"
                @expand="expand(e)"
              />
            </template>
          </section>
        </template>

        <p v-if="errors.exercises" class="field-error is-error">{{ errors.exercises }}</p>
        <Btn class="add-ex" @click="addExercise"><Icon name="plus" />Add exercise</Btn>

        <template v-if="mode === 'done'">
          <h2 class="eyebrow">Session comments</h2>
          <label class="text-field">
            <span class="visually-hidden">Session comments</span>
            <textarea v-model="comments" placeholder="How did it go?" />
          </label>
        </template>

        <button v-if="mode !== 'new'" type="button" class="delete" :disabled="saving !== null" @click="deleteSession">
          {{ mode === "planned" ? "Delete this plan" : "Delete this session" }}
        </button>
      </template>
    </main>

    <footer v-if="!loading" class="dock">
      <template v-if="mode === 'done'">
        <Btn variant="primary" size="huge" :loading="saving === 'save'" :disabled="saving !== null" @click="save('save')">Save</Btn>
      </template>
      <template v-else>
        <Btn variant="primary" size="huge" :loading="saving === 'start'" :disabled="saving !== null" @click="save('start')">
          Start session
        </Btn>
        <Btn :loading="saving === 'later'" :disabled="saving !== null" @click="save('later')">Save for later</Btn>
      </template>
    </footer>

    <Sheet :open="menuFor !== null" :title="menuFor?.title || 'Exercise'" @close="menuFor = null">
      <div v-if="menuFor" class="actions">
        <button type="button" class="action" :disabled="!canMove(exercises, menuIndex, -1)" @click="menuAction('up')">
          <Icon name="up" />Move up
        </button>
        <button type="button" class="action" :disabled="!canMove(exercises, menuIndex, 1)" @click="menuAction('down')">
          <Icon name="down" />Move down
        </button>
        <button v-if="canLinkWithNext(exercises, menuIndex)" type="button" class="action" @click="menuAction('link')">
          <Icon name="link" />Superset with {{ nextTitle }}
        </button>
        <button v-if="menuFor.superset_group !== null" type="button" class="action" @click="menuAction('unlink')">
          <Icon name="x" />Unlink superset
        </button>
        <button type="button" class="action is-danger" @click="menuAction('remove')"><Icon name="minus" />Remove</button>
      </div>
    </Sheet>

    <Sheet :open="restFor !== null" title="Rest" @close="restFor = null">
      <template v-if="restFor">
        <p class="muted small sheet-note">
          {{ restFor.superset_group !== null ? "After each round of the superset." : `After each set of ${restFor.title || "this exercise"}.` }}
        </p>
        <Stepper
          :model-value="restFor.rest_seconds"
          label="rest"
          unit="min:sec"
          :step="15"
          :max="3600"
          :format="(v) => formatClock(v ?? 0)"
          :parse="parseClock"
        @update:model-value="updateRest"
        />
        <Btn variant="primary" class="sheet-done" @click="restFor = null">Done</Btn>
      </template>
    </Sheet>
  </div>
</template>

<style scoped>
.title-field {
  margin-bottom: 4px;
}
.title-field :deep(.title-input) {
  border: 0;
  background: transparent;
  outline: none;
  padding: 10px 0;
  font-size: 18px;
  font-weight: 800;
  text-transform: uppercase;
  font-stretch: 85%;
  letter-spacing: 0.03em;
  color: var(--k);
}
.title-field :deep(.title-input::placeholder) {
  color: var(--muted);
  font-weight: 600;
}
.from {
  white-space: nowrap;
}
.date-field {
  margin: 8px 0 12px;
}
.date-label {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  font-stretch: 85%;
}
.date-field input {
  text-align: right;
}

.ex {
  background: var(--card);
  border-radius: var(--r-lg);
  padding: 8px 12px 12px;
  margin-bottom: 10px;
}
.ex-h {
  display: flex;
  align-items: center;
  gap: 4px;
}
.ex-h :deep(.name-input) {
  border: 0;
  border-bottom: 1.5px dashed transparent;
  background: transparent;
  outline: none;
  padding: 8px 0 6px;
  font-size: 18px;
  font-weight: 800;
  text-transform: uppercase;
  font-stretch: 85%;
  letter-spacing: 0.02em;
  color: var(--k);
}
.ex-h :deep(.name-input:focus) {
  border-bottom-color: var(--k);
}
.ex-h :deep(.name-input[aria-invalid="true"]) {
  border-bottom-color: var(--alert);
}
.rest {
  display: flex;
  align-items: center;
  gap: 3px;
  min-height: 44px;
  padding: 0 6px;
  font-size: 13px;
  color: var(--muted);
  white-space: nowrap;
}
.ex-menu {
  width: 40px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: var(--r);
  flex: 0 0 auto;
}
.plan-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 8px 0 6px;
}
.sub-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-stretch: 85%;
  color: var(--muted);
}
.note-field {
  margin-top: 8px;
  min-height: 40px;
  border-style: dashed;
}
.note-field input {
  font-size: 15px;
  padding: 8px 0;
}

/* Superset: the only striped element in the app */
.ss {
  background: var(--card);
  border: 2px solid var(--k);
  border-radius: 10px;
  padding: 0 10px 10px;
  margin-bottom: 10px;
  overflow: hidden;
}
.ss.is-collapsed {
  padding-bottom: 2px;
}
.ss-h {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--k);
  color: var(--y);
  margin: 0 -10px 8px;
  padding: 12px 10px 8px;
  font-size: 12.5px;
  font-weight: 800;
  text-transform: uppercase;
  font-stretch: 85%;
  letter-spacing: 0.04em;
}
.ss-h::before {
  content: "";
  position: absolute;
  inset: 0 0 auto 0;
  height: 5px;
  background: var(--hazard);
}
.ss-title {
  flex: 1;
  white-space: nowrap;
}
.ss-rest {
  display: flex;
  align-items: center;
  gap: 3px;
  min-height: 32px;
  color: var(--on-k);
  font-size: 11.5px;
  font-weight: 500;
  text-transform: none;
  letter-spacing: 0;
  font-stretch: 100%;
  white-space: nowrap;
}
.ss.is-collapsed :deep(.collapsed) {
  padding-inline: 2px;
  border-bottom: 1px solid var(--rule);
  border-radius: 0;
  margin: 0;
}
.ss.is-collapsed :deep(.collapsed:last-child) {
  border-bottom: 0;
}
.ss-member {
  padding: 4px 0 10px;
  border-bottom: 1px solid var(--rule);
}
.letter {
  font-size: 18px;
  white-space: nowrap;
}
.rounds {
  display: grid;
  grid-template-columns: 22px repeat(var(--members), 1fr);
  gap: 6px;
  align-items: center;
}
.rounds-name {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.rounds-n {
  color: var(--muted);
  font-size: 12px;
  text-align: center;
}
.round-cell {
  min-height: 44px;
  border: 1px solid var(--rule-strong);
  border-radius: var(--r);
  font-weight: 600;
  font-size: 14px;
  background: var(--card);
}
.round-cell.is-selected {
  background: var(--y);
  border: 2px solid var(--k);
}

.add-ex {
  width: 100%;
  margin-top: 4px;
}
.delete {
  display: block;
  margin: 28px auto 0;
  min-height: 44px;
  color: var(--alert);
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.actions {
  display: grid;
}
.action {
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 52px;
  border-bottom: 1px solid var(--rule);
  font-size: 16px;
  font-weight: 600;
  text-align: left;
}
.action:last-child {
  border-bottom: 0;
}
.action:disabled {
  opacity: 0.35;
}
.action.is-danger {
  color: var(--alert);
}
.sheet-note {
  margin-bottom: 10px;
}
.sheet-done {
  width: 100%;
  margin-top: 14px;
}
</style>
