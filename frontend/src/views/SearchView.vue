<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { RouterLink } from "vue-router";
import { api } from "@/api/client";
import type {
  AutocompleteItem,
  AutocompleteResponse,
  SearchResult,
  SearchResultsResponse,
  SearchFilter,
} from "@/types/lifting";

// Search state
const searchQuery = ref("");
const autocompleteItems = ref<AutocompleteItem[]>([]);
const showAutocomplete = ref(false);
const highlightedIndex = ref(-1);

// Filter state
const sessionFilter = ref<SearchFilter | null>(null);
const exerciseFilter = ref<SearchFilter | null>(null);

// Results state
const results = ref<SearchResult[]>([]);
const total = ref(0);
const loading = ref(false);
const error = ref<string | null>(null);

// Debounce timer
let debounceTimer: ReturnType<typeof setTimeout> | null = null;

// Computed: active filters for display
const activeFilters = computed(() => {
  const filters: SearchFilter[] = [];
  if (sessionFilter.value) filters.push(sessionFilter.value);
  if (exerciseFilter.value) filters.push(exerciseFilter.value);
  return filters;
});

// Computed: both filters active (for responsive column visibility)
const bothFiltersActive = computed(
  () => sessionFilter.value !== null && exerciseFilter.value !== null,
);

// Fetch autocomplete suggestions
async function fetchAutocomplete(query: string) {
  if (query.length < 3) {
    autocompleteItems.value = [];
    showAutocomplete.value = false;
    return;
  }

  const response = await api.get<AutocompleteResponse>(
    `/api/lifting/search/autocomplete/?q=${encodeURIComponent(query)}`,
  );

  if (response.data) {
    // Filter out items that match existing filters
    let items = response.data.items;
    if (sessionFilter.value) {
      items = items.filter((i) => i.type !== "session");
    }
    if (exerciseFilter.value) {
      items = items.filter((i) => i.type !== "exercise");
    }
    autocompleteItems.value = items;
    showAutocomplete.value = items.length > 0;
    highlightedIndex.value = -1;
  }
}

// Fetch search results
async function fetchResults() {
  loading.value = true;
  error.value = null;

  const params = new URLSearchParams();
  if (sessionFilter.value) {
    params.set("session_title", sessionFilter.value.value);
  }
  if (exerciseFilter.value) {
    params.set("exercise_title", exerciseFilter.value.value);
  }

  const url = `/api/lifting/search/results/${params.toString() ? "?" + params.toString() : ""}`;

  try {
    const response = await api.get<SearchResultsResponse>(url);
    if (response.data) {
      results.value = response.data.items;
      total.value = response.data.total;
    } else {
      error.value = response.error || "Failed to load results";
    }
  } catch {
    error.value = "Network error. Please try again.";
  } finally {
    loading.value = false;
  }
}

// Handle input changes with debounce
function onSearchInput() {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }
  debounceTimer = setTimeout(() => {
    fetchAutocomplete(searchQuery.value);
  }, 300);
}

// Handle keyboard navigation in autocomplete
function onKeydown(event: KeyboardEvent) {
  if (!showAutocomplete.value || autocompleteItems.value.length === 0) {
    return;
  }

  if (event.key === "ArrowDown") {
    event.preventDefault();
    highlightedIndex.value =
      (highlightedIndex.value + 1) % autocompleteItems.value.length;
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    highlightedIndex.value =
      highlightedIndex.value <= 0
        ? autocompleteItems.value.length - 1
        : highlightedIndex.value - 1;
  } else if (event.key === "Enter" && highlightedIndex.value >= 0) {
    event.preventDefault();
    const item = autocompleteItems.value[highlightedIndex.value];
    if (item) {
      selectItem(item);
    }
  } else if (event.key === "Escape") {
    showAutocomplete.value = false;
    highlightedIndex.value = -1;
  }
}

// Select an autocomplete item
function selectItem(item: AutocompleteItem) {
  const filter: SearchFilter = {
    type: item.type,
    id: item.id,
    label: item.label,
    value: item.value,
  };

  if (item.type === "session") {
    sessionFilter.value = filter;
  } else {
    exerciseFilter.value = filter;
  }

  // Clear input and hide autocomplete
  searchQuery.value = "";
  autocompleteItems.value = [];
  showAutocomplete.value = false;
  highlightedIndex.value = -1;

  // Fetch new results
  fetchResults();
}

// Remove a filter
function removeFilter(filter: SearchFilter) {
  if (filter.type === "session") {
    sessionFilter.value = null;
  } else {
    exerciseFilter.value = null;
  }
  fetchResults();
}

// Format weight for display
function formatWeight(weight: number | null): string {
  return weight !== null ? `${weight} lbs` : "bodyweight";
}

