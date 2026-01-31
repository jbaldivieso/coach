<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { api } from "@/api/client";
import type {
  ExerciseFormData,
  SessionFormData,
  Session,
  ExerciseEditState,
  SetFormData,
  Set,
} from "@/types/lifting";
import { SESSION_TYPES } from "@/types/lifting";
import RestTimer from "@/components/RestTimer.vue";
import IconPlus from "@/components/svg/IconPlus.vue";

const router = useRouter();
const route = useRoute();

// Mode detection
const isEditMode = computed(() => route.name === "edit-session");
const isCopyMode = computed(() => route.name === "copy-session");
const sessionId = computed(() =>
  isEditMode.value ? Number(route.params.id) : null,
);
const sourceSessionId = computed(() =>
  isCopyMode.value ? Number(route.params.id) : null,
);
const pageTitle = computed(() => {
  if (isEditMode.value) return "Edit Session";
  if (isCopyMode.value) return "Copy Session";
  return "New Session";
});

// Form state
const sessionForm = ref<SessionFormData>({
  title: "",
  date: getTodayDateString(),
  session_type: "",
  comments: "",
});

const exercises = ref<ExerciseFormData[]>([createEmptyExercise()]);

// UI state
const loading = ref(false);
const error = ref<string | null>(null);
const validationErrors = ref<Record<string, string>>({});
const titleInputRef = ref<HTMLInputElement | null>(null);
const loadingSession = ref(false);
const exerciseStates = ref<ExerciseEditState[]>([]);
const deletedExerciseIds = ref<number[]>([]);

// Timer state
const timerActive = ref(false);
const timerExerciseIndex = ref<number | null>(null);

const timerExercise = computed(() => {
  if (timerExerciseIndex.value === null) return null;
  return exercises.value[timerExerciseIndex.value] || null;
});

function canShowTimer(exercise: ExerciseFormData): boolean {
  return (
    exercise.title.trim() !== "" &&
    exercise.rest_seconds !== "" &&
    !isNaN(Number(exercise.rest_seconds)) &&
    Number(exercise.rest_seconds) > 0 &&
    exercise.sets.length > 0 &&
    exercise.sets.some((s) => String(s.reps).trim() !== "")
  );
}

function startTimer(index: number) {
  timerExerciseIndex.value = index;
  timerActive.value = true;
}

function closeTimer() {
  timerActive.value = false;
  timerExerciseIndex.value = null;
}

function getTodayDateString(): string {
  return new Date().toISOString().split("T")[0] as string;
}

function createEmptySet(): SetFormData {
  return { weight: "", reps: "" };
}

function createEmptyExercise(): ExerciseFormData {
  return {
    title: "",
    sets: [createEmptySet()],
    rest_seconds: "",
    comments: "",
  };
}

function addSet(exerciseIndex: number) {
  exercises.value[exerciseIndex]?.sets.push(createEmptySet());
}

function removeSet(exerciseIndex: number, setIndex: number) {
  const exercise = exercises.value[exerciseIndex];
  if (exercise && exercise.sets.length > 1) {
    exercise.sets.splice(setIndex, 1);
  }
}

function addExercise() {
  const newExercise = createEmptyExercise();
  exercises.value.push(newExercise);
  if (isEditMode.value) {
    exerciseStates.value.push({ data: newExercise });
  }
}

function removeExercise(index: number) {
  if (exercises.value.length > 1) {
    if (isEditMode.value && exerciseStates.value[index]?.id) {
      deletedExerciseIds.value.push(exerciseStates.value[index].id!);
    }
    exercises.value.splice(index, 1);
    if (isEditMode.value) {
      exerciseStates.value.splice(index, 1);
    }
  }
}

