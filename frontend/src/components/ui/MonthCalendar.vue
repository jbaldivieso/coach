<script setup lang="ts">
import { computed } from "vue";
import { RouterLink } from "vue-router";
import type { SessionDate } from "@/types/lifting";
import { toISODate } from "@/utils/format";

const props = withDefaults(
  defineProps<{
    year: number;
    month: number; // 1-12
    sessions: SessionDate[];
    /** Small squares for the year view; no numbers or links. */
    mini?: boolean;
    loading?: boolean;
  }>(),
  { mini: false, loading: false },
);

interface Day {
  key: string;
  day: number;
  inMonth: boolean;
  isToday: boolean;
  sessionId: number | null;
}

const DOW = ["S", "M", "T", "W", "T", "F", "S"];

const days = computed((): Day[] => {
  const sessionByDate = new Map(props.sessions.map((s) => [s.date, s.session_id]));
  const first = new Date(props.year, props.month - 1, 1);
  const daysInMonth = new Date(props.year, props.month, 0).getDate();
  const lead = first.getDay();
  const today = toISODate(new Date());

  const result: Day[] = [];
  // Mini months only need blank leading cells; the full calendar shows neighbouring days faded.
  const start = new Date(props.year, props.month - 1, 1 - lead);
  const total = props.mini ? lead + daysInMonth : Math.ceil((lead + daysInMonth) / 7) * 7;
  for (let i = 0; i < total; i++) {
    const date = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i);
    const iso = toISODate(date);
    const inMonth = date.getMonth() === props.month - 1;
    result.push({
      key: iso,
      day: date.getDate(),
      inMonth,
      isToday: iso === today,
      sessionId: inMonth ? (sessionByDate.get(iso) ?? null) : null,
    });
  }
  return result;
});

const label = computed(() =>
  new Date(props.year, props.month - 1, 1).toLocaleDateString("en-US", { month: "long", year: "numeric" }),
);
</script>

<template>
  <div v-if="mini" class="mini" role="img" :aria-label="`${label}: ${sessions.length} training days`">
    <i v-for="d in days" :key="d.key" :class="{ blank: !d.inMonth, on: d.sessionId }" />
  </div>
  <div v-else class="cal" :class="{ 'is-loading': loading }" role="group" :aria-label="label">
    <span v-for="(d, i) in DOW" :key="`dow-${i}`" class="dow" aria-hidden="true">{{ d }}</span>
    <template v-for="d in days" :key="d.key">
      <RouterLink
        v-if="d.sessionId"
        :to="{ name: 'session-detail', params: { id: d.sessionId } }"
        class="day on"
        :class="{ today: d.isToday }"
        :aria-label="`${d.key}: trained`"
      >
        {{ d.day }}
      </RouterLink>
      <span v-else class="day" :class="{ out: !d.inMonth, today: d.isToday }">{{ d.day }}</span>
    </template>
  </div>
</template>

<style scoped>
.cal {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
  text-align: center;
  font-size: 14px;
  background: var(--card);
  border-radius: var(--r-lg);
  padding: 8px 6px;
  transition: opacity 0.15s;
}
.cal.is-loading {
  opacity: 0.55;
}
.dow {
  font-size: 11px;
  color: var(--muted);
  font-weight: 700;
  padding-bottom: 4px;
}
.day {
  height: 38px;
  display: grid;
  place-items: center;
  border-radius: var(--r-sm);
}
.day.on {
  background: var(--k);
  color: var(--y);
  font-weight: 700;
}
.day.today {
  outline: 2px solid var(--k);
  outline-offset: -2px;
  font-weight: 800;
}
.day.today.on {
  outline-offset: 2px;
}
.day.out {
  color: var(--muted);
  opacity: 0.45;
}
.mini {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 2px;
}
.mini i {
  aspect-ratio: 1;
  border-radius: 2px;
  background: #dcddda;
}
.mini i.on {
  background: var(--k);
}
.mini i.blank {
  background: transparent;
}
</style>
