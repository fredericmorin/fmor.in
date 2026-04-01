# Header Breadcrumbs Design

**Date:** 2026-03-31

## Overview

Replace the current header navigation (logo left, section links right) with a breadcrumb-based header. The breadcrumb reflects the current location in the site hierarchy. Only inactive section links appear on the right — the active section is already represented in the breadcrumb and is not repeated.

## Breadcrumb Structure

All routes include `fmor.in` as the leftmost crumb, linking to `/photoblog/` (same behaviour as the current logo).

| Route | Left (breadcrumb) | Right (inactive sections) |
|---|---|---|
| `/photoblog/` | `fmor.in / Photoblog` | `Gallery` |
| `/photoblog/#<slug>` | `fmor.in / Photoblog / [photo name]` | `Gallery` |
| `/gallery/` | `fmor.in / Gallery` | `Photoblog` |
| `/gallery/:name/` | `fmor.in / Gallery / [Gallery Name]` | `Photoblog` |
| `/gallery/:name/#<slug>` | `fmor.in / Gallery / [Gallery Name] / [photo name]` | `Photoblog` |

Photo name = `photo.alt` if set, otherwise `photo.slug`.
Gallery Name = hyphens replaced with spaces, title-cased (same logic as `displayName` in `GalleryView.vue` — inline it in `AppHeader` rather than extracting a shared utility).

Ancestor crumbs (all but the last) are clickable links:
- `fmor.in` → `/photoblog/`
- `Photoblog` → `/photoblog/`
- `Gallery` → `/gallery/`
- `[Gallery Name]` → `/gallery/:name/` (hash cleared)

## Styling

- **Ancestor crumbs:** `text-neutral-500`, hover `text-neutral-300`, no underline
- **Current crumb (last):** `text-white`
- **Separator `/`:** `text-neutral-700`, `mx-1.5`
- **Inactive section links (right):** `text-neutral-500`, hover `text-neutral-300` — same muted style as today

## Implementation

### AppHeader.vue

- Import `usePhotoblogStore` and `useGalleriesStore`.
- Compute a `breadcrumbItems` array: `{ label: string, to?: string }[]`. Last item has no `to`.
- Compute `secondaryLinks`: the section(s) not currently active.
- Derive current photo for photoblog: `route.hash` → `photoblogStore.photoBySlug(hash)` → `store.photos[idx]`.
- Derive current photo for gallery: `route.params.name` + `route.hash` → `galleriesStore.photoBySlug(name, hash)` → index into `store.photosFor(name)`.
- Replace existing template with breadcrumb nav on the left and secondary links on the right.

### GalleryView.vue

- Remove the `#header` slot content from the `<PhotoGrid>` usage (the "← Galleries" button and gallery name `h1`).
- The `PhotoGrid` component itself is unchanged — the slot simply goes unused.

### PhotoGrid.vue

No changes needed. The `#header` slot remains available for other potential uses.

## Out of Scope

- No changes to the photoblog grid (no in-page header was added there previously).
- No changes to the gallery index view beyond what the header redesign covers.
- No changes to `PhotoSlideshow`.
