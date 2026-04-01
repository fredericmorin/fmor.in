# fmor.in

Static photography site. Python build script → HTML/CSS/JS output. No backend.

## Commands

- `make build` — full build
- `make serve` — build + serve on localhost:8000
- `make deploy` — clean build + rsync to fmor.in:/data/fmor.in
- `make test` — run tests

## Code conventions

- Build logic lives in `build.py`
- Templates in `templates/`, static assets in `static/`
- Content (photos) in `content/photoblog/` and `content/galleries/`
- Output goes to `output/` (gitignored)

## Key behaviours

- Image slugs are derived from EXIF capture date (`yyyymmdd-hhmmss`), falling back to filename stem
- Sidecar `.yaml` files alongside photos can override EXIF fields; `title` appends to slug, `caption` is available in templates
- AVIF + JPEG generated at multiple sizes via `<picture>`; existing files skipped by mtime

## README

Keep README.md up to date when features change. It documents features, stack, content workflow, Makefile targets, and output naming.

## Git

- Feature branches: `claude/<description>-<id>`
- Commit messages: conventional commits (`feat:`, `fix:`, `docs:`, etc.)
