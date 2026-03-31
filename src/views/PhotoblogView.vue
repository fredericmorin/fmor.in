<script setup lang="ts">
import { computed, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { usePhotoblogStore } from "@/stores/photoblog";
import PhotoSlideshow from "@/components/PhotoSlideshow.vue";
import PhotoGrid from "@/components/PhotoGrid.vue";

const route = useRoute();
const router = useRouter();
const store = usePhotoblogStore();

onMounted(() => store.load());

// Derive view state from URL hash:
//   no hash or #grid → grid
//   #<slug>          → slideshow at that photo
const currentIndex = computed<number | null>(() => {
  const hash = route.hash.replace("#", "");
  if (!hash || hash === "grid") return null;
  const idx = store.photoBySlug(hash);
  return idx !== -1 ? idx : null;
});

const showGrid = computed(() => currentIndex.value === null);

function openPhoto(i: number) {
  const slug = store.photos[i]?.slug;
  if (slug) router.push({ hash: `#${slug}` });
}

function prevPhoto() {
  const i = currentIndex.value;
  if (i !== null && i > 0) {
    router.replace({ hash: `#${store.photos[i - 1].slug}` });
  }
}

function nextPhoto() {
  const i = currentIndex.value;
  if (i !== null && i < store.photos.length - 1) {
    router.replace({ hash: `#${store.photos[i + 1].slug}` });
  }
}

function toGrid() {
  router.push({ path: "/photoblog/", hash: "" });
}

// Update page title
watch(
  currentIndex,
  (idx) => {
    if (idx === null) {
      document.title = "fmor.in — Photoblog";
    } else {
      const photo = store.photos[idx];
      document.title = photo ? `fmor.in — ${photo.alt || photo.slug}` : "fmor.in";
    }
  },
  { immediate: true },
);
</script>

<template>
  <div class="pt-10">
    <div v-if="store.loading" class="flex items-center justify-center h-64 text-neutral-600 text-sm">
      Loading…
    </div>
    <div v-else-if="store.error" class="flex items-center justify-center h-64 text-red-500 text-sm">
      {{ store.error }}
    </div>
    <template v-else>
      <PhotoGrid
        v-if="showGrid"
        :photos="store.photos"
        @select="openPhoto"
      />
      <PhotoSlideshow
        v-else
        :photos="store.photos"
        :index="currentIndex!"
        @prev="prevPhoto"
        @next="nextPhoto"
        @show-grid="toGrid"
      />
    </template>
  </div>
</template>
