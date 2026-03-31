import { ref } from "vue";
import { defineStore } from "pinia";
import type { Photo } from "@/types";
import { fetchWithPreload } from "@/lib/preload";

export const usePhotoblogStore = defineStore("photoblog", () => {
  const photos = ref<Photo[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  async function load() {
    if (photos.value.length > 0) return;
    loading.value = true;
    error.value = null;
    try {
      photos.value = await fetchWithPreload<Photo[]>("/data/photoblog.json");
    } catch (e) {
      error.value = e instanceof Error ? e.message : String(e);
    } finally {
      loading.value = false;
    }
  }

  function photoBySlug(slug: string): number {
    return photos.value.findIndex((p) => p.slug === slug);
  }

  return { photos, loading, error, load, photoBySlug };
});