async function fetchSession(id: number) {
  loadingSession.value = true;
  error.value = null;

  try {
    const response = await api.get<Session>(`/api/lifting/sessions/${id}/`);

    if (response.data) {
      // Populate session form
      sessionForm.value = {
        title: response.data.title,
        date: response.data.date,
        session_type: response.data.session_type,
        comments: response.data.comments,
      };

      // Populate exercises and initialize exercise states
      const exerciseFormDataList: ExerciseFormData[] =
        response.data.exercises.map((ex) => ({
          title: ex.title,
          sets: ex.sets.map((s: Set) => ({
            weight: s.weight?.toString() || "",
            reps: s.reps.toString(),
          })),
          rest_seconds: ex.rest_seconds.toString(),
          comments: ex.comments,
        }));
      exercises.value = exerciseFormDataList;

      // Initialize exercise states for tracking
      exerciseStates.value = response.data.exercises.map((ex, index) => ({
        id: ex.id,
        data: exerciseFormDataList[index]!,
      }));

      // Ensure at least one exercise
      if (exercises.value.length === 0) {
        const newExercise = createEmptyExercise();
        exercises.value.push(newExercise);
        exerciseStates.value.push({ data: newExercise });
      }
    } else {
      error.value = response.error || "Failed to load session";
      router.push({ name: "home" });
    }
  } catch {
    error.value = "Network error. Please try again.";
    router.push({ name: "home" });
  } finally {
    loadingSession.value = false;
  }
}

async function fetchSessionForCopy(id: number) {
  loadingSession.value = true;
  error.value = null;

  try {
    const response = await api.get<Session>(`/api/lifting/sessions/${id}/`);

    if (response.data) {
      // Populate session form with copied values (but today's date)
      sessionForm.value = {
        title: response.data.title,
        date: getTodayDateString(),
        session_type: response.data.session_type,
        comments: "",
      };

      // Transform exercises for copy mode - keep weights, clear reps, show previous in comments
      const formatPreviousSets = (sets: Set[]): string => {
        return sets
          .map((s) => {
            const w = s.weight !== null ? `${s.weight} lbs` : "bodyweight";
            return `${w} x ${s.reps}`;
          })
          .join(", ");
      };

      exercises.value = response.data.exercises.map((ex) => ({
        title: ex.title,
        sets: ex.sets.map((s: Set) => ({
          weight: s.weight?.toString() || "",
          reps: "", // Clear reps for new entry
        })),
        rest_seconds: ex.rest_seconds.toString(),
        comments: `Previously: ${formatPreviousSets(ex.sets)}`,
      }));

      // Ensure at least one exercise
      if (exercises.value.length === 0) {
        exercises.value.push(createEmptyExercise());
      }
    } else {
      error.value = response.error || "Failed to load session";
      router.push({ name: "home" });
    }
  } catch {
    error.value = "Network error. Please try again.";
    router.push({ name: "home" });
  } finally {
    loadingSession.value = false;
  }
}

function validateForm(): boolean {
  validationErrors.value = {};
  let isValid = true;

  // Session title
  if (!sessionForm.value.title.trim()) {
    validationErrors.value["session.title"] = "Title is required";
    isValid = false;
  }

  // Date validation
  if (!sessionForm.value.date) {
    validationErrors.value["session.date"] = "Date is required";
    isValid = false;
  } else {
    const selectedDate = new Date(sessionForm.value.date);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    selectedDate.setHours(0, 0, 0, 0);
    if (selectedDate > today) {
      validationErrors.value["session.date"] = "Date cannot be in the future";
      isValid = false;
    }
  }

  // Session type
  if (!sessionForm.value.session_type) {
    validationErrors.value["session.type"] = "Please select a session type";
    isValid = false;
  }

  // Exercise validation
  exercises.value.forEach((exercise, exIndex) => {
    if (!exercise.title.trim()) {
      validationErrors.value[`exercise.${exIndex}.title`] =
        "Exercise title is required";
      isValid = false;
    }

    const restValue = String(exercise.rest_seconds).trim();
    if (!restValue) {
      validationErrors.value[`exercise.${exIndex}.rest`] =
        "Rest time is required";
      isValid = false;
    } else if (isNaN(Number(restValue)) || Number(restValue) < 0) {
      validationErrors.value[`exercise.${exIndex}.rest`] =
        "Rest must be a positive number";
      isValid = false;
    }

    // Validate sets
    if (exercise.sets.length === 0) {
      validationErrors.value[`exercise.${exIndex}.sets`] =
        "At least one set is required";
      isValid = false;
    } else {
      exercise.sets.forEach((set, setIndex) => {
        const repsVal = String(set.reps).trim();
        if (!repsVal) {
          validationErrors.value[`exercise.${exIndex}.set.${setIndex}.reps`] =
            "Reps required";
          isValid = false;
        } else if (isNaN(parseInt(repsVal, 10)) || parseInt(repsVal, 10) < 0) {
          validationErrors.value[`exercise.${exIndex}.set.${setIndex}.reps`] =
            "Invalid reps";
          isValid = false;
        }

        const weightVal = String(set.weight).trim();
        if (weightVal !== "" && isNaN(parseInt(weightVal, 10))) {
          validationErrors.value[`exercise.${exIndex}.set.${setIndex}.weight`] =
            "Invalid weight";
          isValid = false;
        }
      });
    }
  });

  return isValid;
}

