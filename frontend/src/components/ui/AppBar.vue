<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { RouterLink, useRouter, type RouteLocationRaw } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { changelog, hasUnreadChanges } from "@/data/changelog";
import Icon from "./Icon.vue";

const props = defineProps<{
  title?: string;
  small?: boolean;
  /** Show a back arrow. A route is the fallback when there's no history to go back to; a function takes over entirely. */
  back?: RouteLocationRaw | (() => void);
  /** Show an X instead of a back arrow, with the same semantics. */
  close?: RouteLocationRaw | (() => void);
}>();

const router = useRouter();
const authStore = useAuthStore();

const menuOpen = ref(false);
const unread = ref(hasUnreadChanges());
const latestTeaser = computed(() =>
  (changelog[0]?.changes ?? []).map((c) => c.title).slice(0, 2).join(", "),
);

const nav = computed(() => props.close ?? props.back);

function navigate() {
  const target = nav.value;
  if (typeof target === "function") {
    target();
  } else if (window.history.state?.back) {
    router.back();
  } else {
    router.push(target ?? "/");
  }
}

function toggleMenu() {
  menuOpen.value = !menuOpen.value;
  if (menuOpen.value) unread.value = hasUnreadChanges();
}

async function logout() {
  menuOpen.value = false;
  if (await authStore.logout()) {
    router.push({ name: "login" });
  }
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === "Escape") menuOpen.value = false;
}

onMounted(() => document.addEventListener("keydown", onKeydown));
onUnmounted(() => document.removeEventListener("keydown", onKeydown));
</script>

<template>
  <header class="appbar">
    <div class="appbar-inner">
      <button v-if="nav" class="appbar-icon" :aria-label="close ? 'Close' : 'Back'" @click="navigate">
        <Icon :name="close ? 'x' : 'left'" />
      </button>
      <slot name="title">
        <h1 class="appbar-title" :class="{ 'is-small': small }">{{ title }}</h1>
      </slot>
      <slot name="actions" />
      <div class="appbar-menu">
        <button
          class="appbar-icon"
          :class="{ 'is-open': menuOpen }"
          aria-label="Menu"
          aria-haspopup="menu"
          :aria-expanded="menuOpen"
          @click="toggleMenu"
        >
          <Icon name="more" />
          <i v-if="unread" class="unread-dot" aria-label="Unread updates" />
        </button>
        <div v-if="menuOpen" class="menu-sheet" role="menu">
          <RouterLink to="/changelog" class="menu-item" role="menuitem" @click="menuOpen = false">
            <span>
              <b>What's new</b>
              <small v-if="latestTeaser">{{ latestTeaser }}</small>
            </span>
            <i v-if="unread" class="unread-dot is-static" />
          </RouterLink>
          <button class="menu-item" role="menuitem" @click="logout">
            <span>
              <b>Log out</b>
              <small v-if="authStore.user">{{ authStore.user.username }}</small>
            </span>
          </button>
        </div>
      </div>
    </div>
  </header>
  <div v-if="menuOpen" class="menu-dim" @click="menuOpen = false" />
</template>

<style scoped>
.appbar {
  position: sticky;
  top: 0;
  z-index: 20;
  background: var(--y);
  color: var(--k);
  padding-top: env(safe-area-inset-top);
}
.appbar-inner {
  display: flex;
  align-items: center;
  gap: 4px;
  min-height: 56px;
  padding: 0 max(8px, calc((100% - var(--content)) / 2 - 8px)) 0 max(var(--gutter), calc((100% - var(--content)) / 2));
}
.appbar-inner:has(> .appbar-icon:first-child) {
  padding-left: max(6px, calc((100% - var(--content)) / 2 - 10px));
}
.appbar-title {
  flex: 1;
  min-width: 0;
  font-size: 28px;
  font-weight: 800;
  line-height: 1.1;
  text-transform: uppercase;
  font-stretch: 80%;
  letter-spacing: 0.03em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.appbar-title.is-small {
  font-size: 19px;
}
.appbar-icon {
  position: relative;
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: var(--r);
  color: var(--k);
  flex: 0 0 auto;
}
.appbar-icon.is-open {
  background: var(--k);
  color: var(--y);
}
.appbar-menu {
  position: relative;
}
.unread-dot {
  position: absolute;
  top: 9px;
  right: 9px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--alert);
  box-shadow: 0 0 0 2px var(--y);
}
.appbar-icon.is-open .unread-dot {
  box-shadow: 0 0 0 2px var(--k);
}
.unread-dot.is-static {
  position: static;
  box-shadow: none;
  flex: 0 0 auto;
}
.menu-sheet {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  width: 240px;
  background: var(--card);
  border: 2px solid var(--k);
  border-radius: var(--r-lg);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.25);
  z-index: 2;
  overflow: hidden;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 12px 14px;
  border-bottom: 1px solid var(--rule);
  text-align: left;
}
.menu-item:last-child {
  border-bottom: 0;
}
.menu-item span {
  flex: 1;
}
.menu-item b {
  display: block;
}
.menu-item small {
  display: block;
  color: var(--muted);
  font-size: 12.5px;
}
.menu-dim {
  position: fixed;
  inset: 0;
  z-index: 15;
  background: var(--dim);
}
</style>
