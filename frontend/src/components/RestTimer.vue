<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { useActiveSessionStore } from "@/stores/activeSession";
import { formatClock } from "@/utils/format";
import { playAlarm, unlockAudio, vibrate } from "@/utils/audio";
import AppBar from "@/components/ui/AppBar.vue";
import Btn from "@/components/ui/Btn.vue";
import Icon from "@/components/ui/Icon.vue";

const props = defineProps<{
  title: string; // "Bench · Rest"
  next: string; // "Set 4 · 155 × 5"
  goLabel: string; // "Go to set 4"
  noteLabel: string; // "Note on Bench"
}>();

const emit = defineEmits<{
  /** Rest is finished or skipped: back to the set. */
  done: [];
  /** Hide the rest screen; the timer keeps running. */
  hide: [];
  note: [];
}>();

const store = useActiveSessionStore();

const now = ref(Date.now());
const flashOn = ref(false);
let ticker: number | null = null;
let flashTimer: number | null = null;
let wakeLock: WakeLockSentinel | null = null;

const remaining = computed(() => store.remaining(now.value));
const total = computed(() => store.rest?.total ?? 0);
const paused = computed(() => store.rest?.pausedRemaining !== null);
const isOver = computed(() => store.rest !== null && !paused.value && remaining.value <= 0);
const progress = computed(() => (total.value > 0 ? Math.min(1, 1 - remaining.value / total.value) : 1));
// Ceil so "0:00" only shows when it's really over
const clock = computed(() => formatClock(Math.ceil(remaining.value)));

function tick() {
  now.value = Date.now();
}

watch(isOver, (over) => {
  if (!over) return;
  playAlarm();
  vibrate();
  // Flash between yellow and black, ending on black; with reduced motion, just go black
  flashOn.value = true;
  if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
  let toggles = 0;
  if (flashTimer) clearInterval(flashTimer);
  flashTimer = window.setInterval(() => {
    flashOn.value = !flashOn.value;
    if (++toggles >= 9) {
      clearInterval(flashTimer!);
      flashTimer = null;
      flashOn.value = true;
    }
  }, 150);
});

function extend() {
  unlockAudio(); // +30 after the alarm starts a new countdown
  if (isOver.value) store.startRest(30);
  else store.adjustRest(30);
  flashOn.value = false;
  tick();
}

function adjust(delta: number) {
  store.adjustRest(delta);
  tick();
}

function togglePause() {
  unlockAudio();
  store.toggleRestPause();
  tick();
}

async function acquireWakeLock() {
  if (!("wakeLock" in navigator)) return;
  try {
    wakeLock = await navigator.wakeLock.request("screen");
  } catch {
    // Not available or denied; the timer still runs
  }
}

function releaseWakeLock() {
  wakeLock?.release();
  wakeLock = null;
}

// The wake lock drops when the app is backgrounded; take it again on return,
// and jump the clock to the right time.
function onVisibilityChange() {
  if (document.visibilityState === "visible") {
    tick();
    acquireWakeLock();
  }
}

onMounted(() => {
  // Reopened after rest already ran out (app was backgrounded or killed)
  if (isOver.value) flashOn.value = true;
  acquireWakeLock();
  ticker = window.setInterval(tick, 250);
  document.addEventListener("visibilitychange", onVisibilityChange);
});

onUnmounted(() => {
  if (ticker) clearInterval(ticker);
  if (flashTimer) clearInterval(flashTimer);
  releaseWakeLock();
  document.removeEventListener("visibilitychange", onVisibilityChange);
});
</script>

<template>
  <div class="rest" :class="{ 'is-over': isOver && flashOn }" role="timer" :aria-label="`Rest, ${clock} left`">
    <AppBar :title="props.title" small transparent :back="() => emit('hide')" />
    <main class="rest-body">
      <div class="clock">
        <b aria-live="off">{{ clock }}</b>
        <div class="of">{{ isOver ? `${formatClock(total)} done` : paused ? "Paused" : `of ${formatClock(total)}` }}</div>
        <div v-if="!isOver" class="bar"><i :style="{ transform: `scaleX(${progress})` }" /></div>
      </div>
      <div class="nextline" :class="{ big: isOver }"><span>{{ isOver ? "Up" : "Next" }}</span>{{ next }}</div>
      <button v-if="!isOver" type="button" class="notelink" @click="emit('note')">
        <Icon name="pencil" size="sm" />{{ noteLabel }}
      </button>
    </main>
    <footer class="rest-dock">
      <div v-if="isOver" class="tbtns two">
        <Btn @click="extend">+30</Btn>
        <Btn variant="primary" @click="emit('done')">{{ goLabel }}</Btn>
      </div>
      <div v-else class="tbtns">
        <Btn :disabled="remaining <= 0" @click="adjust(-15)">−15</Btn>
        <Btn @click="extend">+30</Btn>
        <Btn @click="togglePause">{{ paused ? "Go" : "Pause" }}</Btn>
        <Btn variant="dark" @click="emit('done')">Skip</Btn>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.rest {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  flex-direction: column;
  background: var(--y);
  color: var(--k);
  transition: background-color 0.08s, color 0.08s;
}
.rest-body {
  flex: 1;
  width: 100%;
  max-width: 640px;
  margin: 0 auto;
  padding: 0 var(--gutter);
  overflow-y: auto;
}
.clock {
  text-align: center;
  margin-top: 6vh;
}
.clock b {
  display: block;
  font-size: min(140px, 36vw);
  font-weight: 800;
  font-stretch: 75%;
  line-height: 0.9;
  letter-spacing: -0.02em;
}
.of {
  margin-top: 6px;
  font-size: 20px;
  font-weight: 700;
  font-stretch: 85%;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.bar {
  margin: 22px 8px 0;
  height: 14px;
  background: rgba(0, 0, 0, 0.14);
  border-radius: 2px;
  overflow: hidden;
}
.bar i {
  display: block;
  height: 100%;
  background: var(--k);
  transform-origin: left;
  transition: transform 0.25s linear;
}
.nextline {
  display: flex;
  gap: 10px;
  align-items: baseline;
  margin: 6vh 8px 0;
  padding-top: 12px;
  border-top: 2px solid currentColor;
  font-size: 18px;
  font-weight: 600;
}
.nextline span {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  font-stretch: 85%;
}
.nextline.big {
  font-size: 24px;
  font-weight: 800;
}
.notelink {
  display: flex;
  gap: 8px;
  align-items: center;
  min-height: 44px;
  margin: 8px 8px 0;
  font-size: 14px;
  font-weight: 600;
  text-decoration: underline;
  text-underline-offset: 3px;
}
.rest-dock {
  width: 100%;
  max-width: 640px;
  margin: 0 auto;
  padding: 10px var(--gutter) calc(18px + env(safe-area-inset-bottom));
}
.tbtns {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
}
.tbtns.two {
  grid-template-columns: 1fr 2fr;
}
.tbtns :deep(.btn) {
  min-height: 60px;
  font-size: 17px;
  font-weight: 800;
  background: transparent;
  border: 2px solid var(--k);
  padding: 0 6px;
}
.tbtns :deep(.btn-dark) {
  background: var(--k);
  color: var(--y);
}

/* Rest over: black, with yellow */
.rest.is-over {
  background: var(--k);
  color: var(--y);
}
.rest.is-over .tbtns :deep(.btn) {
  border-color: var(--y);
  color: var(--y);
}
.rest.is-over .tbtns :deep(.btn-primary) {
  background: var(--y);
  color: var(--k);
}
</style>
