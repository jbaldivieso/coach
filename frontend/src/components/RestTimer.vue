<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import type { Set } from "@/types/lifting";

const props = defineProps<{
  exerciseName: string;
  restSeconds: number;
  sets: Set[];
}>();

const emit = defineEmits<{
  close: [];
}>();

// Timer state
const timeRemaining = ref(props.restSeconds);
const isRunning = ref(true);
const isComplete = ref(false);
const isFlashing = ref(false);
const flashInverted = ref(false);

// Wake lock
let wakeLock: WakeLockSentinel | null = null;

// Audio context for alarm sound
let audioContext: AudioContext | null = null;
let audioElement: HTMLAudioElement | null = null;

// Timer interval
let timerInterval: number | null = null;
let flashInterval: number | null = null;

const formattedTime = computed(() => {
  const minutes = Math.floor(timeRemaining.value / 60);
  const seconds = timeRemaining.value % 60;
  if (minutes > 0) {
    return `${minutes}:${seconds.toString().padStart(2, "0")}`;
  }
  return seconds.toString();
});

const setsDisplay = computed(() => {
  return props.sets
    .map((s) => {
      const weightPart = s.weight !== null ? `${s.weight} lbs` : "bodyweight";
      return `${weightPart} x ${s.reps}`;
    })
    .join(", ");
});

async function startTimer() {
  if (timerInterval) clearInterval(timerInterval);

  // Initialize and resume audio context early (important for iOS)
  try {
    if (!audioContext) {
      audioContext = new AudioContext();
    }
    if (audioContext.state === "suspended") {
      await audioContext.resume();
    }
  } catch (error) {
    console.log("Failed to initialize audio context:", error);
  }

  isRunning.value = true;
  timerInterval = window.setInterval(() => {
    if (timeRemaining.value > 0) {
      timeRemaining.value--;
    } else {
      completeTimer();
    }
  }, 1000);
}

function pauseTimer() {
  isRunning.value = false;
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
}

function resumeTimer() {
  startTimer();
}

function togglePause() {
  if (isRunning.value) {
    pauseTimer();
  } else {
    resumeTimer();
  }
}

function completeTimer() {
  pauseTimer();
  isComplete.value = true;
  timeRemaining.value = 0;

  // Play alarm sound
  playAlarmSound();

  // Trigger haptic feedback
  triggerHapticFeedback();

  // Flash the screen
  flashScreen();
}

async function playAlarmSound() {
  // Try Web Audio API first (better quality)
  try {
    if (!audioContext) {
      audioContext = new AudioContext();
    }

    // Critical for iOS: resume context if suspended
    if (audioContext.state === "suspended") {
      await audioContext.resume();
    }

    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.value = 880; // A5 note
    oscillator.type = "square";

    // Louder volume for iOS
    gainNode.gain.setValueAtTime(0.5, audioContext.currentTime);

    // Create a more insistent beeping pattern: 5 beeps
    const beepDuration = 0.2;
    const beepGap = 0.15;

    for (let i = 0; i < 5; i++) {
      const startTime = audioContext.currentTime + i * (beepDuration + beepGap);
      gainNode.gain.setValueAtTime(0.5, startTime);
      gainNode.gain.setValueAtTime(0, startTime + beepDuration);
    }

    oscillator.start();
    oscillator.stop(
      audioContext.currentTime + 5 * (beepDuration + beepGap) + 0.1,
    );
  } catch (error) {
    console.log("Web Audio API failed:", error);
    // Fallback to HTMLAudioElement
    playFallbackSound();
  }
}

function playFallbackSound() {
  try {
    // Generate a beep sound using Web Audio API and play via audio element
    if (!audioContext) {
      audioContext = new AudioContext();
    }

    // Create a short beep buffer
    const duration = 0.2;
    const sampleRate = audioContext.sampleRate;
    const buffer = audioContext.createBuffer(
      1,
      duration * sampleRate,
      sampleRate,
    );
    const data = buffer.getChannelData(0);

    // Generate 880Hz sine wave
    for (let i = 0; i < buffer.length; i++) {
      data[i] = Math.sin((2 * Math.PI * 880 * i) / sampleRate) * 0.5;
    }

    // Play the beep 5 times with gaps
    let playCount = 0;
    const playBeep = () => {
      const source = audioContext!.createBufferSource();
      source.buffer = buffer;
      source.connect(audioContext!.destination);
      source.start();

      playCount++;
      if (playCount < 5) {
        setTimeout(playBeep, 350);
      }
    };
    playBeep();
  } catch (error) {
    console.log("Fallback audio failed:", error);
  }
}

