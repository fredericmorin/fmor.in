# Slideshow Blur-Up Progressive Loading Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Show the cached grid thumbnail (blurred, scaled up) while the full-resolution slideshow image loads, then cross-fade to the hi-res version once it's ready.

**Architecture:** All changes are in `PhotoSlideshow.vue`. A `isLoading` boolean resets on each photo change. Two image layers stack in the photo area: a blurred placeholder (using the same `srcset`/`sizes` as the grid so it's a cache hit) on the bottom, and the full-res `<picture>` on top starting at `opacity: 0`. When the full-res `@load` fires, `isLoading` becomes `false` and the opacity transitions to 1.

**Tech Stack:** Vue 3 Composition API, Tailwind CSS, inline CSS transitions

---

### Task 1: Add `isLoading` state and reset it on photo change

**Files:**
- Modify: `src/components/PhotoSlideshow.vue:1-73` (script section)

- [ ] **Step 1: Add `isLoading` ref and reset watcher**

  In the `<script setup>` block, after the existing `watch` for adjacent preloading (line 44), add:

  ```ts
  const isLoading = ref(true);

  watch(
    () => props.index,
    () => {
      isLoading.value = true;
    },
  );
  ```

  The import line at the top already includes `ref` and `watch` — no import changes needed.

- [ ] **Step 2: Add `onLoad` handler for the full-res image**

  After the watcher above, add:

  ```ts
  function onFullResLoad() {
    isLoading.value = false;
  }
  ```

- [ ] **Step 3: Verify the file compiles**

  Run: `npm run build 2>&1 | tail -5`

  Expected: no TypeScript or Vite errors.

- [ ] **Step 4: Commit**

  ```bash
  git add src/components/PhotoSlideshow.vue
  git commit -m "feat: add isLoading state to slideshow, reset on photo change"
  ```

---

### Task 2: Add the blurred placeholder layer

**Files:**
- Modify: `src/components/PhotoSlideshow.vue` (template section)

The placeholder must use the same `srcset` and `sizes` as the grid thumbnails so the browser resolves the exact same URL already cached.

The existing `srcset` helper in the component:
```ts
function srcset(photo: Photo, format: "avif" | "jpg") {
  return photo.sizes.map((s) => `${photo.base}-${s}.${format} ${s}w`).join(", ");
}
```

- [ ] **Step 1: Insert the placeholder `<picture>` inside the photo area div**

  In the template, find the `<!-- Image -->` comment (line 92). Insert the following **before** it:

  ```html
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
  ```

  The `absolute inset-0` positions it behind the full-res image. The `scale(1.05)` hides the blurred edges. The fallback `:src` uses `sizes[0]` (smallest size) in case `srcset` isn't picked up.

- [ ] **Step 2: Verify the file compiles**

  Run: `npm run build 2>&1 | tail -5`

  Expected: no errors.

- [ ] **Step 3: Commit**

  ```bash
  git add src/components/PhotoSlideshow.vue
  git commit -m "feat: add blurred placeholder layer to slideshow"
  ```

---

### Task 3: Wire up the full-res fade-in and `@load` handler

**Files:**
- Modify: `src/components/PhotoSlideshow.vue` (template section)

- [ ] **Step 1: Update the full-res `<picture>` element**

  Find the existing `<!-- Image -->` block (the `<picture v-if="photo">` around line 93). Replace it with:

  ```html
  <!-- Full-res image (fades in once loaded) -->
  <picture v-if="photo" class="absolute inset-0 flex items-center justify-center w-full h-full">
    <source
      v-if="avifSupported"
      type="image/avif"
      :srcset="srcset(photo, 'avif')"
      sizes="100vw"
    />
    <source type="image/jpeg" :srcset="srcset(photo, 'jpg')" sizes="100vw" />
    <img
      :key="photo.slug"
      :src="fallbackSrc(photo)"
      :alt="photo.alt"
      class="max-w-full max-h-full object-contain select-none"
      :style="{ maxHeight: 'calc(100vh - 40px - 40px)', transition: 'opacity 0.4s ease', opacity: isLoading ? 0 : 1 }"
      draggable="false"
      @load="onFullResLoad"
    />
  </picture>
  ```

  Key changes vs. the original:
  - Added `absolute inset-0 flex items-center justify-center` so it layers on top of the placeholder
  - Added `:key="photo.slug"` on the `<img>` — forces Vue to recreate the element on photo change, ensuring `@load` always fires for the current photo
  - Added `transition: opacity 0.4s ease` and `:style="{ opacity: isLoading ? 0 : 1 }"` for the fade-in
  - Added `@load="onFullResLoad"`

  Note: All styles are combined into a single `:style` object to avoid any ambiguity with Vue's style merging.

- [ ] **Step 2: Verify the file compiles**

  Run: `npm run build 2>&1 | tail -5`

  Expected: no errors.

- [ ] **Step 3: Commit**

  ```bash
  git add src/components/PhotoSlideshow.vue
  git commit -m "feat: fade in full-res image after load, wired to isLoading state"
  ```

---

### Task 4: Manual verification and Python test suite

**Files:** none changed

- [ ] **Step 1: Start the dev server**

  Run: `make serve`

  Open the photoblog or a gallery in the browser.

- [ ] **Step 2: Verify blur-up on first open**

  Click any photo thumbnail. You should see the blurred thumbnail appear immediately, then the sharp full-res image fade in on top. If the hi-res was already cached, the fade may be instant — use DevTools → Network → throttle to "Slow 3G" to observe the effect clearly.

- [ ] **Step 3: Verify navigating between photos**

  Press ArrowRight / ArrowLeft to move through photos. Each photo change should reset to the blurred placeholder, then fade to sharp.

- [ ] **Step 4: Verify no layout shift**

  The EXIF bar and navigation arrows should not move during the fade transition.

- [ ] **Step 5: Run the Python test suite**

  Run: `make test`

  Expected: all tests pass (no changes to build pipeline).

- [ ] **Step 6: Final commit if any fixup needed, then done**

  If no fixups needed, the feature is complete. The three commits from Tasks 1–3 form the complete change.
