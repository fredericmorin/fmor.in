# Parallel Build + Progress Reporting

**Date:** 2026-03-27
**Status:** Approved

## Problem

The build is sequential: each `resize_and_save` call (photo × size × format) runs one at a time. There is no progress feedback during the slow image generation phase.

## Goals

1. Parallelize image generation using a thread pool.
2. Show non-scrolling progress to stderr when attached to a terminal.
3. Stream generated file names to stderr when not attached to a terminal.

## Scope

Changes are confined to `build.py`. No new files, no new dependencies (stdlib only: `concurrent.futures`, `os`).

---

## Design

### Reporter

A `Reporter` class constructed once in `build_site`, detecting `sys.stderr.isatty()` at creation.

**Non-TTY mode** (pipe, CI, redirect):
- Each completed path is printed as a plain line to stderr: `output/photoblog/photos/001-800.avif`
- Output streams as futures complete via `as_completed`

**TTY mode** (interactive terminal):
- A single status line is maintained using `\r` to overwrite in place
- Format: `[42/150] output/photoblog/photos/001-800.avif`
- No scrolling; terminal width is respected (truncate path if needed)
- On `finish()`: clear the status line, print the summary

Methods:
- `report(path: Path)` — called per completed file
- `finish(summary: str)` — called once at the end

### Image Task Collection

`build_site` collects all image tasks into a flat list of `(source, output_path, max_width, fmt)` tuples before submitting any:
- Photoblog: each photo × `PHOTOBLOG_SIZES` × `IMAGE_FORMATS`
- Each gallery: each photo × `GALLERY_SIZES` × `IMAGE_FORMATS`
- Gallery cover (if `_cover` file): same as gallery photos

This replaces the current separate `generate_photoblog_images` and `generate_gallery_images` calls. The two functions are refactored to return task lists rather than execute directly.

### Parallel Execution

```
tasks = collect_all_image_tasks(...)
total = len(tasks)
with ThreadPoolExecutor() as pool:
    futures = {pool.submit(resize_and_save, *task): task for task in tasks}
    for future in as_completed(futures):
        path = future.result()   # resize_and_save returns output_path
        reporter.report(path)
reporter.finish(summary)
```

`resize_and_save` is updated to return `output_path`. The existing skip-if-newer check stays in place.

Default worker count: Python's `ThreadPoolExecutor` default (`min(32, os.cpu_count() + 4)`). No configuration knob needed.

### Error Handling

If a `resize_and_save` future raises, the exception propagates naturally via `future.result()` and halts the build with a traceback — same behavior as today.

---

## Files Changed

- `build.py` — all changes contained here

## No Changes To

- Templates, static assets, EXIF extraction, scanning logic, Makefile, tests
