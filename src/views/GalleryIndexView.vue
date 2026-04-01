<script setup lang="ts">
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { useGalleriesStore } from "@/stores/galleries";
import GalleryCard from "@/components/GalleryCard.vue";

const router = useRouter();
const store = useGalleriesStore();

onMounted(() => {
  store.loadIndex();
  document.title = "fmor.in — Galleries";
});

function openGallery(slug: string) {
  router.push(`/gallery/${slug}/`);
}
</script>

<template>
  <div class="pt-10">
    <div
      v-if="store.indexLoading"
      class="flex items-center justify-center h-64 text-neutral-600 text-sm"
    >
      Loading…
    </div>
    <div
      v-else-if="store.indexError"
      class="flex items-center justify-center h-64 text-red-500 text-sm"
    >
      {{ store.indexError }}
    </div>
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-0.5 p-0.5">
      <GalleryCard
        v-for="gallery in store.index"
        :key="gallery.slug"
        :gallery="gallery"
        @select="openGallery(gallery.slug)"
      />
    </div>
  </div>
</template>
