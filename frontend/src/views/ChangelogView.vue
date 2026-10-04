<script setup lang="ts">
import { onMounted } from "vue";
import { changelog, markChangesSeen } from "@/data/changelog";
import { parseDate } from "@/utils/format";
import AppBar from "@/components/ui/AppBar.vue";

function formatDate(iso: string): string {
  return parseDate(iso).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
}

onMounted(markChangesSeen);
</script>

<template>
  <div class="screen">
    <AppBar title="What's new" back="/" />
    <main class="screen-body">
      <section v-for="group in changelog" :key="group.date" class="group">
        <h2 class="eyebrow">{{ formatDate(group.date) }}</h2>
        <div class="list">
          <article v-for="change in group.changes" :key="change.title" class="change">
            <h3>{{ change.title }}</h3>
            <p v-if="change.description">{{ change.description }}</p>
          </article>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.group:first-child .eyebrow {
  margin-top: 4px;
}
.change {
  padding: 12px 0;
  border-bottom: 1px solid var(--rule);
}
.change:last-child {
  border-bottom: 0;
}
.change h3 {
  font-size: 17px;
  font-weight: 800;
  line-height: 1.25;
  text-transform: uppercase;
  font-stretch: 85%;
  letter-spacing: 0.02em;
}
.change p {
  margin-top: 4px;
  color: var(--muted);
}
</style>
