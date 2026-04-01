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

function thumbSrcset(photo: Photo, format: "avif" | "jpg") {
  return photo.sizes.map((s) => `${photo.base}-${s}.${format} ${s}w`).join(", ");
}

function thumbFallback(photo: Photo) {
  return `${photo.base}-${photo.sizes[0]}.jpg`;
}
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
        <picture class="block w-full h-full">
          <source
            v-if="avifSupported"
            type="image/avif"
            :srcset="thumbSrcset(photo, 'avif')"
            sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw"
          />
          <source
            type="image/jpeg"
            :srcset="thumbSrcset(photo, 'jpg')"
            sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw"
          />
          <img
            :src="thumbFallback(photo)"
            :alt="photo.alt"
            class="w-full h-full object-cover transition-opacity duration-200"
            :class="i === activeIndex ? 'ring-2 ring-inset ring-white' : ''"
            loading="lazy"
          />
        </picture>
      </button>
    </div>
  </div>
</template>
