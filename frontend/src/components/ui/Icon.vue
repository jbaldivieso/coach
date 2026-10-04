<script setup lang="ts">
// Stroke icons from the Safety signal mock; they inherit currentColor.
const paths = {
  search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  minus: '<path d="M5 12h14"/>',
  check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
  left: '<path d="m15 5-7 7 7 7"/>',
  right: '<path d="m9 5 7 7-7 7"/>',
  down: '<path d="m6 9 6 6 6-6"/>',
  up: '<path d="m6 15 6-6 6 6"/>',
  grip: '<path d="M9 6h.01M9 12h.01M9 18h.01M15 6h.01M15 12h.01M15 18h.01"/>',
  more: '<path d="M5 12h.01M12 12h.01M19 12h.01"/>',
  clock: '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l2.5 2"/>',
  x: '<path d="M6 6l12 12M18 6 6 18"/>',
  link: '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
  pencil: '<path d="M4 20h4L19 9l-4-4L4 16z"/>',
  copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/>',
  play: '<path d="M7 5v14l11-7z"/>',
  undo: '<path d="M9 14 4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 0 12h-3"/>',
} as const;

export type IconName = keyof typeof paths;

withDefaults(defineProps<{ name: IconName; size?: "sm" | "md" }>(), { size: "md" });
</script>

<template>
  <svg
    class="icon-svg"
    :class="`icon-${size}`"
    viewBox="0 0 24 24"
    aria-hidden="true"
    focusable="false"
    v-html="paths[name]"
  />
</template>

<style scoped>
.icon-svg {
  flex: 0 0 auto;
  fill: none;
  stroke: currentColor;
  stroke-width: 2;
  stroke-linecap: round;
  stroke-linejoin: round;
}
.icon-md {
  width: 20px;
  height: 20px;
}
.icon-sm {
  width: 16px;
  height: 16px;
}
</style>
