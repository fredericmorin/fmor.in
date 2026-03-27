# fmor.in — Static Photoblog & Gallery

## Overview

A static photography website with two sections — a full-screen slideshow photoblog and a grid-based gallery — built from source photo folders by a Python build script. Dark, neutral design that puts all emphasis on the photographs.

**Domain:** fmor.in
**Stack:** Python (build), HTML/CSS/JS (output), no backend
**Build tools:** Pillow (10.1+ with built-in AVIF support), Jinja2, exifread
**Package management:** uv

## Project Structure

```
fmor.in/
├── content/
│   ├── photoblog/              # Flat folder of photos
│   └── galleries/
│       ├── street/             # Each subfolder = one gallery
│       ├── landscapes/
│       └── portraits/
├── templates/
│   ├── base.html               # Shared layout (header, dark theme, meta)
│   ├── photoblog.html          # Slideshow page
│   ├── gallery_index.html      # Grid of gallery covers
│   ├── gallery.html            # Single gallery: thumbnail grid + lightbox
│   └── partials/
│       └── exif.html           # EXIF info block (reused)
├── static/
│   ├── css/style.css
│   └── js/main.js
├── build.py                    # Build orchestrator
├── Makefile                    # make build, make clean, make serve
├── pyproject.toml              # uv project dependencies
└── output/                     # Generated static site
    ├── index.html              # Landing or redirect
    ├── photoblog/
    │   ├── index.html
    │   └── photos/             # Responsive images
    ├── gallery/
    │   ├── index.html
    │   ├── street/
    │   │   └── index.html
    │   └── ...
    └── static/
        ├── css/
        └── js/
```

## Accepted Source Formats

`.jpg`, `.jpeg`, `.png`, `.tiff` — other files in content folders are silently ignored.

## Build Pipeline

Invoked via `make build` which calls `build.py`.

1. **Scan** `content/` folder tree, build photo manifest (path, EXIF metadata, sort order). Empty folders are skipped (no HTML generated) and a warning is emitted to stderr.
2. **Generate responsive images** — for each source photo, produce 3 sizes (800px, 1600px, 2400px) × 2 formats (AVIF, JPEG) into `output/`. Skip files already up-to-date based on source file mtime (incremental builds). Mtime-based skipping applies only to image generation.
3. **Generate gallery covers** — cover photo of each gallery folder (see Gallery Index section), resized for the cover grid
4. **Render templates** — Jinja2 templates are always re-rendered on every build (cheap operation). Produces HTML files in `output/`.
5. **Copy static assets** — `static/` → `output/static/`

### Output file naming

- **Photoblog:** `output/photoblog/photos/<index>-<size>.<fmt>` where `<index>` is a zero-padded position based on sort order (e.g., `001-800.avif`). This avoids collisions from duplicate source filenames.
- **Galleries:** `output/gallery/<folder-name>/photos/<original-stem>-<size>.<fmt>`. Files are scoped under their gallery subfolder, so collisions across galleries are not possible. If two source files in the same gallery share a stem (e.g., `sunset.jpg` and `sunset.png`), the build fails with an error.

### Makefile Targets

- `make build` — run full build pipeline
- `make clean` — remove `output/` directory
- `make serve` — `python -m http.server` in `output/` for local preview

## Responsive Images

Each photoblog photo generates 6 files: 3 sizes × 2 formats. Gallery photos generate 8 files (4 sizes including a 400px thumbnail size).

```
photo-001-800.avif    photo-001-800.jpg
photo-001-1600.avif   photo-001-1600.jpg
photo-001-2400.avif   photo-001-2400.jpg
```

Served via `<picture>` element (example shows photoblog/lightbox `sizes`; see context-specific values below):

```html
<picture>
  <source type="image/avif"
    srcset="photo-800.avif 800w, photo-1600.avif 1600w, photo-2400.avif 2400w"
    sizes="100vw">
  <img src="photo-1600.jpg"
    srcset="photo-800.jpg 800w, photo-1600.jpg 1600w, photo-2400.jpg 2400w"
    sizes="100vw">
</picture>
```

The browser selects the appropriate size based on viewport width and device pixel ratio.

**`sizes` attribute varies by context:**
- Photoblog slideshow and lightbox: `sizes="100vw"`
- Gallery thumbnails: `sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw"`
- Gallery covers: `sizes="(max-width: 768px) 50vw, 33vw"`

Gallery thumbnails additionally generate a smaller 400px size for the grid (4 sizes total for gallery photos: 400, 800, 1600, 2400).

## EXIF Metadata

Extracted at build time using exifread, embedded as JSON in the generated HTML.

**Fields displayed:** camera model, lens, focal length, aperture, shutter speed, ISO, date taken, white balance, metering mode, exposure compensation.

**GPS data is excluded.**

**Missing EXIF data:** Fields that are absent are silently omitted from the display. If date taken is absent, fall back to file modification time for sorting. If no EXIF data exists at all, the EXIF bar is hidden.

