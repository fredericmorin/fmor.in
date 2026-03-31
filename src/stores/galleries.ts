import { ref } from "vue";
import { defineStore } from "pinia";
import type { GalleryMeta, Photo } from "@/types";
import { fetchWithPreload } from "@/lib/preload";

export const useGalleriesStore = defineStore("galleries", () => {
  const index = ref<GalleryMeta[]>([]);
  const indexLoading = ref(false);
  const indexError = ref<string | null>(null);

  const byName = ref<Map<string, Photo[]>>(new Map());
  const galleryLoading = ref<Map<string, boolean>>(new Map());
  const galleryError = ref<Map<string, string>>(new Map());

  async function loadIndex() {
    if (index.value.length > 0) return;
    indexLoading.value = true;
    indexError.value = null;
    try {
      index.value = await fetchWithPreload<GalleryMeta[]>("/data/gallery-index.json");
    } catch (e) {
      indexError.value = e instanceof Error ? e.message : String(e);
    } finally {
      indexLoading.value = false;
    }
  }

  async function loadGallery(name: string) {
    if (byName.value.has(name)) return;
    galleryLoading.value.set(name, true);
    galleryError.value.delete(name);
    try {
      byName.value.set(
        name,
        await fetchWithPreload<Photo[]>(`/data/galleries/${name}.json`),
      );
    } catch (e) {
      galleryError.value.set(name, e instanceof Error ? e.message : String(e));
    } finally {
      galleryLoading.value.set(name, false);
    }
  }

  function photosFor(name: string): Photo[] {
    return byName.value.get(name) ?? [];
  }

  function photoBySlug(name: string, slug: string): number {
    return photosFor(name).findIndex((p) => p.slug === slug);
  }

  function isLoading(name: string): boolean {
    return galleryLoading.value.get(name) ?? false;
  }

  return {
    index,
    indexLoading,
    indexError,
    loadIndex,
    loadGallery,
    photosFor,
    photoBySlug,
    isLoading,
    galleryError,
  };
});
