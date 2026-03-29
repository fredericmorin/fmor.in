# fmor.in

Static photography site with a full-screen photoblog slideshow and a grid-based gallery. No backend — a Python build script processes source photos and emits a folder of HTML/CSS/JS.

## Features

- **Photoblog** — full-viewport slideshow, one photo at a time, newest-first by EXIF date; swipe up/down to switch to the inline grid view
- **Gallery** — responsive thumbnail grid with a lightbox viewer, organised into named subfolders
- **Responsive images** — AVIF + JPEG at multiple sizes via `<picture>`, served to the right device without waste
- **EXIF metadata** — camera, lens, focal length, aperture, shutter, ISO displayed in a compact bar below each photo (GPS excluded); overrideable via sidecar YAML files
- **Navigation** — keyboard arrows, click/hover zones, and touch swipe on all photo views; maximised photo area in mobile landscape
- **Deep linking** — URL hash (`#slug`, `/gallery/street/#slug`) for direct links; browser back/forward works
- **Parallel builds** — image generation runs in a thread pool with live progress output

## Stack

Python 3.12+, Pillow, Jinja2, exifread, PyYAML, uv · Vanilla JS (<5 KB), no runtime dependencies

## Adding content

**Photoblog:** drop photos into `content/photoblog/`. Accepted formats: `.jpg`, `.jpeg`, `.png`, `.tiff`.

**Galleries:** create a subfolder under `content/galleries/` and drop photos into it. The folder name becomes the gallery name and URL slug.

**Gallery cover:** by default the first photo (by date) is used as the cover card image. To override, place a `_cover.jpg` (or any accepted format with a `_cover` stem) in the folder — it will be used as the cover and excluded from the gallery photo list.

**EXIF sidecar files:** place a `.yaml` file alongside any photo (same base name, e.g. `shot.yaml` for `shot.jpg`) to override or supplement its EXIF metadata. Any key in the sidecar replaces the value extracted from the image. Two extra keys are supported: `title` (appended to the output slug and URL) and `caption` (available in templates). Invalid YAML files are skipped with a warning.

## Makefile targets

| Target | What it does |
|--------|-------------|
| `make build` | Run the full build pipeline |
| `make serve` | Build, then serve `output/` on `localhost:8000` |
| `make deploy` | Clean build, then rsync `output/` to `fmor.in:/data/fmor.in` |

## Build pipeline

1. **Scan** — walks `content/`, builds a photo manifest with EXIF metadata and sort order. Empty folders are skipped with a warning.
2. **Generate images** — produces 3 sizes × 2 formats (AVIF + JPEG) per photoblog photo, 4 sizes × 2 formats per gallery photo. Skips files already up-to-date by source mtime. Runs in parallel with live progress.
3. **Generate covers** — resizes each gallery's cover photo for the index grid.
4. **Render templates** — Jinja2 templates are always re-rendered (fast).
5. **Copy static assets** — `static/` → `output/static/`

### Output naming

- **Photoblog:** `output/photoblog/photos/<slug>-<size>.<fmt>` (e.g. `20240615-093000-golden-hour-800.avif`) — slug is derived from the EXIF capture date (`yyyymmdd-hhmmss`), with the sidecar `title` appended when present; falls back to the filename stem when no EXIF date is available.
- **Galleries:** `output/gallery/<folder>/photos/<slug>-<size>.<fmt>` — same slug logic, scoped per gallery. Build fails if two source files in the same gallery resolve to the same slug.
