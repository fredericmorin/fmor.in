# Gallery Slideshow Design

**Date:** 2026-03-28
**Status:** Approved

## Summary

Rebuild the individual gallery page (`/gallery/<name>/`) to use the same UX pattern as the photoblog: JS-driven thumbnail grid, slug-based URL hashes, slideshow-first navigation, and EXIF display. Approach A — reuse existing photoblog JS wholesale.

## Changes

### `templates/gallery.html`

- Remove the Jinja2 `{% for photo %}` thumbnail grid loop.
- Remove the lightbox `<div id="lightbox">` and all its contents.
- Change `window.GALLERY_PHOTOS` to `window.PHOTOS` in the `<script>` block.
- Add the same slideshow + grid HTML structure as `photoblog.html`, below the existing gallery header:
  - `<div class="slideshow" id="slideshow" data-section="gallery">` containing nav zones, `#photo-picture`, `#photo-counter`, and `#exif-container`.
  - `<div id="photoblog-grid-view">` containing `<div class="thumbnail-grid" id="photoblog-grid-thumbnails">`.
- The gallery header (`← Galleries · Title`) stays above these divs, unchanged.

### `build.py`

- In the gallery build loop, replace the call to `build_gallery_photo_json(gallery["photos"], gallery["name"])` with `build_photo_json(gallery["photos"], f"/gallery/{gallery['name']}/photos", GALLERY_SIZES)`.
- Delete the `build_gallery_photo_json` function (no longer used).

### `static/js/main.js`

Remove the entire lightbox section, including:
- `openLightbox`, `closeLightbox`, `navigateLightbox`, `showLightboxPhoto` functions
- `lightboxIndex`, `lightboxOpen`, `previousFocus` variables
- `trapFocus` function
- Lightbox backdrop-click event listener
- `checkGalleryHash` function and its `DOMContentLoaded` call
- The lightbox branch in the `keydown` handler

The existing `initSlideshow()` already fires for any page that sets `window.PHOTOS`, so gallery pages automatically get slideshow behaviour with no new JS needed.

## Behaviour After Change

| Action | Result |
|---|---|
| Navigate to `/gallery/album/` (no hash) | Grid view shown |
| Navigate to `/gallery/album/#gallery` | Grid view shown |
| Click thumbnail | Slideshow opens at `#<slug>` |
| "Grid" link in slideshow | Returns to grid at `#gallery` |
| ← / → keys in slideshow | Navigate between photos |
| Esc key in slideshow | Returns to grid |
| EXIF data | Shown below photo in `#exif-container`, same as photoblog |

## What Is Not Changing

- Gallery index page (`gallery_index.html`) — unchanged.
- Photo generation / image sizes — unchanged (`GALLERY_SIZES` stays the same).
- Gallery header (back link + title) — stays in place above the slideshow/grid.
- CSS — no new styles needed; gallery reuses all existing photoblog/slideshow classes.
