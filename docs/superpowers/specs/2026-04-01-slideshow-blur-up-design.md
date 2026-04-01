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

1. **Placeholder (bottom):** A `<picture>` element using the same `srcset` as the grid thumbnail and `sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw"`. This causes the browser to resolve the same URL it already fetched for the grid thumbnail — a guaranteed cache hit, so the placeholder renders instantly. Rendered with `object-contain`, CSS `filter: blur(12px)`, and `transform: scale(1.05)` (to hide blurred edges). Always visible.

2. **Full-res (top):** The existing `<picture>` element. Starts at `opacity: 0`, transitions to `opacity: 1` over 0.4s once its `@load` event fires.

### State

A single reactive boolean `isLoading` per photo:

- Set to `true` whenever `props.index` changes (via `watch`)
- Set to `false` when the full-res `<img>` fires `@load`

### Edge Cases

- **Already cached:** `@load` fires immediately; transition is imperceptible — correct behaviour
- **Index changes mid-load:** The `watch` on `index` resets `isLoading = true`. The full-res `<img>` gets `:key="photo.slug"` so Vue recreates it on photo change, ensuring `@load` always fires for the current photo and stale load events from the previous photo are discarded.
- **Deep-linked photo:** No grid visit means the thumbnail-sized image isn't cached; both placeholder and full-res load from scratch. The placeholder still appears first (being smaller), so the blur-up still works, just with a short delay — acceptable

### Format selection

The placeholder uses the same `srcset` helper and `avifSupported` flag as the full-res image, so it requests the same format (AVIF or JPEG) the browser already cached from the grid.

## Scope

- **Changed:** `src/components/PhotoSlideshow.vue` only
- **Unchanged:** `PhotoGrid.vue`, `types.ts`, build scripts, adjacent-photo preloading logic