function buildPayload() {
  return {
    title: sessionForm.value.title.trim(),
    date: sessionForm.value.date,
    session_type: sessionForm.value.session_type,
    comments: sessionForm.value.comments.trim(),
    exercises: exercises.value.map((ex) => ({
      title: ex.title.trim(),
      sets: ex.sets
        .filter((s) => String(s.reps).trim() !== "")
        .map((s) => ({
          weight: String(s.weight).trim() ? parseInt(String(s.weight), 10) : null,
          reps: parseInt(String(s.reps), 10),
        })),
      rest_seconds: parseInt(String(ex.rest_seconds), 10),
      comments: ex.comments.trim(),
    })),
  };
}

async function handleUpdate() {
  if (!sessionId.value) return;

  error.value = null;
  if (!validateForm()) return;

  loading.value = true;

  try {
    await api.fetchCsrfToken();

    // 1. Update session metadata
    const sessionPayload = {
      title: sessionForm.value.title.trim(),
      date: sessionForm.value.date,
      session_type: sessionForm.value.session_type,
      comments: sessionForm.value.comments.trim(),
    };

    const sessionResponse = await api.put<Session>(
      `/api/lifting/sessions/${sessionId.value}/`,
      sessionPayload,
    );

    if (!sessionResponse.data) {
      error.value = sessionResponse.error || "Failed to update session";
      loading.value = false;
      return;
    }

    // 2. Delete removed exercises
    for (const exerciseId of deletedExerciseIds.value) {
      await api.delete(`/api/lifting/exercises/${exerciseId}/`);
    }

    // 3. Update/create exercises
    const payload = buildPayload();
    for (let i = 0; i < exercises.value.length; i++) {
      const exerciseData = payload.exercises[i];
      const exerciseState = exerciseStates.value[i];

      if (exerciseState && exerciseState.id) {
        // Update existing exercise
        await api.put(
          `/api/lifting/exercises/${exerciseState.id}/`,
          exerciseData,
        );
      } else if (sessionId.value) {
        // Create new exercise
        await api.post(
          `/api/lifting/sessions/${sessionId.value}/exercises/`,
          exerciseData,
        );
      }
    }

    // Success - redirect to session detail
    router.push({ name: "session-detail", params: { id: sessionId.value } });
  } catch {
    error.value = "Network error. Please try again.";
  } finally {
    loading.value = false;
  }
}

async function handleSubmit() {
  if (isEditMode.value) {
    await handleUpdate();
    return;
  }

  error.value = null;

  if (!validateForm()) {
    return;
  }

  loading.value = true;

  try {
    await api.fetchCsrfToken();

    const payload = buildPayload();
    const response = await api.post<Session>(
      "/api/lifting/sessions/with-exercises/",
      payload,
    );

    if (response.data) {
      router.push({ name: "session-detail", params: { id: response.data.id } });
    } else {
      error.value = response.error || "Failed to create session";
    }
  } catch {
    error.value = "Network error. Please try again.";
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  if (isEditMode.value && sessionId.value) {
    fetchSession(sessionId.value);
  } else if (isCopyMode.value && sourceSessionId.value) {
    fetchSessionForCopy(sourceSessionId.value);
  } else {
    titleInputRef.value?.focus();
  }
});
</script>

