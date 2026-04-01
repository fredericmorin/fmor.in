# Header Breadcrumbs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the site header's logo+nav layout with a breadcrumb trail on the left and inactive section links on the right.

**Architecture:** `AppHeader` imports both Pinia stores and derives breadcrumb items and secondary nav links purely from route state + store data. `GalleryView` drops its in-page breadcrumb slot since the header now owns that context.

**Tech Stack:** Vue 3 (Composition API), Vue Router, Pinia

---

## File Map

| File | Change |
|---|---|
| `src/components/AppHeader.vue` | Full rewrite of script + template |
| `src/views/GalleryView.vue` | Remove `#header` slot from `<PhotoGrid>` |

No new files. No test files (project has no frontend test suite — only Python build tests).

---

### Task 1: Rewrite AppHeader.vue

**Files:**
- Modify: `src/components/AppHeader.vue`

- [ ] **Step 1: Replace the file contents**

```vue
<script setup lang="ts">
import { computed } from "vue";
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

function navigate(path: string) {
  router.push(path);
}
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
```

- [ ] **Step 2: Verify it builds without type errors**

```bash
cd /Users/fred/project/fmor.in && npx tsc --noEmit
```

Expected: no output (zero errors).

- [ ] **Step 3: Commit**

```bash
git add src/components/AppHeader.vue
git commit -m "feat: replace header nav with breadcrumb trail"
```

---

### Task 2: Remove in-page breadcrumb from GalleryView

**Files:**
- Modify: `src/views/GalleryView.vue`

- [ ] **Step 1: Replace the `<PhotoGrid>` usage** (lines 80–92) to drop the slot

Old:
```vue
      <PhotoGrid v-if="showGrid" :photos="photos" @select="openPhoto">
        <template #header>
          <div class="flex items-center gap-4 px-4 py-3 border-b border-neutral-800">
            <button
              class="text-sm text-neutral-500 hover:text-neutral-300 transition-colors"
              @click="router.push('/gallery/')"
            >
              ← Galleries
            </button>
            <h1 class="text-sm text-neutral-300 font-medium">{{ displayName(name) }}</h1>
          </div>
        </template>
      </PhotoGrid>
```

New:
```vue
      <PhotoGrid v-if="showGrid" :photos="photos" @select="openPhoto" />
```

- [ ] **Step 2: Verify it builds without type errors**

```bash
cd /Users/fred/project/fmor.in && npx tsc --noEmit
```

Expected: no output (zero errors).

- [ ] **Step 3: Smoke test in the browser**

```bash
make serve
```

Visit each route and verify:

| URL | Expected breadcrumb (left) | Expected right nav |
|---|---|---|
| `/photoblog/` | `fmor.in / Photoblog` | `Gallery` |
| `/photoblog/#<any-slug>` | `fmor.in / Photoblog / [photo name]` | `Gallery` |
| `/gallery/` | `fmor.in / Gallery` | `Photoblog` |
| `/gallery/<name>/` | `fmor.in / Gallery / [Name]` | `Photoblog` — no in-page breadcrumb below header |
| `/gallery/<name>/#<slug>` | `fmor.in / Gallery / [Name] / [photo name]` | `Photoblog` |

Also confirm clicking ancestor crumbs navigates correctly:
- `fmor.in` → goes to `/photoblog/`
- `Photoblog` (when photo open) → goes to `/photoblog/`
- `Gallery` (when in gallery) → goes to `/gallery/`
- `[Gallery Name]` (when photo open) → goes back to gallery grid

- [ ] **Step 4: Commit**

```bash
git add src/views/GalleryView.vue
git commit -m "feat: remove in-page gallery breadcrumb (moved to header)"
```
