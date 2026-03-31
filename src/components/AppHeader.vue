<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

const photoblogActive = computed(() => route.path.startsWith("/photoblog"));
const galleryActive = computed(() => route.path.startsWith("/gallery"));

function navigate(path: string) {
  router.push(path);
}
</script>

<template>
  <header class="fixed top-0 left-0 right-0 z-50 h-10 flex items-center justify-between px-4 bg-neutral-950 border-b border-neutral-800">
    <a
      href="/photoblog/"
      class="text-sm font-medium tracking-widest text-neutral-300 hover:text-white transition-colors"
      @click.prevent="navigate('/photoblog/')"
    >
      fmor.in
    </a>
    <nav class="flex gap-6">
      <a
        href="/photoblog/"
        class="text-sm transition-colors"
        :class="photoblogActive ? 'text-white border-b border-white pb-0.5' : 'text-neutral-500 hover:text-neutral-300'"
        @click.prevent="navigate('/photoblog/')"
      >
        Photoblog
      </a>
      <a
        href="/gallery/"
        class="text-sm transition-colors"
        :class="galleryActive ? 'text-white border-b border-white pb-0.5' : 'text-neutral-500 hover:text-neutral-300'"
        @click.prevent="navigate('/gallery/')"
      >
        Gallery
      </a>
    </nav>
  </header>
</template>