function triggerHapticFeedback() {
  // Note: iOS Safari does not support the Vibration API
  // Haptic feedback on iOS relies on the audio playing through the device
  // and the system's haptic engine responding to certain audio patterns
  if ("vibrate" in navigator) {
    // Vibration pattern: vibrate, pause, vibrate, pause, vibrate
    const didVibrate = navigator.vibrate([200, 100, 200, 100, 200]);
    console.log("Vibration triggered:", didVibrate);
  } else {
    console.log("Vibration API not supported (expected on iOS)");
  }
}

function flashScreen() {
  isFlashing.value = true;
  let flashCount = 0;
  const maxFlashes = 10; // 5 inversions = 10 toggles

  flashInterval = window.setInterval(() => {
    flashInverted.value = !flashInverted.value;
    flashCount++;

    if (flashCount >= maxFlashes) {
      if (flashInterval) clearInterval(flashInterval);
      isFlashing.value = false;
      flashInverted.value = false;
    }
  }, 150);
}

function handleOk() {
  cleanup();
  emit("close");
}

function handleCancel() {
  cleanup();
  emit("close");
}

function handleExtend() {
  isComplete.value = false;
  timeRemaining.value = 30;
  startTimer();
}

async function acquireWakeLock() {
  if ("wakeLock" in navigator) {
    try {
      wakeLock = await navigator.wakeLock.request("screen");
    } catch {
      // Wake lock not available or denied, fail silently
    }
  }
}

function releaseWakeLock() {
  if (wakeLock) {
    wakeLock.release();
    wakeLock = null;
  }
}

function cleanup() {
  if (timerInterval) clearInterval(timerInterval);
  if (flashInterval) clearInterval(flashInterval);
  releaseWakeLock();
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  if (audioElement) {
    audioElement.pause();
    audioElement = null;
  }
}

// Handle visibility change to re-acquire wake lock
function handleVisibilityChange() {
  if (document.visibilityState === "visible" && isRunning.value) {
    acquireWakeLock();
  }
}

onMounted(() => {
  acquireWakeLock();
  startTimer();
  document.addEventListener("visibilitychange", handleVisibilityChange);
});

onUnmounted(() => {
  cleanup();
  document.removeEventListener("visibilitychange", handleVisibilityChange);
});

// Re-acquire wake lock if timer resumes
watch(isRunning, (running) => {
  if (running) {
    acquireWakeLock();
  }
});
</script>

<template>
  <div class="rest-timer-overlay" :class="{ inverted: flashInverted }">
    <div class="rest-timer-content">
      <h1 class="exercise-name">{{ exerciseName }}</h1>

      <div class="timer-display">
        {{ formattedTime }}
      </div>

      <div class="timer-controls controls field has-addons">
        <template v-if="!isComplete">
          <div class="control">
            <button class="button is-large control-button" @click="togglePause">
              {{ isRunning ? "Pause" : "Play" }}
            </button>
          </div>
          <div class="control">
            <button
              class="button is-large control-button"
              @click="handleCancel"
            >
              Cancel
            </button>
          </div>
        </template>
        <template v-else>
          <div class="control">
            <button class="button is-large control-button" @click="handleOk">
              OK
            </button>
          </div>
          <div class="control">
            <button
              class="button is-large control-button"
              @click="handleExtend"
            >
              +30
            </button>
          </div>
        </template>
      </div>

      <div class="timer-info">
        <p>Rest: {{ restSeconds }} seconds</p>
        <p>Sets so far: {{ setsDisplay || "—" }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rest-timer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  background-color: var(--color6);
  color: var(--color2);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  transition:
    background-color 0.1s,
    color 0.1s;
}

.rest-timer-overlay.inverted {
  background-color: var(--color2);
  color: var(--color6);
}

.rest-timer-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  width: 100%;
  max-width: 400px;
}

.exercise-name {
  font-size: 3rem;
  font-weight: 700;
  margin-bottom: 2rem;
  text-align: center;
  word-break: break-word;
}

.timer-display {
  font-size: 10rem;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  line-height: 1;
  margin-bottom: 2rem;
  color: var(--bulma-primary-invert);
}

.timer-controls {
  margin-bottom: 3rem;
}

.control-button {
  min-width: 120px;
  background-color: var(--color1);
  color: var(--color2);
}

.timer-info {
  font-size: 1.1rem;
  opacity: 0.8;
}

.timer-info p {
  margin-bottom: 0.5rem;
}
</style>