<template>
  <div class="container">
    <section class="section">
      <h1 class="title">{{ pageTitle }}</h1>

      <div v-if="loadingSession" class="has-text-centered py-6">
        <span class="loader"></span>
        <p class="mt-3">Loading session...</p>
      </div>

      <form v-else @submit.prevent="handleSubmit">
        <!-- Session Fields -->
        <div class="box">
          <h2 class="subtitle">Session Details</h2>

          <!-- Title -->
          <div class="field">
            <label class="label" for="session-title">Title</label>
            <div class="control">
              <input
                id="session-title"
                ref="titleInputRef"
                v-model="sessionForm.title"
                class="input"
                :class="{ 'is-danger': validationErrors['session.title'] }"
                type="text"
                placeholder="e.g., Upper Body Day"
              />
            </div>
            <p v-if="validationErrors['session.title']" class="help is-danger">
              {{ validationErrors["session.title"] }}
            </p>
          </div>

          <!-- Date -->
          <div class="field">
            <label class="label" for="session-date">Date</label>
            <div class="control">
              <input
                id="session-date"
                v-model="sessionForm.date"
                class="input"
                :class="{ 'is-danger': validationErrors['session.date'] }"
                type="date"
                :max="getTodayDateString()"
              />
            </div>
            <p v-if="validationErrors['session.date']" class="help is-danger">
              {{ validationErrors["session.date"] }}
            </p>
          </div>

          <!-- Type -->
          <div class="field">
            <label class="label" for="session-type">Type</label>
            <div class="control">
              <div
                class="select is-fullwidth"
                :class="{ 'is-danger': validationErrors['session.type'] }"
              >
                <select id="session-type" v-model="sessionForm.session_type">
                  <option value="" disabled>Select type...</option>
                  <option
                    v-for="type in SESSION_TYPES"
                    :key="type.value"
                    :value="type.value"
                  >
                    {{ type.label }}
                  </option>
                </select>
              </div>
            </div>
            <p v-if="validationErrors['session.type']" class="help is-danger">
              {{ validationErrors["session.type"] }}
            </p>
          </div>

          <!-- Comments -->
          <div class="field">
            <label class="label" for="session-comments">Comments</label>
            <div class="control">
              <textarea
                id="session-comments"
                v-model="sessionForm.comments"
                class="textarea"
                placeholder="Optional notes about this session..."
                rows="2"
              ></textarea>
            </div>
          </div>
        </div>

        <!-- Exercises -->
        <div v-for="(exercise, index) in exercises" :key="index" class="box">
          <div
            class="is-flex is-justify-content-space-between is-align-items-center mb-3"
          >
            <h2 class="subtitle mb-0">Exercise {{ index + 1 }}</h2>
            <button
              v-if="exercises.length > 1"
              type="button"
              class="delete"
              aria-label="Remove exercise"
              @click="removeExercise(index)"
            ></button>
          </div>

          <!-- Exercise Title -->
          <div class="field">
            <label class="label" :for="`exercise-${index}-title`">Title</label>
            <div class="control">
              <input
                :id="`exercise-${index}-title`"
                v-model="exercise.title"
                class="input"
                :class="{
                  'is-danger': validationErrors[`exercise.${index}.title`],
                }"
                type="text"
                placeholder="e.g., Bench Press"
              />
            </div>
            <p
              v-if="validationErrors[`exercise.${index}.title`]"
              class="help is-danger"
            >
              {{ validationErrors[`exercise.${index}.title`] }}
            </p>
          </div>

          <!-- Rest time -->
          <div class="field">
            <label class="label" :for="`exercise-${index}-rest`"
              >Rest (sec)</label
            >
            <div class="control">
              <input
                :id="`exercise-${index}-rest`"
                v-model="exercise.rest_seconds"
                class="input"
                :class="{
                  'is-danger': validationErrors[`exercise.${index}.rest`],
                }"
                type="number"
                placeholder="e.g., 60"
                min="0"
              />
            </div>
            <p
              v-if="validationErrors[`exercise.${index}.rest`]"
              class="help is-danger"
            >
              {{ validationErrors[`exercise.${index}.rest`] }}
            </p>
          </div>

          <!-- Sets -->
          <div class="field">
            <label class="label">Sets</label>
            <div
              v-for="(set, setIndex) in exercise.sets"
              :key="setIndex"
              class="columns is-mobile is-vcentered mb-0"
            >
              <div class="column is-4">
                <div class="control">
                  <input
                    :id="`exercise-${index}-set-${setIndex}-weight`"
                    v-model="set.weight"
                    class="input"
                    :class="{
                      'is-danger':
                        validationErrors[
                          `exercise.${index}.set.${setIndex}.weight`
                        ],
                    }"
                    type="number"
                    placeholder="lbs"
                    min="0"
                  />
                </div>
              </div>
              <div class="column is-narrow has-text-centered px-1">
                <span>&times;</span>
              </div>
              <div class="column is-4">
                <div class="control">
                  <input
                    :id="`exercise-${index}-set-${setIndex}-reps`"
                    v-model="set.reps"
                    class="input"
                    :class="{
                      'is-danger':
                        validationErrors[
                          `exercise.${index}.set.${setIndex}.reps`
                        ],
                    }"
                    type="number"
                    placeholder="reps"
                    min="0"
                  />
                </div>
              </div>
              <div class="column">
                <button
                  v-if="setIndex === exercise.sets.length - 1"
                  type="button"
                  class="button is-small is-ghost add-set-btn"
                  aria-label="Add set"
                  @click="addSet(index)"
                >
                  <span class="icon is-small">
                    <IconPlus />
                  </span>
                </button>
              </div>
              <div class="column">
                <button
                  v-if="exercise.sets.length > 1"
                  type="button"
                  class="delete is-small"
                  aria-label="Remove set"
                  @click="removeSet(index, setIndex)"
                ></button>
              </div>
            </div>
            <p
              v-if="validationErrors[`exercise.${index}.sets`]"
              class="help is-danger"
            >
              {{ validationErrors[`exercise.${index}.sets`] }}
            </p>
          </div>

          <!-- Timer Button -->
          <div v-if="canShowTimer(exercise)" class="field">
            <button
              type="button"
              class="button is-fullwidth is-outlined"
              @click="startTimer(index)"
            >
              Start Timer
            </button>
          </div>

          <!-- Exercise Comments -->
          <div class="field">
            <label class="label" :for="`exercise-${index}-comments`"
              >Comments</label
            >
            <div class="control">
              <textarea
                :id="`exercise-${index}-comments`"
                v-model="exercise.comments"
                class="textarea"
                placeholder="Optional notes about this exercise..."
                rows="2"
              ></textarea>
            </div>
          </div>
        </div>

        <!-- Add Exercise Button -->
        <div class="field">
          <button
            type="button"
            class="button is-fullwidth"
            @click="addExercise"
          >
            + Add Another Exercise
          </button>
        </div>

        <!-- Error Display -->
        <div v-if="error" class="notification is-danger is-light">
          {{ error }}
        </div>

        <!-- Submit Button -->
        <div class="field mt-5">
          <button
            type="submit"
            class="button is-primary is-fullwidth"
            :class="{ 'is-loading': loading }"
            :disabled="loading"
          >
            {{ isEditMode ? "Update Session" : "Save Session" }}
          </button>
        </div>
      </form>
    </section>
  </div>

  <!-- Rest Timer Overlay -->
  <RestTimer
    v-if="timerActive && timerExercise"
    :exercise-name="timerExercise.title"
    :rest-seconds="Number(timerExercise.rest_seconds)"
    :sets="
      timerExercise.sets
        .filter((s) => String(s.reps).trim() !== '')
        .map((s) => ({
          weight: String(s.weight).trim() ? parseInt(String(s.weight), 10) : null,
          reps: parseInt(String(s.reps), 10),
        }))
    "
    @close="closeTimer"
  />
</template>

<style scoped>
.set-buttons {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.add-set-btn {
  padding: 0;
  height: 1.25rem;
  width: 1.25rem;
}

.add-set-btn .icon {
  height: 0.875rem;
  width: 0.875rem;
}
</style>
