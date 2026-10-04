<script setup lang="ts">
import { ref, computed } from "vue";
import type { Outing } from "@/types/lifting";
import { parseDate, formatShortDate, formatSet, formatWeight } from "@/utils/format";

// Heaviest set per outing as dots over time; newest in yellow. Bodyweight
// exercises plot their most reps instead. The outing list below is the table view.
const props = defineProps<{ outings: Outing[] }>(); // newest first

const W = 320;
const H = 140;
const PAD = { left: 30, right: 12, top: 14, bottom: 22 };

interface Point {
  key: number;
  x: number;
  y: number;
  value: number;
  label: string;
  newest: boolean;
}

const mode = computed<"weight" | "reps">(() =>
  props.outings.some((o) => o.sets.some((s) => s.weight !== null)) ? "weight" : "reps",
);

const series = computed(() =>
  props.outings
    .map((o) => {
      const sets = o.sets.filter((s) => (mode.value === "weight" ? s.weight !== null : true));
      if (!sets.length) return null;
      const best = sets.reduce((a, b) =>
        mode.value === "weight" ? (b.weight! > a.weight! || (b.weight === a.weight && b.reps > a.reps) ? b : a) : b.reps > a.reps ? b : a,
      );
      return { outing: o, best, value: mode.value === "weight" ? best.weight! : best.reps, t: parseDate(o.date).getTime() };
    })
    .filter((p): p is NonNullable<typeof p> => p !== null)
    .reverse(), // oldest → newest, left → right
);

/** Three clean ticks spanning the data. */
const ticks = computed(() => {
  const values = series.value.map((p) => p.value);
  if (!values.length) return [0];
  let lo = Math.min(...values);
  let hi = Math.max(...values);
  if (lo === hi) {
    lo -= 5;
    hi += 5;
  }
  const raw = (hi - lo) / 2;
  const magnitude = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * magnitude).find((s) => s >= raw)!;
  const start = Math.floor(lo / step) * step;
  const result = [start, start + step, start + 2 * step];
  while (result[result.length - 1]! < hi) result.push(result[result.length - 1]! + step);
  return result;
});

const yMin = computed(() => ticks.value[0]!);
const yMax = computed(() => ticks.value[ticks.value.length - 1]!);
function yFor(v: number) {
  const span = yMax.value - yMin.value || 1;
  return PAD.top + (1 - (v - yMin.value) / span) * (H - PAD.top - PAD.bottom);
}

const points = computed((): Point[] => {
  const s = series.value;
  if (!s.length) return [];
  const t0 = s[0]!.t;
  const t1 = s[s.length - 1]!.t;
  const width = W - PAD.left - PAD.right;
  return s.map((p, i) => ({
    key: p.outing.exercise_id,
    x: t1 === t0 ? PAD.left + width / 2 : PAD.left + ((p.t - t0) / (t1 - t0)) * width,
    y: yFor(p.value),
    value: p.value,
    label: `${formatShortDate(p.outing.date)} · ${formatSet(p.best)}`,
    newest: i === s.length - 1,
  }));
});

/** Month labels where the month changes, skipping ones that would crowd. */
const months = computed(() => {
  const s = series.value;
  const labels: { x: number; text: string }[] = [];
  s.forEach((p, i) => {
    const d = parseDate(p.outing.date);
    const prev = i > 0 ? parseDate(s[i - 1]!.outing.date) : null;
    if (prev && prev.getMonth() === d.getMonth() && prev.getFullYear() === d.getFullYear()) return;
    const x = points.value[i]!.x;
    if (labels.length && x - labels[labels.length - 1]!.x < 34) return;
    labels.push({ x, text: d.toLocaleDateString("en-US", { month: "short" }) });
  });
  return labels;
});

const newest = computed(() => points.value[points.value.length - 1] ?? null);
const active = ref<Point | null>(null);
const description = computed(() => {
  const s = series.value;
  if (!s.length) return "";
  const what = mode.value === "weight" ? "Heaviest set" : "Most reps";
  return `${what} per session, ${formatShortDate(s[0]!.outing.date)} to ${formatShortDate(s[s.length - 1]!.outing.date)}`;
});
</script>

<template>
  <figure v-if="points.length > 1" class="chart">
    <div class="plot">
      <svg :viewBox="`0 0 ${W} ${H}`" role="img" :aria-label="description" @pointerleave="active = null">
        <g aria-hidden="true">
          <template v-for="t in ticks" :key="t">
            <line class="grid" :x1="PAD.left" :x2="W - PAD.right" :y1="yFor(t)" :y2="yFor(t)" />
            <text class="tick" x="0" :y="yFor(t) + 3">{{ mode === "weight" ? formatWeight(t) : t }}</text>
          </template>
          <text v-for="m in months" :key="m.x" class="tick" :x="m.x" :y="H - 4" text-anchor="middle">{{ m.text }}</text>
        </g>
        <g>
          <g
            v-for="p in points"
            :key="p.key"
            class="pt"
            tabindex="0"
            :aria-label="p.label"
            @pointerenter="active = p"
            @pointerdown="active = p"
            @focus="active = p"
            @blur="active = null"
          >
            <circle class="hit" :cx="p.x" :cy="p.y" r="12" />
            <circle class="dot" :class="{ newest: p.newest }" :cx="p.x" :cy="p.y" :r="p.newest ? 5 : 4" />
          </g>
        </g>
        <text
          v-if="newest && !active"
          class="end-label"
          :x="newest.x - 9"
          :y="newest.y + (newest.y < 30 ? 16 : -9)"
          text-anchor="end"
          aria-hidden="true"
        >
          {{ mode === "weight" ? formatWeight(newest.value) : `${newest.value} reps` }}
        </text>
      </svg>
      <div
        v-if="active"
        class="tip"
        :style="{
          left: `${(active.x / W) * 100}%`,
          top: `${(active.y / H) * 100}%`,
          '--shift': active.x / W < 0.2 ? '-12%' : active.x / W > 0.8 ? '-88%' : '-50%',
        }"
        role="status"
      >
        {{ active.label }}
      </div>
    </div>
    <figcaption class="small muted">
      {{ mode === "weight" ? "Heaviest set" : "Most reps" }} per session. Heavy and light days both show up.
    </figcaption>
  </figure>
</template>

<style scoped>
.chart {
  margin: 8px 0 6px;
}
.plot {
  position: relative;
  background: var(--card);
  border-radius: var(--r-lg);
  padding: 8px 6px 4px;
}
svg {
  display: block;
  width: 100%;
  height: auto;
  overflow: visible;
  touch-action: pan-y;
}
.grid {
  stroke: var(--rule);
  stroke-width: 1;
}
.tick {
  font-size: 9px;
  fill: var(--muted);
}
.hit {
  fill: transparent;
}
.dot {
  fill: var(--k);
  stroke: var(--card);
  stroke-width: 2;
}
.dot.newest {
  fill: var(--y);
  stroke: var(--k);
}
.pt {
  outline: none;
  cursor: pointer;
}
.pt:focus-visible .dot {
  stroke: var(--k);
  stroke-width: 3;
}
.end-label {
  font-size: 10px;
  font-weight: 700;
  fill: var(--k);
}
.tip {
  position: absolute;
  transform: translate(var(--shift, -50%), calc(-100% - 12px));
  background: var(--k);
  color: var(--on-k);
  font-size: 12.5px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: var(--r-sm);
  white-space: nowrap;
  pointer-events: none;
}
figcaption {
  margin-top: 4px;
}
</style>
