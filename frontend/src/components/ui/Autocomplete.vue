<script setup lang="ts">
import { ref } from "vue";
import type { TitleSuggestion } from "@/types/lifting";
import { formatShortDate } from "@/utils/format";

const props = withDefaults(
  defineProps<{
    modelValue: string;
    fetch: (query: string) => Promise<TitleSuggestion[]>;
    label: string;
    placeholder?: string;
    /** Show suggestions on focus even before typing (recent names). */
    suggestOnFocus?: boolean;
    inputClass?: string;
    invalid?: boolean;
  }>(),
  { placeholder: "", suggestOnFocus: false, inputClass: "", invalid: false },
);

const emit = defineEmits<{
  "update:modelValue": [value: string];
  pick: [suggestion: TitleSuggestion];
  /** Focus left the field; value is what was typed (or picked). */
  commit: [value: string];
}>();

const input = ref<HTMLInputElement | null>(null);
const suggestions = ref<TitleSuggestion[]>([]);
const open = ref(false);
const highlight = ref(-1);
let debounce: ReturnType<typeof setTimeout> | null = null;
let requestId = 0;

async function refresh(query: string) {
  const id = ++requestId;
  const results = await props.fetch(query);
  if (id !== requestId) return;
  // An exact match alone is no help
  suggestions.value = results.filter((s) => s.title !== query.trim() || results.length > 1);
  highlight.value = -1;
}

function onInput(event: Event) {
  const value = (event.target as HTMLInputElement).value;
  emit("update:modelValue", value);
  open.value = true;
  if (debounce) clearTimeout(debounce);
  debounce = setTimeout(() => refresh(value), 180);
}

function onFocus() {
  open.value = true;
  if (props.suggestOnFocus || props.modelValue.trim()) refresh(props.modelValue);
}

// Set while a pick blurs the input: the parent has the picked value, but
// props.modelValue still holds what was typed until it re-renders.
let picking = false;

function onBlur() {
  open.value = false;
  if (picking) {
    picking = false;
    return; // pick already reported the value
  }
  emit("commit", props.modelValue.trim());
}

function pick(suggestion: TitleSuggestion) {
  if (debounce) clearTimeout(debounce);
  requestId++; // drop any search still in flight
  emit("update:modelValue", suggestion.title);
  emit("pick", suggestion);
  suggestions.value = [];
  open.value = false;
  picking = document.activeElement === input.value;
  input.value?.blur();
  picking = false;
}

function onKeydown(event: KeyboardEvent) {
  const count = suggestions.value.length;
  if (event.key === "Escape") {
    open.value = false;
    return;
  }
  if (!open.value || count === 0) {
    if (event.key === "Enter") input.value?.blur();
    return;
  }
  if (event.key === "ArrowDown") {
    event.preventDefault();
    highlight.value = (highlight.value + 1) % count;
  } else if (event.key === "ArrowUp") {
    event.preventDefault();
    highlight.value = highlight.value <= 0 ? count - 1 : highlight.value - 1;
  } else if (event.key === "Enter") {
    event.preventDefault();
    const chosen = suggestions.value[highlight.value];
    if (chosen) pick(chosen);
    else input.value?.blur();
  }
}

defineExpose({ focus: () => input.value?.focus() });
</script>

<template>
  <div class="ac">
    <input
      ref="input"
      :value="modelValue"
      :class="inputClass"
      :placeholder="placeholder"
      :aria-label="label"
      :aria-invalid="invalid || undefined"
      role="combobox"
      :aria-expanded="open && suggestions.length > 0"
      aria-autocomplete="list"
      autocomplete="off"
      autocapitalize="words"
      enterkeyhint="done"
      @input="onInput"
      @focus="onFocus"
      @blur="onBlur"
      @keydown="onKeydown"
    />
    <ul v-if="open && suggestions.length" class="ac-list" role="listbox">
      <li
        v-for="(s, i) in suggestions"
        :key="s.title"
        role="option"
        :aria-selected="i === highlight"
        class="ac-item"
        :class="{ 'is-active': i === highlight }"
        @mousedown.prevent="pick(s)"
      >
        <b>{{ s.title }}</b>
        <span>{{ s.last_date ? `${formatShortDate(s.last_date)} · ` : "" }}{{ s.count }}×</span>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.ac {
  position: relative;
  flex: 1;
  min-width: 0;
}
.ac input {
  width: 100%;
}
.ac-list {
  list-style: none;
  margin: 6px 0 0;
  padding: 0 10px;
  background: var(--card);
  border: 2px solid var(--k);
  border-radius: var(--r);
  position: absolute;
  left: 0;
  right: 0;
  z-index: 30;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.18);
  max-height: 290px;
  overflow-y: auto;
}
.ac-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  min-height: 46px;
  padding: 8px 2px;
  border-bottom: 1px solid var(--rule);
  font-size: 15px;
  cursor: pointer;
  text-transform: none;
  font-stretch: 100%;
  letter-spacing: 0;
  font-weight: 400;
  color: var(--k);
}
.ac-item:last-child {
  border-bottom: 0;
}
.ac-item span {
  color: var(--muted);
  font-size: 12.5px;
  white-space: nowrap;
}
.ac-item.is-active {
  background: var(--chip);
}
</style>
