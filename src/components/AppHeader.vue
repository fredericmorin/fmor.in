<script setup lang="ts">
import { computed, onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { usePhotoblogStore } from "@/stores/photoblog";
import { useGalleriesStore } from "@/stores/galleries";

const route = useRoute();
const router = useRouter();
const photoblogStore = usePhotoblogStore();
const galleriesStore = useGalleriesStore();

const photoblogActive = computed(() => route.path.startsWith("/photoblog"));
const galleryActive = computed(() => route.path.startsWith("/gallery"));

function displayName(n: string) {
  return n.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

interface BreadcrumbItem {
  label: string;
  to?: string;
}

const breadcrumbItems = computed<BreadcrumbItem[]>(() => {
  const hash = route.hash.replace("#", "");
  const hasPhoto = Boolean(hash && hash !== "grid");

  if (photoblogActive.value) {
    const items: BreadcrumbItem[] = [
      { label: "fmor.in", to: "/photoblog/" },
      hasPhoto ? { label: "Photoblog", to: "/photoblog/" } : { label: "Photoblog" },
    ];
    if (hasPhoto) {
      const idx = photoblogStore.photoBySlug(hash);
      const photo = idx !== -1 ? photoblogStore.photos[idx] : null;
      items.push({ label: photo?.alt || hash });
    }
    return items;
  }

  if (galleryActive.value) {
    const name = route.params.name as string | undefined;
    const items: BreadcrumbItem[] = [{ label: "fmor.in", to: "/photoblog/" }];
    if (!name) {
      items.push({ label: "Gallery" });
      return items;
    }
    items.push({ label: "Gallery", to: "/gallery/" });
    if (hasPhoto) {
      items.push({ label: displayName(name), to: `/gallery/${name}/` });
      const idx = galleriesStore.photoBySlug(name, hash);
      const photo = idx !== -1 ? galleriesStore.photosFor(name)[idx] : null;
      items.push({ label: photo?.alt || hash });
    } else {
      items.push({ label: displayName(name) });
    }
    return items;
  }

  return [{ label: "fmor.in", to: "/photoblog/" }];
});

const secondaryLinks = computed(() => {
  const links: { label: string; to: string }[] = [];
  if (!photoblogActive.value) links.push({ label: "Photoblog", to: "/photoblog/" });
  if (!galleryActive.value) links.push({ label: "Gallery", to: "/gallery/" });
  return links;
});

const parentRoute = computed(() => {
  for (let i = breadcrumbItems.value.length - 1; i >= 0; i--) {
    if (breadcrumbItems.value[i].to) return breadcrumbItems.value[i].to!;
  }
  return null;
});

function navigate(path: string) {
  router.push(path);
}

function onKeydown(e: KeyboardEvent) {
  if ((e.key === "ArrowUp" || e.key === "Escape") && parentRoute.value) {
    e.preventDefault();
    router.push(parentRoute.value);
  }
}

onMounted(() => document.addEventListener("keydown", onKeydown));
onUnmounted(() => document.removeEventListener("keydown", onKeydown));
</script>

<template>
  <header
    class="fixed top-0 left-0 right-0 z-50 h-10 flex items-center justify-between px-4 bg-neutral-950 border-b border-neutral-800"
  >
    <nav class="flex items-center text-sm">
      <template v-for="(item, i) in breadcrumbItems" :key="i">
        <span v-if="i > 0" class="text-neutral-700 mx-1.5">/</span>
        <a
          v-if="item.to"
          :href="item.to"
          class="transition-colors"
          :class="
            i === 0
              ? 'font-medium tracking-widest text-neutral-500 hover:text-neutral-300'
              : 'text-neutral-500 hover:text-neutral-300'
          "
          @click.prevent="navigate(item.to)"
          >{{ item.label }}</a
        >
        <span v-else class="text-white">{{ item.label }}</span>
      </template>
    </nav>
    <nav class="flex gap-6">
      <a
        v-for="link in secondaryLinks"
        :key="link.to"
        :href="link.to"
        class="text-sm text-neutral-500 hover:text-neutral-300 transition-colors"
        @click.prevent="navigate(link.to)"
        >{{ link.label }}</a
      >
    </nav>
  </header>
</template>

<style scoped>
@media (orientation: landscape) and (max-height: 500px) {
  header {
    display: none;
  }
}
</style>
