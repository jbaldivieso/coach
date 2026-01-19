<script setup lang="ts">
import { ref, onMounted } from "vue";
import { RouterLink } from "vue-router";
import { api } from "@/api/client";
import type { Session, PaginatedSessions } from "@/types/lifting";

// Data state
const sessions = ref<Session[]>([]);
const hasMore = ref(false);
const total = ref(0);

// UI state
const loading = ref(false);
const loadingMore = ref(false);
const error = ref<string | null>(null);
const expandedSessionIds = ref<Set<number>>(new Set());

const PAGE_SIZE = 10;

async function fetchSessions(offset: number = 0, append: boolean = false) {
  const isInitialLoad = offset === 0 && !append;

  if (isInitialLoad) {
    loading.value = true;
  } else {
    loadingMore.value = true;
  }
  error.value = null;

  try {
    const response = await api.get<PaginatedSessions>(
      `/api/lifting/sessions/?offset=${offset}&limit=${PAGE_SIZE}`
    );

    if (response.data) {
      if (append) {
        sessions.value = [...sessions.value, ...response.data.items];
      } else {
        sessions.value = response.data.items;
      }
      hasMore.value = response.data.has_more;
      total.value = response.data.total;
    } else {
      error.value = response.error || "Failed to load sessions";
    }
  } catch {
    error.value = "Network error. Please try again.";
  } finally {
    loading.value = false;
    loadingMore.value = false;
  }
}

function loadMore() {
  fetchSessions(sessions.value.length, true);
}

function toggleExpanded(sessionId: number) {
  if (expandedSessionIds.value.has(sessionId)) {
    expandedSessionIds.value.delete(sessionId);
  } else {
    expandedSessionIds.value.add(sessionId);
  }
  // Trigger reactivity by reassigning
  expandedSessionIds.value = new Set(expandedSessionIds.value);
}

function isExpanded(sessionId: number): boolean {
  return expandedSessionIds.value.has(sessionId);
}

function formatWeight(weight_lbs: number | null): string {
  return weight_lbs !== null ? `${weight_lbs} lbs` : "bodyweight";
}

function formatReps(reps: number[]): string {
  return reps.join(", ");
}

onMounted(() => {
  fetchSessions();
});
</script>

<template>
  <div class="container">
    <section class="section">
      <!-- Header with title and add button -->
      <div class="is-flex is-justify-content-space-between is-align-items-center mb-5">
        <h1 class="title mb-0">Sessions</h1>
        <RouterLink :to="{ name: 'create-session' }" class="button is-primary">
          +
        </RouterLink>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="has-text-centered py-6">
        <span class="loader"></span>
        <p class="mt-3">Loading sessions...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="notification is-danger is-light">
        {{ error }}
        <button class="button is-small is-danger is-light ml-3" @click="fetchSessions()">
          Retry
        </button>
      </div>

      <!-- Empty state -->
      <div v-else-if="sessions.length === 0" class="has-text-centered py-6">
        <p class="is-size-5 has-text-grey">No sessions yet</p>
      </div>

      <!-- Sessions list -->
      <div v-else>
        <div v-for="session in sessions" :key="session.id" class="box mb-3">
          <!-- Row 1: Date and Title -->
          <div class="is-flex is-justify-content-space-between is-align-items-center">
            <div>
              <span class="has-text-weight-semibold">{{ session.date }}</span>
              <span class="ml-2">{{ session.title }}</span>
            </div>
            <RouterLink
              :to="{ name: 'edit-session', params: { id: session.id } }"
              class="button is-small is-ghost"
            >
              <span class="icon is-small">
                <span>✏️</span>
              </span>
            </RouterLink>
          </div>

          <!-- Row 2: Expandable exercises summary -->
          <div class="mt-2">
            <button
              class="button is-small is-ghost p-0"
              @click="toggleExpanded(session.id)"
            >
              <span class="icon is-small">
                <span>{{ isExpanded(session.id) ? '▼' : '▶' }}</span>
              </span>
              <span>{{ session.exercises.length }} exercise{{ session.exercises.length !== 1 ? 's' : '' }}</span>
            </button>

            <!-- Expanded exercise details -->
            <div v-if="isExpanded(session.id)" class="mt-3 pl-4">
              <div v-for="exercise in session.exercises" :key="exercise.id" class="mb-2">
                <p>
                  <strong>{{ exercise.title }}</strong>:
                  {{ formatWeight(exercise.weight_lbs) }} &times; {{ formatReps(exercise.reps) }}
                  <span class="has-text-grey is-size-7">({{ exercise.rest_seconds }}s rest)</span>
                </p>
                <p v-if="exercise.comments" class="has-text-grey is-size-7 ml-3">
                  {{ exercise.comments }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Load more button -->
        <div v-if="hasMore" class="has-text-centered mt-4">
          <button
            class="button is-link is-light"
            :class="{ 'is-loading': loadingMore }"
            :disabled="loadingMore"
            @click="loadMore"
          >
            Load more
          </button>
        </div>
      </div>
    </section>
  </div>
</template>
