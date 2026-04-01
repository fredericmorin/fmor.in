<script setup lang="ts">
import { ref, onMounted } from "vue";
import type { GalleryMeta } from "@/types";
import { useAvif } from "@/composables/useAvif";

const props = defineProps<{
  gallery: GalleryMeta;
}>();

const emit = defineEmits<{
  select: [];
}>();

const avifSupported = ref(false);

onMounted(async () => {
  avifSupported.value = await useAvif();
});

function srcset(format: "avif" | "jpg") {
  return props.gallery.sizes
    .map((s) => `${props.gallery.cover_base}-${s}.${format} ${s}w`)
    .join(", ");
}

function fallbackSrc() {
  const sizes = props.gallery.sizes;
  const size = sizes.includes(400) ? 400 : sizes[0];
  return `${props.gallery.cover_base}-${size}.jpg`;
}

const displayName = (name: string) =>
  name.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
</script>

<template>
  <button
    class="relative aspect-[4/3] overflow-hidden bg-neutral-900 group focus:outline-none focus-visible:ring-2 focus-visible:ring-white w-full"
    :aria-label="`Gallery: ${gallery.name}`"
    @click="emit('select')"
  >
    <picture class="block w-full h-full">
      <source
        v-if="avifSupported"
        type="image/avif"
        :srcset="srcset('avif')"
        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
      />
      <source
        type="image/jpeg"
        :srcset="srcset('jpg')"
        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
      />
      <img
        :src="fallbackSrc()"
        :alt="gallery.name"
        class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
        loading="lazy"
      />
    </picture>
    <!-- Overlay -->
    <div class="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent" />
    <div class="absolute bottom-0 left-0 right-0 px-4 py-3 text-left">
      <p class="text-white text-sm font-medium leading-tight">{{ displayName(gallery.name) }}</p>
      <p class="text-neutral-400 text-xs mt-0.5">{{ gallery.count }} photos</p>
    </div>
  </button>
</template>
