<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { useRouter, useRoute } from "vue-router";
import { api } from "@/api/client";
import type { Session, Set } from "@/types/lifting";
import { SESSION_TYPES } from "@/types/lifting";
import PencilIcon from "@/components/svg/IconPencil.vue";
import CopyIcon from "@/components/svg/IconCopy.vue";

const router = useRouter();
const route = useRoute();

const sessionId = computed(() => Number(route.params.id));

// State
const session = ref<Session | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);
const showDeleteConfirm = ref(false);
const deleting = ref(false);

function getSessionTypeLabel(type: string): string {
  const found = SESSION_TYPES.find((t) => t.value === type);
  return found ? found.label : type;
}

function formatSets(sets: Set[]): string {
  return sets
    .map((s) => {
      const weight = s.weight !== null ? `${s.weight} lbs` : "bodyweight";
      return `${weight} x ${s.reps}`;
    })
    .join(", ");
}

function formatRestTime(seconds: number): string {
  if (seconds >= 60) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return secs > 0 ? `${mins}m ${secs}s` : `${mins}m`;
  }
  return `${seconds}s`;
}

async function fetchSession() {
  loading.value = true;
  error.value = null;

  const response = await api.get<Session>(
    `/api/lifting/sessions/${sessionId.value}/`,
  );

  if (response.data) {
    session.value = response.data;
  } else {
    error.value = response.error || "Failed to load session";
  }

  loading.value = false;
}

function showDeleteConfirmation() {
  showDeleteConfirm.value = true;
}

function cancelDelete() {
  showDeleteConfirm.value = false;
}

async function confirmDelete() {
  deleting.value = true;

  await api.fetchCsrfToken();
  const response = await api.delete(`/api/lifting/sessions/${sessionId.value}/`);

  if (response.error) {
    error.value = response.error;
    deleting.value = false;
    showDeleteConfirm.value = false;
  } else {
    router.push({ name: "home" });
  }
}

onMounted(() => {
  fetchSession();
});
</script>

<template>
  <div class="container">
    <section class="section">
      <!-- Loading State -->
      <div v-if="loading" class="has-text-centered py-6">
        <span class="loader"></span>
        <p class="mt-3">Loading session...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="notification is-danger is-light">
        <p>{{ error }}</p>
        <button
          data-testid="retry-button"
          class="button is-danger is-outlined mt-3"
          @click="fetchSession"
        >
          Retry
        </button>
      </div>

      <!-- Session Content -->
      <template v-else-if="session">
        <!-- Header -->
        <div class="is-flex is-justify-content-space-between is-align-items-start mb-4">
          <div>
            <h1 class="title mb-2">{{ session.title }}</h1>
            <p class="subtitle is-6 mb-1">
              {{ session.date }} &bull; {{ getSessionTypeLabel(session.session_type) }}
            </p>
          </div>
          <div class="buttons">
            <router-link
              :to="{ name: 'edit-session', params: { id: session.id } }"
              class="button is-small is-ghost"
            >
              <PencilIcon />
            </router-link>
            <router-link
              :to="{ name: 'copy-session', params: { id: session.id } }"
              class="button is-small is-ghost"
            >
              <CopyIcon />
            </router-link>
          </div>
        </div>

        <!-- Session Comments -->
        <div v-if="session.comments" class="box mb-4">
          <p>{{ session.comments }}</p>
        </div>

        <!-- Exercises -->
        <div
          v-for="exercise in session.exercises"
          :key="exercise.id"
          class="box"
        >
          <h2 class="subtitle mb-2">{{ exercise.title }}</h2>
          <p class="mb-2">{{ formatSets(exercise.sets) }}</p>
          <p class="is-size-7 has-text-grey mb-2">
            Rest: {{ formatRestTime(exercise.rest_seconds) }}
          </p>
          <p v-if="exercise.comments" class="is-italic has-text-grey-dark">
            {{ exercise.comments }}
          </p>
        </div>

        <!-- Delete Section -->
        <div class="mt-5">
          <template v-if="!showDeleteConfirm">
            <button
              data-testid="delete-button"
              class="button is-danger is-outlined is-fullwidth"
              @click="showDeleteConfirmation"
            >
              Delete Session
            </button>
          </template>
          <template v-else>
            <div class="notification is-danger is-light">
              <p class="mb-3">Are you sure you want to delete this session?</p>
              <div class="buttons">
                <button
                  data-testid="confirm-delete"
                  class="button is-danger"
                  :class="{ 'is-loading': deleting }"
                  :disabled="deleting"
                  @click="confirmDelete"
                >
                  Delete
                </button>
                <button
                  data-testid="cancel-delete"
                  class="button"
                  :disabled="deleting"
                  @click="cancelDelete"
                >
                  Cancel
                </button>
              </div>
            </div>
          </template>
        </div>
      </template>
    </section>
  </div>
</template>
<style scoped>
.buttons {gap: 0}
</style>
