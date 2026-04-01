<script setup lang="ts">
import { computed, watch, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useGalleriesStore } from "@/stores/galleries";
import PhotoSlideshow from "@/components/PhotoSlideshow.vue";
import PhotoGrid from "@/components/PhotoGrid.vue";

const route = useRoute();
const router = useRouter();
const store = useGalleriesStore();

const name = computed(() => route.params.name as string);
const photos = computed(() => store.photosFor(name.value));
const loading = computed(() => store.isLoading(name.value));
const error = computed(() => store.galleryError.get(name.value));

const displayName = (n: string) => n.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

onMounted(() => store.loadGallery(name.value));
watch(name, (n) => store.loadGallery(n));

const currentIndex = computed<number | null>(() => {
  const hash = route.hash.replace("#", "");
  if (!hash || hash === "grid") return null;
  const idx = store.photoBySlug(name.value, hash);
  return idx !== -1 ? idx : null;
});

const showGrid = computed(() => currentIndex.value === null);

function openPhoto(i: number) {
  const slug = photos.value[i]?.slug;
  if (slug) router.push({ hash: `#${slug}` });
}

function prevPhoto() {
  const i = currentIndex.value;
  if (i !== null && i > 0) {
    router.replace({ hash: `#${photos.value[i - 1].slug}` });
  }
}

function nextPhoto() {
  const i = currentIndex.value;
  if (i !== null && i < photos.value.length - 1) {
    router.replace({ hash: `#${photos.value[i + 1].slug}` });
  }
}

function toGrid() {
  router.push({ path: `/gallery/${name.value}/`, hash: "" });
}

watch(
  [currentIndex, name],
  ([idx]) => {
    const n = name.value;
    if (idx === null) {
      document.title = `fmor.in — ${displayName(n)}`;
    } else {
      const photo = photos.value[idx];
      document.title = photo
        ? `fmor.in — ${photo.alt || photo.slug}`
        : `fmor.in — ${displayName(n)}`;
    }
  },
  { immediate: true },
);
</script>

<template>
  <div class="pt-10">
    <div v-if="loading" class="flex items-center justify-center h-64 text-neutral-600 text-sm">
      Loading…
    </div>
    <div v-else-if="error" class="flex items-center justify-center h-64 text-red-500 text-sm">
      {{ error }}
    </div>
    <template v-else>
      <PhotoGrid v-if="showGrid" :photos="photos" @select="openPhoto" />
      <PhotoSlideshow
        v-else
        :photos="photos"
        :index="currentIndex!"
        @prev="prevPhoto"
        @next="nextPhoto"
        @show-grid="toGrid"
      />
    </template>
  </div>
</template>
