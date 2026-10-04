<script setup lang="ts">
import { ref, computed, nextTick } from "vue";
import Icon from "./Icon.vue";

const props = withDefaults(
  defineProps<{
    modelValue: number | null;
    label: string;
    step?: number;
    min?: number;
    max?: number;
    unit?: string;
    /** Allow typing decimals (weights like 152.5). */
    decimal?: boolean;
    /** null is a real value (bodyweight); typing nothing sets it. */
    nullable?: boolean;
    size?: "lg" | "md";
    format?: (value: number | null) => string;
    parse?: (text: string) => number | null;
  }>(),
  { step: 1, min: 0, size: "lg", decimal: false, nullable: false },
);

const emit = defineEmits<{ "update:modelValue": [value: number | null] }>();

const editing = ref(false);
const draft = ref("");
const inputEl = ref<HTMLInputElement | null>(null);

const display = computed(() => {
  if (props.format) return props.format(props.modelValue);
  if (props.modelValue === null) return props.nullable ? "BW" : "–";
  return String(Math.round(props.modelValue * 100) / 100);
});

function clamp(value: number): number {
  let v = Math.max(props.min, value);
  if (props.max !== undefined) v = Math.min(props.max, v);
  return Math.round(v * 100) / 100;
}

function bump(direction: 1 | -1) {
  const current = props.modelValue;
  if (current === null) {
    if (direction > 0) emit("update:modelValue", clamp(props.step));
    return;
  }
  // Snap to the step grid first, so 152.5 + 5 lands on 155 rather than 157.5.
  const snapped =
    direction > 0
      ? Math.floor(current / props.step + 1e-9) * props.step + props.step
      : Math.ceil(current / props.step - 1e-9) * props.step - props.step;
  emit("update:modelValue", clamp(snapped));
}

async function startEdit() {
  draft.value = props.modelValue === null ? "" : display.value;
  editing.value = true;
  await nextTick();
  inputEl.value?.focus();
  inputEl.value?.select();
}

function defaultParse(text: string): number | null | undefined {
  const trimmed = text.trim().replace(",", ".");
  if (trimmed === "") return props.nullable ? null : undefined;
  const value = props.decimal ? Number.parseFloat(trimmed) : Number.parseInt(trimmed, 10);
  return Number.isFinite(value) ? clamp(value) : undefined;
}

function commit() {
  if (!editing.value) return;
  editing.value = false;
  const parsed = props.parse ? props.parse(draft.value) : defaultParse(draft.value);
  // undefined (or a null we can't accept) means "not a number": keep what was there
  if (parsed === undefined || (parsed === null && !props.nullable)) return;
  if (parsed !== props.modelValue) emit("update:modelValue", parsed);
}

const root = ref<HTMLElement | null>(null);

/** Enter moves on to the next stepper's number (weight → reps), like a form's Next key. */
async function onEnter() {
  const steppers = Array.from(document.querySelectorAll<HTMLElement>(".stepper"));
  const next = steppers[steppers.indexOf(root.value!) + 1];
  commit();
  await nextTick();
  const nextNum = next?.querySelector<HTMLButtonElement>("button.num");
  if (nextNum) nextNum.click();
  else inputEl.value?.blur();
}
</script>

<template>
  <div ref="root" class="stepper" :class="`is-${size}`">
    <button class="pm" type="button" :aria-label="`Less ${label}`" @click="bump(-1)">
      <Icon name="minus" />
    </button>
    <div class="value">
      <input
        v-if="editing"
        ref="inputEl"
        v-model="draft"
        class="num is-editing"
        :inputmode="parse ? 'text' : decimal ? 'decimal' : 'numeric'"
        enterkeyhint="next"
        :aria-label="label"
        @blur="commit"
        @keydown.enter.prevent="onEnter"
      />
      <button v-else class="num" type="button" :aria-label="`${label}: ${display}. Tap to type.`" @click="startEdit">
        {{ display }}
      </button>
      <span v-if="unit" class="unit">{{ unit }}</span>
    </div>
    <button class="pm" type="button" :aria-label="`More ${label}`" @click="bump(1)">
      <Icon name="plus" />
    </button>
  </div>
</template>

<style scoped>
.stepper {
  display: grid;
  align-items: center;
  gap: 8px;
}
.pm {
  display: grid;
  place-items: center;
  background: var(--card);
  border: 1.5px solid var(--rule-strong);
  border-radius: var(--r);
  color: var(--k);
}
.pm:active {
  background: var(--chip);
}
.num {
  font-weight: 800;
  line-height: 1;
  color: var(--k);
  background: var(--card);
  border: 2px solid var(--k);
  border-radius: var(--r);
  text-align: center;
  white-space: nowrap;
}
.num.is-editing {
  background: var(--y);
  outline: none;
  min-width: 0;
}

/* Track dial: big centered number with the unit under it */
.is-lg {
  grid-template-columns: 56px 1fr 56px;
}
.is-lg .pm {
  height: 56px;
}
.is-lg .value {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.is-lg .num {
  font-size: 48px;
  letter-spacing: -0.03em;
  min-width: 120px;
  width: 140px;
  padding: 8px 10px 6px;
}
.is-lg .unit {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  font-weight: 700;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.16em;
  font-stretch: 85%;
}

/* Plan editor row: − number unit + */
.is-md {
  grid-template-columns: 48px 1fr 48px;
}
.is-md .pm {
  height: 48px;
}
.is-md .value {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 6px;
}
.is-md .num {
  font-size: 30px;
  min-width: 92px;
  width: 104px;
  padding: 6px 8px 4px;
  border-width: 1.5px;
}
.is-md .unit {
  width: 34px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
}
</style>
