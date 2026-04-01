<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import type { Photo } from "@/types";
import { useAvif } from "@/composables/useAvif";
import ExifBar from "@/components/ExifBar.vue";

const props = defineProps<{
  photos: Photo[];
  index: number;
}>();

const emit = defineEmits<{
  prev: [];
  next: [];
  showGrid: [];
}>();

const avifSupported = ref(false);

onMounted(async () => {
  avifSupported.value = await useAvif();
});

const photo = computed(() => props.photos[props.index]);

const total = computed(() => props.photos.length);
const canPrev = computed(() => props.index > 0);
const canNext = computed(() => props.index < props.photos.length - 1);

function ext(avif: boolean) {
  return avif ? "avif" : "jpg";
}

function srcset(photo: Photo, format: "avif" | "jpg") {
  return photo.sizes.map((s) => `${photo.base}-${s}.${format} ${s}w`).join(", ");
}

function fallbackSrc(photo: Photo) {
  const size = photo.sizes.includes(1920) ? 1920 : photo.sizes[Math.floor(photo.sizes.length / 2)];
  return `${photo.base}-${size}.jpg`;
}

const isLoading = ref(true);

watch(
  () => props.index,
  () => {
    isLoading.value = true;
  },
);

function onFullResLoad() {
  isLoading.value = false;
}

// Preload adjacent photos
watch(
  () => props.index,
  (idx) => {
    useAvif().then((avif) => {
      const fmtExt = ext(avif);
      const pickSize = (p: Photo) => {
        const target = window.innerWidth * (window.devicePixelRatio || 1);
        return p.sizes.find((s) => s >= target) ?? p.sizes[p.sizes.length - 1];
      };
      for (const offset of [-1, 1]) {
        const neighbor = props.photos[idx + offset];
        if (neighbor) {
          const img = new Image();
          img.src = `${neighbor.base}-${pickSize(neighbor)}.${fmtExt}`;
        }
      }
    });
  },
  { immediate: true },
);

// Keyboard navigation
function onKeydown(e: KeyboardEvent) {
  if (e.key === "ArrowLeft" && canPrev.value) emit("prev");
  else if (e.key === "ArrowRight" && canNext.value) emit("next");
}

onMounted(() => document.addEventListener("keydown", onKeydown));
onUnmounted(() => document.removeEventListener("keydown", onKeydown));
</script>

<template>
  <div class="flex flex-col" style="height: calc(100vh - 40px)">
    <!-- Photo area -->
    <div class="relative flex-1 flex items-center justify-center bg-neutral-950 overflow-hidden">
      <!-- Grid toggle -->
      <button
        class="absolute top-3 left-3 z-10 text-xs text-neutral-500 hover:text-neutral-300 transition-colors px-2 py-1 rounded"
        @click="emit('showGrid')"
      >
        Grid
      </button>

      <!-- Counter -->
      <div class="absolute top-3 right-3 z-10 text-xs text-neutral-600 tabular-nums">
        {{ index + 1 }} / {{ total }}
      </div>

      <!-- Blurred placeholder (uses grid thumbnail sizes → cache hit) -->
      <picture v-if="photo" class="absolute inset-0 w-full h-full">
        <source
          v-if="avifSupported"
          type="image/avif"
          :srcset="srcset(photo, 'avif')"
          sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw"
        />
        <source
          type="image/jpeg"
          :srcset="srcset(photo, 'jpg')"
          sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw"
        />
        <img
          :src="`${photo.base}-${photo.sizes[0]}.jpg`"
          :alt="photo.alt"
          class="w-full h-full object-contain"
          style="filter: blur(12px); transform: scale(1.05)"
          draggable="false"
        />
      </picture>

      <!-- Image -->
      <picture v-if="photo" class="max-w-full max-h-full">
        <source
          v-if="avifSupported"
          type="image/avif"
          :srcset="srcset(photo, 'avif')"
          sizes="100vw"
        />
        <source type="image/jpeg" :srcset="srcset(photo, 'jpg')" sizes="100vw" />
        <img
          :src="fallbackSrc(photo)"
          :alt="photo.alt"
          class="max-w-full max-h-full object-contain select-none"
          style="max-height: calc(100vh - 40px - 40px)"
          draggable="false"
        />
      </picture>

      <!-- Prev zone -->
      <button
        v-if="canPrev"
        class="absolute left-0 top-0 bottom-0 w-1/5 flex items-center justify-start pl-3 opacity-0 hover:opacity-100 transition-opacity group"
        aria-label="Previous photo"
        @click="emit('prev')"
      >
        <span class="text-3xl text-white drop-shadow-lg group-hover:scale-110 transition-transform"
          >‹</span
        >
      </button>

      <!-- Next zone -->
      <button
        v-if="canNext"
        class="absolute right-0 top-0 bottom-0 w-1/5 flex items-center justify-end pr-3 opacity-0 hover:opacity-100 transition-opacity group"
        aria-label="Next photo"
        @click="emit('next')"
      >
        <span class="text-3xl text-white drop-shadow-lg group-hover:scale-110 transition-transform"
          >›</span
        >
      </button>
    </div>

    <!-- EXIF bar -->
    <ExifBar v-if="photo" :exif="photo.exif" :date="photo.date" />
  </div>
</template>
