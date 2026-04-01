<script setup lang="ts">
import { ref, onMounted } from "vue";
import type { Photo } from "@/types";
import { useAvif } from "@/composables/useAvif";

const props = defineProps<{
  photos: Photo[];
  activeIndex?: number;
  /** Optional header slot content (e.g. back link + title for gallery pages) */
  showHeader?: boolean;
}>();

const emit = defineEmits<{
  select: [index: number];
}>();

const avifSupported = ref(false);
const activeRef = ref<HTMLElement | null>(null);

onMounted(async () => {
  avifSupported.value = await useAvif();
  // Scroll active thumbnail into view when returning from slideshow
  if (activeRef.value) {
    activeRef.value.scrollIntoView({ block: "center", behavior: "instant" });
  }
});

</script>

<template>
  <div>
    <slot name="header" />
    <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-0.5 p-0.5">
      <button
        v-for="(photo, i) in photos"
        :key="photo.slug"
        :ref="
          (el) => {
            if (i === activeIndex) activeRef = el as HTMLElement;
          }
        "
        class="relative aspect-square overflow-hidden bg-neutral-900 focus:outline-none focus-visible:ring-2 focus-visible:ring-white"
        :aria-label="photo.alt || `Photo ${i + 1}`"
        :aria-current="i === activeIndex ? 'true' : undefined"
        @click="emit('select', i)"
      >
        <img
          :src="`${photo.base}-${photo.sizes[0]}.${avifSupported ? 'avif' : 'jpg'}`"
          :alt="photo.alt"
          class="w-full h-full object-cover transition-opacity duration-200"
          :class="i === activeIndex ? 'ring-2 ring-inset ring-white' : ''"
          loading="lazy"
        />
      </button>
    </div>
  </div>
</template>
