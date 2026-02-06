<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { RouterLink } from "vue-router";
import { api } from "@/api/client";
import type { CalendarMonth } from "@/types/lifting";
import IconChevronLeft from "@/components/svg/IconChevronLeft.vue";
import IconChevronRight from "@/components/svg/IconChevronRight.vue";

// State
const now = new Date();
const currentYear = ref(now.getFullYear());
const currentMonth = ref(now.getMonth() + 1); // 1-indexed
const calendarData = ref<CalendarMonth | null>(null);
const loading = ref(false);

// Computed
const monthName = computed(() => {
  const date = new Date(currentYear.value, currentMonth.value - 1, 1);
  return date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
});

const isCurrentMonth = computed(() => {
  return (
    currentYear.value === now.getFullYear() &&
    currentMonth.value === now.getMonth() + 1
  );
});

const sessionsByDate = computed(() => {
  const map = new Map<string, number>();
  if (calendarData.value) {
    for (const session of calendarData.value.sessions) {
      map.set(session.date, session.session_id);
    }
  }
  return map;
});

interface CalendarDay {
  day: number | null;
  date: string | null;
  isToday: boolean;
  sessionId: number | null;
}

const calendarDays = computed((): CalendarDay[][] => {
  const year = currentYear.value;
  const month = currentMonth.value;

  // First day of month (0 = Sunday)
  const firstDay = new Date(year, month - 1, 1).getDay();
  // Days in month
  const daysInMonth = new Date(year, month, 0).getDate();

  const today = new Date();
  const todayStr =
    today.getFullYear() === year && today.getMonth() + 1 === month
      ? today.getDate()
      : null;

  const weeks: CalendarDay[][] = [];
  let currentWeek: CalendarDay[] = [];

  // Add empty cells for days before first day of month
  for (let i = 0; i < firstDay; i++) {
    currentWeek.push({ day: null, date: null, isToday: false, sessionId: null });
  }

  // Add days of month
  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    const sessionId = sessionsByDate.value.get(dateStr) || null;

    currentWeek.push({
      day,
      date: dateStr,
      isToday: day === todayStr,
      sessionId,
    });

    if (currentWeek.length === 7) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  }

  // Fill remaining days in last week
  while (currentWeek.length > 0 && currentWeek.length < 7) {
    currentWeek.push({ day: null, date: null, isToday: false, sessionId: null });
  }
  if (currentWeek.length > 0) {
    weeks.push(currentWeek);
  }

  return weeks;
});

// Methods
async function fetchCalendarData() {
  loading.value = true;
  try {
    const response = await api.get<CalendarMonth>(
      `/api/lifting/sessions/calendar/?year=${currentYear.value}&month=${currentMonth.value}`,
    );
    if (response.data) {
      calendarData.value = response.data;
    }
  } finally {
    loading.value = false;
  }
}

function previousMonth() {
  if (currentMonth.value === 1) {
    currentMonth.value = 12;
    currentYear.value--;
  } else {
    currentMonth.value--;
  }
}

function nextMonth() {
  if (isCurrentMonth.value) return;

  if (currentMonth.value === 12) {
    currentMonth.value = 1;
    currentYear.value++;
  } else {
    currentMonth.value++;
  }
}

// Watch for month/year changes
watch([currentYear, currentMonth], () => {
  fetchCalendarData();
});

onMounted(() => {
  fetchCalendarData();
});
</script>

<template>
  <div class="calendar-container">
    <!-- Header with navigation -->
    <div class="calendar-header">
      <button class="button is-ghost is-small" @click="previousMonth">
        <span class="icon">
          <IconChevronLeft />
        </span>
      </button>
      <span class="calendar-title">{{ monthName }}</span>
      <button
        class="button is-ghost is-small"
        :class="{ 'is-invisible': isCurrentMonth }"
        :disabled="isCurrentMonth"
        @click="nextMonth"
      >
        <span class="icon">
          <IconChevronRight />
        </span>
      </button>
    </div>

    <!-- Weekday headers -->
    <div class="calendar-weekdays">
      <span v-for="day in ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']" :key="day">
        {{ day }}
      </span>
    </div>

    <!-- Calendar grid -->
    <div class="calendar-grid" :class="{ 'is-loading': loading }">
      <div v-for="(week, weekIndex) in calendarDays" :key="weekIndex" class="calendar-week">
        <template v-for="(dayObj, dayIndex) in week" :key="dayIndex">
          <!-- Empty cell -->
          <span v-if="!dayObj.day" class="calendar-day empty"></span>

          <!-- Day with session - link to session -->
          <RouterLink
            v-else-if="dayObj.sessionId"
            :to="{ name: 'session-detail', params: { id: dayObj.sessionId } }"
            class="calendar-day has-session"
            :class="{ 'is-today': dayObj.isToday }"
          >
            {{ dayObj.day }}
          </RouterLink>

          <!-- Day without session -->
          <span
            v-else
            class="calendar-day"
            :class="{ 'is-today': dayObj.isToday }"
          >
            {{ dayObj.day }}
          </span>
        </template>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.calendar-container {
  background: var(--bulma-primary-light-invert);
  border-radius: var(--bulma-radius, 6px);
  padding: 1rem;
  box-shadow: var(--bulma-shadow, 0 2px 3px rgba(10, 10, 10, 0.1));
}

.calendar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  .icon {
    width: 0.75rem;
    height: 0.75rem;
    svg {
      fill: var(--bulma-primary-dark);
      width: 100%;
      height: 100%;
    }
  }
}

.calendar-title {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--bulma-primary-dark-invert);
}

.calendar-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  text-align: center;
  font-size: 0.75rem;
  color: var(--bulma-primary-dark-invert);
  margin-bottom: 0.5rem;
}

.calendar-grid {
  opacity: 1;
  transition: opacity 0.15s;
  &.is-loading {
    opacity: 0.5;
  }
}

.calendar-week {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}

.calendar-day {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  border-radius: 50%;
  text-decoration: none;
  color: var(--bulma-primary-light);
  &.empty {
    background: transparent;
  }
  &.is-today {
    border: 2px solid var(--bulma-primary-invert);
  }
  &.has-session {
    background: var(--bulma-primary);
    color: var(--bulma-primary-dark);
    font-weight: 600;
  }

  &.has-session:hover {
    background: var(--bulma-primary);
    color: var(--bulma-primary-invert);
  }
}
</style>
