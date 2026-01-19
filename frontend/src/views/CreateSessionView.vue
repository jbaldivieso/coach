<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { api } from "@/api/client";
import type { ExerciseFormData, SessionFormData, Session } from "@/types/lifting";
import { SESSION_TYPES } from "@/types/lifting";

const router = useRouter();

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

function getTodayDateString(): string {
  return new Date().toISOString().split("T")[0] as string;
}

function createEmptyExercise(): ExerciseFormData {
  return {
    title: "",
    weight_lbs: "",
    rest_seconds: "",
    reps: "",
  };
}

function addExercise() {
  exercises.value.push(createEmptyExercise());
}

function removeExercise(index: number) {
  if (exercises.value.length > 1) {
    exercises.value.splice(index, 1);
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
    })),
  };
}

async function handleSubmit() {
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
  titleInputRef.value?.focus();
});
</script>

<template>
  <div class="container">
    <section class="section">
      <h1 class="title">New Session</h1>

      <form @submit.prevent="handleSubmit">
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
            Save Session
          </button>
        </div>
      </form>
    </section>
  </div>
</template>
