# Slideshow Blur-Up Progressive Loading

**Date:** 2026-04-01
**Status:** Approved

## Problem

When navigating to a photo in the slideshow, the full-resolution image (up to 1920px wide) can take several seconds to load, leaving the user looking at a blank/dark area.

## Solution

Implement a blur-up progressive loading pattern in `PhotoSlideshow.vue`:

- While the hi-res image loads, show the smallest available size scaled up and blurred as a placeholder
- Cross-fade to the full-res image once it finishes loading
- No spinner — the blurred placeholder is itself the visual feedback

## Design

### Layers

Two images are stacked in the photo area:

1. **Placeholder (bottom):** `<img>` using `{base}-{sizes[0]}.{ext}` — the smallest available size. Rendered with `object-contain`, CSS `filter: blur(12px)`, and `transform: scale(1.05)` (to hide blurred edges). Always visible.

2. **Full-res (top):** The existing `<picture>` element. Starts at `opacity: 0`, transitions to `opacity: 1` over 0.4s once its `@load` event fires.

### State

A single reactive boolean `isLoading` per photo:

- Set to `true` whenever `props.index` changes (via `watch`)
- Set to `false` when the full-res `<img>` fires `@load`

### Edge Cases

- **Already cached:** `@load` fires immediately; transition is imperceptible — correct behaviour
- **Index changes mid-load:** The `watch` on `index` resets `isLoading = true`. The full-res `<img>` gets `:key="photo.slug"` so Vue recreates it on photo change, ensuring `@load` always fires for the current photo and stale load events from the previous photo are discarded.
- **Deep-linked photo:** No grid visit means the placeholder may also be uncached; the blur-up still occurs from the same small image, just with a brief delay on both layers — acceptable

### Format selection

The placeholder uses the same format logic as the full-res image (AVIF if supported, else JPEG), ensuring the smallest size used matches what the browser would cache.

## Scope

- **Changed:** `src/components/PhotoSlideshow.vue` only
- **Unchanged:** `PhotoGrid.vue`, `types.ts`, build scripts, adjacent-photo preloading logic
