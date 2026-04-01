# fmor.in

Static photography site. Python image pipeline + Vue 3 SPA → HTML/CSS/JS output. No backend.

## Commands

- `make build` — full build (JS bundle + Python pipeline)
- `make serve` — run Python pipeline, then start Vite dev server
- `make deploy` — full build + rsync to fmor.in:/data/fmor.in/htdocs
- `make fmt` — format Python (ruff) and JS/HTML (prettier)
- `make test` — run tests

## Code conventions

- Build logic lives in `build.py`
- Vue SPA source in `src/` (Vue 3, TypeScript, Pinia, Vue Router, Tailwind)
- Templates in `templates/` (Jinja2 SPA shells), static assets in `static/`
- Content (photos) in `content/photoblog/` and `content/galleries/`
- Output goes to `output/` (gitignored); JS bundle to `static/dist/` (gitignored)

## Key behaviours

- Image slugs are derived from EXIF capture date (`yyyymmdd-hhmmss`), falling back to filename stem
- Sidecar `.yaml` files alongside photos can override EXIF fields; `title` appends to slug, `caption` is available in templates
- AVIF + JPEG generated at 4 sizes (400, 800, 1920, 3200) via `<picture>`; existing files skipped by mtime
- HEIC/HEIF accepted in addition to JPEG/PNG/TIFF
- Build writes JSON manifests to `output/data/` for the SPA to fetch at runtime
- Landing page is a meta-refresh redirect to `/photoblog/`; all section pages are SPA shells

## README

Keep README.md up to date when features change. It documents features, stack, content workflow, Makefile targets, and output naming.

## Git

- Feature branches: `claude/<description>-<id>`
- Commit messages: conventional commits (`feat:`, `fix:`, `docs:`, etc.)