**Presentation:** Compact single-line bar below the photo. Date left-aligned, all other fields right-aligned, dot-separated. Small subtle text (~10px, #555/#666 on dark background).

## Section 1: Photoblog (Slideshow)

**URL:** `/photoblog/`

**Layout:** Full-viewport slideshow. One photo at a time.

- Fixed header (~40px): "fmor.in" left, "Photoblog | Gallery" nav right
- Photo fills remaining viewport, centered, `object-fit: contain`
- Compact EXIF bar at bottom
- Photo counter top-right (e.g., "3 / 27")

**Navigation:**

- Mouse hover zones: left 20% and right 20% of viewport show arrow cursor/indicator, click navigates
- Keyboard: left/right arrow keys
- Touch: swipe left/right on mobile
- No page reload — JS swaps `<picture>` sources

**Sort order:** EXIF date taken, newest first. Filename as tiebreaker.

**Deep linking:** URL hash (`#3`) for direct links to specific photos. Browser back/forward navigates between photos.

**Preloading:** Next and previous photos are preloaded for instant transitions.

## Section 2: Gallery

### Gallery Index

**URL:** `/gallery/`

**Layout:** Responsive grid of gallery cover cards. Each card shows:

- Cover image: by default, the first photo in the gallery's sort order. Can be overridden by placing a `_cover.jpg` (or any accepted format with `_cover` stem) in the folder. `_cover.*` files are excluded from the gallery photo list — they are used only as the cover.
- Gallery name (folder name) overlaid at bottom with gradient
- Photo count

**Sort order:** Galleries are listed alphabetically by folder name.

**Grid columns:** 2 on mobile, 3 on desktop.

### Gallery Page

**URL:** `/gallery/<folder-name>/`

**Layout:** Breadcrumb ("← Galleries · Street") at top, then responsive thumbnail grid.

**Grid:** Square thumbnails, 2 columns on mobile, 3-4 on desktop. Gap: 8px.

**Sort order:** EXIF date taken, newest first. Filename as tiebreaker (same as photoblog).

### Lightbox

Triggered by clicking a thumbnail.

- `position: fixed` full-viewport overlay, near-black background (`rgba(0,0,0,0.95)`)
- Photo centered, `object-fit: contain`
- Same compact EXIF bar as photoblog
- Close: X button (top-right), Escape key, or click on backdrop
- Navigation: same hover zones + keyboard + swipe as photoblog
- Photo counter top-right
- Body scroll locked while open
- Deep linking via URL hash (`/gallery/street/#5`)

## Header

Minimal fixed header on all pages:

- Height: ~40px
- Background: `#111`, border-bottom: `#2a2a2a`
- Left: "fmor.in" — site name, 14px, 600 weight, `#ccc`
- Right: "Photoblog" and "Gallery" links — 12px, uppercase, `#777` default, `#fff` with underline when active

## Color Palette

| Element | Color |
|---------|-------|
| Page background | `#111` |
| Content areas | `#1a1a1a` |
| Header background | `#111` |
| Header border | `#2a2a2a` |
| Primary text | `#ccc` |
| Secondary text | `#888` |
| EXIF / subtle text | `#555` – `#666` |
| Active nav | `#fff` |
| Lightbox backdrop | `rgba(0,0,0,0.95)` |

No colored accents. Photos are the only source of color on the page.

## Typography

System font stack: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`

Small sizes throughout to minimize visual competition with photos.

## Responsive Breakpoints

| Breakpoint | Gallery grid | Thumbnail grid | Notes |
|------------|-------------|----------------|-------|
| < 768px | 2 columns | 2 columns | Swipe nav, nav wraps below site name |
| 768–1200px | 3 columns | 3 columns | Standard layout |
| > 1200px | 3 columns | 4 columns | Full layout |

## JavaScript

**No dependencies.** Vanilla JS only, targeting well under 5KB total.

### Photoblog slideshow

- Photo manifest as JSON embedded in HTML at build time
- `swapPhoto(index)` updates `<picture>` sources and EXIF bar
- Preloads adjacent photos
- Keyboard, hover zone, and touch event listeners
- URL hash state management

### Gallery lightbox

- Opens as fixed overlay on thumbnail click
- Same nav mechanics as photoblog (hover, keyboard, swipe)
- Escape / X / backdrop click to close
- Body scroll lock
- URL hash for deep-linking

## Landing Page

`/index.html` uses `<meta http-equiv="refresh" content="0;url=/photoblog/">` to redirect to the photoblog. This keeps the photoblog as the primary experience.

## Accessibility

- All `<img>` elements include an `alt` attribute (filename stem, cleaned up: underscores/hyphens replaced with spaces)
- Navigation controls have `aria-label` attributes (e.g., "Next photo", "Previous photo", "Close lightbox")
- Visible focus outlines on all interactive elements for keyboard navigation
- `prefers-reduced-motion` media query disables slide transitions when the user prefers reduced motion
- Lightbox traps focus while open and restores it on close

## Social / Meta

- OpenGraph tags on all pages (`og:title`, `og:image`, `og:type`)
- Favicon (place `favicon.ico` in `static/`, copied to output root)
