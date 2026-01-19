<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { api } from "@/api/client";
import type { ExerciseFormData, SessionFormData, Session, ExerciseEditState } from "@/types/lifting";
import { SESSION_TYPES } from "@/types/lifting";

const router = useRouter();
const route = useRoute();

// Edit mode detection
const isEditMode = computed(() => route.name === 'edit-session');
const sessionId = computed(() => isEditMode.value ? Number(route.params.id) : null);
const pageTitle = computed(() => isEditMode.value ? 'Edit Session' : 'New Session');

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

function getTodayDateString(): string {
  return new Date().toISOString().split("T")[0] as string;
}

function createEmptyExercise(): ExerciseFormData {
  return {
    title: "",
    weight_lbs: "",
    rest_seconds: "",
    reps: "",
    comments: "",
  };
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
      const exerciseFormDataList: ExerciseFormData[] = response.data.exercises.map(ex => ({
        title: ex.title,
        weight_lbs: ex.weight_lbs?.toString() || "",
        rest_seconds: ex.rest_seconds.toString(),
        reps: ex.reps.join(", "),
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
  exercises.value.forEach((exercise, index) => {
    if (!exercise.title.trim()) {
      validationErrors.value[`exercise.${index}.title`] = "Exercise title is required";
      isValid = false;
    }

    const restValue = String(exercise.rest_seconds).trim();
    if (!restValue) {
      validationErrors.value[`exercise.${index}.rest`] = "Rest time is required";
      isValid = false;
    } else if (isNaN(Number(restValue)) || Number(restValue) < 0) {
      validationErrors.value[`exercise.${index}.rest`] = "Rest must be a positive number";
      isValid = false;
    }

    if (!exercise.reps.trim()) {
      validationErrors.value[`exercise.${index}.reps`] = "Reps are required";
      isValid = false;
    } else {
      const repsArray = exercise.reps.split(",").map((r) => r.trim()).filter((r) => r !== "");
      const invalidReps = repsArray.some((r) => isNaN(parseInt(r, 10)));
      if (invalidReps || repsArray.length === 0) {
        validationErrors.value[`exercise.${index}.reps`] = "Reps must be comma-separated numbers (e.g., 5, 5, 5)";
        isValid = false;
      }
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
      weight_lbs: String(ex.weight_lbs).trim() ? parseInt(String(ex.weight_lbs), 10) : null,
      rest_seconds: parseInt(String(ex.rest_seconds), 10),
      reps: ex.reps.split(",").map((r) => parseInt(r.trim(), 10)).filter((r) => !isNaN(r)),
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
      sessionPayload
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
          exerciseData
        );
      } else if (sessionId.value) {
        // Create new exercise
        await api.post(
          `/api/lifting/sessions/${sessionId.value}/exercises/`,
          exerciseData
        );
      }
    }

    // Success - redirect to home
    router.push({ name: "home" });
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
    const response = await api.post<Session>("/api/lifting/sessions/with-exercises/", payload);

    if (response.data) {
      router.push({ name: "home" });
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
              <div class="select is-fullwidth" :class="{ 'is-danger': validationErrors['session.type'] }">
                <select id="session-type" v-model="sessionForm.session_type">
                  <option value="" disabled>Select type...</option>
                  <option v-for="type in SESSION_TYPES" :key="type.value" :value="type.value">
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
          <div class="is-flex is-justify-content-space-between is-align-items-center mb-3">
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
                :class="{ 'is-danger': validationErrors[`exercise.${index}.title`] }"
                type="text"
                placeholder="e.g., Bench Press"
              />
            </div>
            <p v-if="validationErrors[`exercise.${index}.title`]" class="help is-danger">
              {{ validationErrors[`exercise.${index}.title`] }}
            </p>
          </div>

          <!-- Weight and Rest -->
          <div class="columns is-mobile">
            <div class="column">
              <div class="field">
                <label class="label" :for="`exercise-${index}-weight`">Weight (lbs)</label>
                <div class="control">
                  <input
                    :id="`exercise-${index}-weight`"
                    v-model="exercise.weight_lbs"
                    class="input"
                    type="number"
                    placeholder="Optional"
                    min="0"
                  />
                </div>
              </div>
            </div>
            <div class="column">
              <div class="field">
                <label class="label" :for="`exercise-${index}-rest`">Rest (sec)</label>
                <div class="control">
                  <input
                    :id="`exercise-${index}-rest`"
                    v-model="exercise.rest_seconds"
                    class="input"
                    :class="{ 'is-danger': validationErrors[`exercise.${index}.rest`] }"
                    type="number"
                    placeholder="e.g., 60"
                    min="0"
                  />
                </div>
                <p v-if="validationErrors[`exercise.${index}.rest`]" class="help is-danger">
                  {{ validationErrors[`exercise.${index}.rest`] }}
                </p>
              </div>
            </div>
          </div>

          <!-- Reps -->
          <div class="field">
            <label class="label" :for="`exercise-${index}-reps`">Reps</label>
            <div class="control">
              <input
                :id="`exercise-${index}-reps`"
                v-model="exercise.reps"
                class="input"
                :class="{ 'is-danger': validationErrors[`exercise.${index}.reps`] }"
                type="text"
                placeholder="e.g., 5, 5, 5"
              />
            </div>
            <p class="help" :class="{ 'is-danger': validationErrors[`exercise.${index}.reps`] }">
              {{ validationErrors[`exercise.${index}.reps`] || "Enter comma-separated numbers for each set" }}
            </p>
          </div>

          <!-- Exercise Comments -->
          <div class="field">
            <label class="label" :for="`exercise-${index}-comments`">Comments</label>
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
          <button type="button" class="button is-link is-light is-fullwidth" @click="addExercise">
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
            {{ isEditMode ? 'Update Session' : 'Save Session' }}
          </button>
        </div>
      </form>
    </section>
  </div>
</template>
