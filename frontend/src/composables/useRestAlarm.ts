import { ref, computed, watch, onUnmounted } from "vue";
import { useActiveSessionStore } from "@/stores/activeSession";
import { playAlarm, vibrate } from "@/utils/audio";

/**
 * Sound the alarm when rest hits zero, whichever screen of the live session
 * is showing (Lift with or without the rest screen, or Edit). Call from a
 * component's setup; `now` ticks while it's mounted.
 */
export function useRestAlarm(enabled: () => boolean = () => true) {
  const store = useActiveSessionStore();
  const now = ref(Date.now());
  const ticker = window.setInterval(() => (now.value = Date.now()), 250);
  onUnmounted(() => clearInterval(ticker));

  const isOver = computed(
    () => enabled() && store.rest !== null && store.rest.pausedRemaining === null && store.remaining(now.value) <= 0,
  );
  watch(isOver, (over) => {
    if (!over) return;
    playAlarm();
    vibrate();
  });

  return { now };
}
