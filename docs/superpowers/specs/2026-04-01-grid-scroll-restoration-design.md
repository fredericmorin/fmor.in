# Grid Scroll Restoration Design

**Date:** 2026-04-01
**Status:** Approved

## Problem

When navigating through slideshow photos and returning to the grid view, the grid scrolls to the top rather than to the last-viewed photo. The scroll mechanism already exists in `PhotoGrid` (`scrollIntoView` on mount) but `activeIndex` is never passed from the parent views.

## Solution

Track the last non-null `currentIndex` in a `lastViewedIndex` ref within each view, and pass it as `activeIndex` to `PhotoGrid`.

## Changes

### `PhotoblogView.vue` and `GalleryView.vue` (identical pattern in both)

Add a ref to track the last slideshow position:

```ts
const lastViewedIndex = ref<number | null>(null);

watch(currentIndex, (idx) => {
  if (idx !== null) lastViewedIndex.value = idx;
});
```

Pass it to `PhotoGrid`:

```html
<PhotoGrid
  :photos="store.photos"
  :active-index="lastViewedIndex ?? undefined"
  @select="openPhoto"
/>
```

### `PhotoGrid.vue`

No changes required. The existing `activeIndex` prop and `onMounted` scroll logic handle everything:

```ts
onMounted(async () => {
  avifSupported.value = await useAvif();
  if (activeRef.value) {
    activeRef.value.scrollIntoView({ block: "center", behavior: "instant" });
  }
});
```

## Behaviour

| Scenario | Result |
|---|---|
| Navigate to photo #N via slideshow, click Grid | Grid scrolls to photo #N |
| Navigate slideshow A→B→C, click Grid | Grid scrolls to photo C |
| Direct URL entry `#slug` → click Grid | Grid scrolls to that photo |
| Fresh grid visit (no hash) | No scroll (top of page, as before) |

## Scope

- 2 files modified: `src/views/PhotoblogView.vue`, `src/views/GalleryView.vue`
- ~4 lines added per file
- No component API changes
