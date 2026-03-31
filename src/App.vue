<script setup lang="ts">
import { useRoute } from "vue-router";
import AppHeader from "@/components/AppHeader.vue";

const route = useRoute();
</script>

<template>
  <div class="min-h-screen bg-neutral-950 text-neutral-300">
    <AppHeader />
    <RouterView v-slot="{ Component }">
      <Transition name="fade" mode="out-in">
        <component :is="Component" :key="route.path" />
      </Transition>
    </RouterView>
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 150ms ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