// Format reps for display
function formatReps(reps: number[]): string {
  return reps.join(", ");
}

// Get autocomplete item prefix
function getItemPrefix(type: string): string {
  return type === "session" ? "Session:" : "Exercise:";
}

// Close autocomplete when clicking outside
function onClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement;
  if (!target.closest(".autocomplete-container")) {
    showAutocomplete.value = false;
  }
}

// Watch for filter changes to refetch results
watch([sessionFilter, exerciseFilter], () => {
  // Results are fetched in selectItem and removeFilter
});

onMounted(() => {
  fetchResults();
  document.addEventListener("click", onClickOutside);
});
</script>

<template>
  <div class="container">
    <section class="section">
      <h1 class="title">Search</h1>

      <!-- Search input with autocomplete -->
      <div class="autocomplete-container mb-4">
        <div class="field">
          <div class="control">
            <input
              v-model="searchQuery"
              type="text"
              class="input"
              placeholder="Search sessions or exercises..."
              @input="onSearchInput"
              @keydown="onKeydown"
              @focus="showAutocomplete = autocompleteItems.length > 0"
            />
          </div>
        </div>

        <!-- Autocomplete dropdown -->
        <div v-if="showAutocomplete" class="autocomplete-dropdown box p-0">
          <div
            v-for="(item, index) in autocompleteItems"
            :key="`${item.type}-${item.id ?? index}`"
            class="autocomplete-item p-3"
            :class="{ 'is-highlighted': index === highlightedIndex }"
            @click="selectItem(item)"
          >
            <span class="has-text-weight-semibold">{{
              getItemPrefix(item.type)
            }}</span>
            {{ item.label }}
          </div>
        </div>
      </div>

      <!-- Filter pills -->
      <div v-if="activeFilters.length > 0" class="tags mb-4">
        <span
          v-for="filter in activeFilters"
          :key="`${filter.type}-${filter.id ?? filter.value}`"
          class="tag is-medium is-primary is-light"
        >
          {{ filter.type === "session" ? "Session" : "Exercise" }}:
          {{ filter.value }}
          <button
            class="delete is-small"
            @click="removeFilter(filter)"
          ></button>
        </span>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="has-text-centered py-6">
        <span class="loader"></span>
        <p class="mt-3">Searching...</p>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="notification is-danger is-light">
        {{ error }}
        <button
          class="button is-small is-danger is-light ml-3"
          @click="fetchResults()"
        >
          Retry
        </button>
      </div>

      <!-- Empty state -->
      <div v-else-if="results.length === 0" class="has-text-centered py-6">
        <p class="is-size-5 has-text-grey">No results found</p>
      </div>

      <!-- Results table -->
      <div v-else class="table-container">
        <table class="table is-fullwidth">
          <thead>
            <tr>
              <th>Session</th>
              <th v-if="!exerciseFilter">Exercise</th>
              <th>Weight</th>
              <th :class="{ 'is-hidden-mobile': !bothFiltersActive }">Reps</th>
              <th :class="{ 'is-hidden-mobile': !bothFiltersActive }">Rest</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="result in results" :key="result.exercise_id">
              <td>
                <RouterLink
                  :to="{
                    name: 'edit-session',
                    params: { id: result.session_id },
                  }"
                >
                  <template v-if="sessionFilter">{{
                    result.session_date
                  }}</template>
                  <template v-else
                    >{{ result.session_date }}:
                    {{ result.session_title }}</template
                  >
                </RouterLink>
              </td>
              <td v-if="!exerciseFilter">{{ result.exercise_title }}</td>
              <td>{{ formatWeight(result.weight_lbs) }}</td>
              <td :class="{ 'is-hidden-mobile': !bothFiltersActive }">
                {{ formatReps(result.reps) }}
              </td>
              <td :class="{ 'is-hidden-mobile': !bothFiltersActive }">
                {{ result.rest_seconds }}s
              </td>
            </tr>
          </tbody>
        </table>
        <p class="has-text-grey is-size-7">
          {{ total }} result{{ total !== 1 ? "s" : "" }}
        </p>
      </div>
    </section>
  </div>
</template>

<style scoped>
.autocomplete-container {
  position: relative;
}

.autocomplete-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  z-index: 10;
  max-height: 300px;
  overflow-y: auto;
}

.autocomplete-item {
  cursor: pointer;
  border-bottom: 1px solid var(--bulma-border);
}

.autocomplete-item:last-child {
  border-bottom: none;
}

.autocomplete-item:hover,
.autocomplete-item.is-highlighted {
  background-color: var(--bulma-scheme-main-bis);
}
.table td,
.table th {
  border-color: var(--color1);
}
</style>
