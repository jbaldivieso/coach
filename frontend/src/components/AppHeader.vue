<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { useAuthStore } from "@/stores/auth";
import { useRouter } from "vue-router";

const authStore = useAuthStore();
const router = useRouter();
const menuOpen = ref(false);

function toggleMenu() {
  menuOpen.value = !menuOpen.value;
}

function closeMenu() {
  menuOpen.value = false;
}

function handleClickOutside(event: MouseEvent) {
  const target = event.target as HTMLElement;
  if (!target.closest('.dropdown')) {
    closeMenu();
  }
}

async function handleLogout() {
  closeMenu();
  const success = await authStore.logout();
  if (success) {
    router.push({ name: "login" });
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<template>
  <nav class="navbar" role="navigation" aria-label="main navigation">
    <div class="container">
      <div class="navbar-brand">
        <router-link class="navbar-item has-text-weight-bold" to="/">
          Coach
        </router-link>
      </div>

      <div class="navbar-end" v-if="authStore.isAuthenticated">
        <div class="navbar-item">
          <div class="dropdown is-right" :class="{ 'is-active': menuOpen }">
            <div class="dropdown-trigger">
              <button
                class="button is-ghost hamburger-button"
                @click="toggleMenu"
                aria-haspopup="true"
                aria-controls="dropdown-menu"
                :class="{ 'is-open': menuOpen }"
              >
                <span class="hamburger-icon">
                  <span class="bar"></span>
                  <span class="bar"></span>
                  <span class="bar"></span>
                </span>
              </button>
            </div>
            <div class="dropdown-menu" id="dropdown-menu" role="menu">
              <div class="dropdown-content">
                <router-link
                  class="dropdown-item"
                  to="/changelog"
                  @click="closeMenu"
                >
                  App updates 🎁
                </router-link>
                <hr class="dropdown-divider" />
                <a
                  class="dropdown-item"
                  @click="handleLogout"
                >
                  Log out
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.dropdown-menu {
  min-width: 12rem;
}

.button.is-ghost {
  background: none;
  border: none;
}

.button.is-ghost:hover {
  background-color: var(--bulma-navbar-item-hover-background-color);
}

.hamburger-button {
  padding: 0.5rem;
  cursor: pointer;
}

.hamburger-icon {
  width: 24px;
  height: 18px;
  display: block;
  position: relative;
}

.hamburger-icon .bar {
  width: 100%;
  height: 2px;
  background-color: currentColor;
  transition: all 0.3s ease-in-out;
  position: absolute;
  left: 0;
  transform-origin: center center;
}

.hamburger-icon .bar:nth-child(1) {
  top: 0;
}

.hamburger-icon .bar:nth-child(2) {
  top: 8px;
}

.hamburger-icon .bar:nth-child(3) {
  top: 16px;
}

/* Transform to X when open */
.hamburger-button.is-open .hamburger-icon .bar:nth-child(1) {
  top: 8px;
  transform: rotate(45deg);
}

.hamburger-button.is-open .hamburger-icon .bar:nth-child(2) {
  opacity: 0;
}

.hamburger-button.is-open .hamburger-icon .bar:nth-child(3) {
  top: 8px;
  transform: rotate(-45deg);
}
</style>
