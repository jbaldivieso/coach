<script setup lang="ts">
import { ref } from "vue";

interface Change {
  date: string;
  title: string;
  description?: string;
}

interface ChangeGroup {
  date: string;
  changes: Change[];
}

const changeGroups = ref<ChangeGroup[]>([
  {
    date: "2026-01-31",
    changes: [
      {
        date: "2026-01-31",
        title: "New approach to sets: weight can change as well as reps!",
        description: "OUR NUMBER 1 MOST REQUESTED FEATURE!!!",
      },
      {
        date: "2026-01-31",
        title: "Search sessions and exercises",
        description: "Want to see how your benching efforts have changed over time? Search it up!"
      },
      {
        date: "2026-01-31",
        title: "Session calendar",
        description: "Get sense of when your workouts have been"
      },
    ],
  },
]);

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}
</script>

<template>
  <div class="container">
    <section class="section">
      <div class="mb-5">
        <h1 class="title">What's New</h1>
      </div>

      <div class="changelog">
        <div
          v-for="group in changeGroups"
          :key="group.date"
          class="changelog-group mb-6"
        >
          <!-- Date header -->
          <div class="changelog-date mb-4">
            <h2>
              {{ formatDate(group.date)}}
            </h2>
          </div>

          <!-- Changes for this date -->
          <div class="changelog-items">
            <div
              v-for="change in group.changes"
              :key="change.title"
              class="box changelog-item"
            >
              <div class="media">
                <div class="media-left">
                  <span class="icon has-text-primary">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 24 24"
                      fill="currentColor"
                      class="changelog-icon"
                    >
                      <path
                        d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
                      />
                    </svg>
                  </span>
                </div>
                <div class="media-content">
                  <h3 class="mb-2">
                    {{ change.title }}
                  </h3>
                  <p
                    v-if="change.description"
                    class="is-size-6"
                  >
                    {{ change.description }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.changelog {
  max-width: 800px;
  margin: 0 auto;
}

.changelog-group {
  position: relative;
}

.changelog-date {
  position: sticky;
  top: 1rem;
  z-index: 10;
}

.changelog-items {
  margin-left: 1rem;
  border-left: 2px solid var(--bulma-primary-light);
  padding-left: 1.5rem;
}

.changelog-item {
  position: relative;
  transition: all 0.2s ease;
}

.changelog-item::before {
  content: "";
  position: absolute;
  left: -1.875rem;
  top: 1.5rem;
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
  background-color: var(--bulma-primary);
  border: 3px solid var(--bulma-scheme-main);
}

.changelog-item:hover {
  box-shadow: 0 0.5em 1em -0.125em rgba(10, 10, 10, 0.15),
    0 0px 0 1px var(--bulma-primary-light);
  transform: translateX(0.25rem);
}

.changelog-icon {
  width: 1.5rem;
  height: 1.5rem;
}

@media screen and (max-width: 768px) {
  .changelog-items {
    margin-left: 0;
    border-left: none;
    padding-left: 0;
  }

  .changelog-item::before {
    display: none;
  }
}
h2 {
  color: var(--color1);
  font-size: 150%;
}
h3 {
  color: var(--bulma-primary-bold);
}
</style>
