# Parallel Build + Progress Reporting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Parallelize image generation in `build.py` using `ThreadPoolExecutor` and add TTY-aware progress reporting to stderr.

**Architecture:** `generate_photoblog_images` and `generate_gallery_images` are renamed to `collect_*_tasks` and return lists of `(source, output_path, max_width, fmt)` tuples instead of executing directly. `build_site` collects all tasks, then dispatches them via a `ThreadPoolExecutor`, reporting each completion through a `Reporter` that detects TTY vs non-TTY and behaves accordingly.

**Tech Stack:** Python stdlib — `concurrent.futures.ThreadPoolExecutor`, `concurrent.futures.as_completed`, `os`, `shutil`, `sys`. No new dependencies.

---

## File Map

| File | Change |
|------|--------|
| `build.py` | Add `Reporter`; rename generators to `collect_*_tasks`; add `run_image_tasks`; update `build_site` |
| `tests/test_images.py` | Update calls from `generate_*` to `collect_*_tasks` + execute tasks inline |

---

### Task 1: Make `resize_and_save` return `output_path`

**Files:**
- Modify: `build.py:152-177`
- Modify: `tests/test_images.py`

The function already creates the file; returning the path lets the parallel executor report completions.

- [ ] **Step 1: Write a failing test**

Add to `tests/test_images.py`:

```python
def test_resize_and_save_returns_output_path(tmp_path):
    from tests.helpers import make_test_image
    from build import resize_and_save
    src = tmp_path / "src.jpg"
    make_test_image(src, width=200, height=200)
    out = tmp_path / "out-100.jpg"
    result = resize_and_save(src, out, 100, "JPEG")
    assert result == out
```

- [ ] **Step 2: Run the test to verify it fails**

```
uv run pytest tests/test_images.py::test_resize_and_save_returns_output_path -v
```

Expected: `FAILED — AssertionError` (function currently returns `None`)

- [ ] **Step 3: Update `resize_and_save` to return `output_path`**

In `build.py`, change the last line of `resize_and_save` from:

```python
        img.save(output_path, fmt, **save_kwargs)
```

to:

```python
        img.save(output_path, fmt, **save_kwargs)
    return output_path
```

Note: the early-return skip path also needs the return. Replace the skip guard:

```python
    if output_path.exists() and output_path.stat().st_mtime > source.stat().st_mtime:
        return
```

with:

```python
    if output_path.exists() and output_path.stat().st_mtime > source.stat().st_mtime:
        return output_path
```

- [ ] **Step 4: Run the test to verify it passes**

```
uv run pytest tests/test_images.py::test_resize_and_save_returns_output_path -v
```

Expected: `PASSED`

- [ ] **Step 5: Run the full test suite to check nothing broke**

```
uv run pytest -v
```

Expected: all previously passing tests still pass.

- [ ] **Step 6: Commit**

```bash
git add build.py tests/test_images.py
git commit -m "feat: resize_and_save returns output_path"
```

---

### Task 2: Add `Reporter` class

**Files:**
- Modify: `build.py` (add class before `build_site`)
- Create test block in: `tests/test_images.py`

`Reporter` detects `sys.stderr.isatty()` at construction. In TTY mode it overwrites a single line; in non-TTY mode it prints one line per file.

- [ ] **Step 1: Write failing tests**

Add to `tests/test_images.py`:

```python
import io
import sys


def test_reporter_non_tty_prints_lines(tmp_path, capsys):
    from build import Reporter
    r = Reporter(total=3, is_tty=False)
    r.report(tmp_path / "a.jpg")
    r.report(tmp_path / "b.avif")
    captured = capsys.readouterr()
    lines = captured.err.strip().splitlines()
    assert len(lines) == 2
    assert "a.jpg" in lines[0]
    assert "b.avif" in lines[1]


def test_reporter_non_tty_finish_prints_summary(capsys):
    from build import Reporter
    r = Reporter(total=5, is_tty=False)
    r.finish("Build complete: 5 files")
    captured = capsys.readouterr()
    assert "Build complete: 5 files" in captured.err


def test_reporter_tty_overwrites_line(tmp_path, capsys, monkeypatch):
    from build import Reporter
    r = Reporter(total=3, is_tty=True)
    r.report(tmp_path / "a.jpg")
    r.report(tmp_path / "b.avif")
    captured = capsys.readouterr()
    # Should use \r, not \n between updates
    assert "\r" in captured.err
    # Should not have two newline-separated file lines
    newline_lines = [l for l in captured.err.split("\n") if l.strip()]
    assert len(newline_lines) <= 1


def test_reporter_tty_finish_clears_line(capsys):
    from build import Reporter
    r = Reporter(total=2, is_tty=True)
    r.finish("Done")
    captured = capsys.readouterr()
    assert "Done" in captured.err
```

- [ ] **Step 2: Run tests to verify they fail**

```
uv run pytest tests/test_images.py::test_reporter_non_tty_prints_lines tests/test_images.py::test_reporter_non_tty_finish_prints_summary tests/test_images.py::test_reporter_tty_overwrites_line tests/test_images.py::test_reporter_tty_finish_clears_line -v
```

Expected: all four `FAILED` with `ImportError` or `AttributeError` (class doesn't exist yet).

- [ ] **Step 3: Implement `Reporter` in `build.py`**

Add this class after the constants block (after `IMAGE_FORMATS = ...`) and before `extract_exif`:

```python
import os


class Reporter:
    """Progress reporter for image generation.

    TTY mode: overwrites a single status line using \\r.
    Non-TTY mode: prints one line per completed file.
    """

    def __init__(self, total: int, is_tty: bool | None = None):
        self._total = total
        self._done = 0
        self._is_tty = sys.stderr.isatty() if is_tty is None else is_tty

    def report(self, path: Path):
        self._done += 1
        rel = str(path)
        if self._is_tty:
            cols = os.get_terminal_size(sys.stderr.fileno()).columns if hasattr(os, "get_terminal_size") else 80
            line = f"[{self._done}/{self._total}] {rel}"
            if len(line) > cols:
                line = line[: cols - 1]
            print(f"\r{line}", end="", flush=True, file=sys.stderr)
        else:
            print(rel, file=sys.stderr)

    def finish(self, summary: str):
        if self._is_tty:
            cols = os.get_terminal_size(sys.stderr.fileno()).columns if hasattr(os, "get_terminal_size") else 80
            print(f"\r{' ' * cols}\r{summary}", file=sys.stderr)
        else:
            print(summary, file=sys.stderr)
```

Also add `import os` to the imports at the top of `build.py` (after `import json`).

- [ ] **Step 4: Run the Reporter tests to verify they pass**

```
uv run pytest tests/test_images.py::test_reporter_non_tty_prints_lines tests/test_images.py::test_reporter_non_tty_finish_prints_summary tests/test_images.py::test_reporter_tty_overwrites_line tests/test_images.py::test_reporter_tty_finish_clears_line -v
```

Expected: all four `PASSED`.

- [ ] **Step 5: Run full test suite**

```
uv run pytest -v
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add build.py tests/test_images.py
git commit -m "feat: add Reporter class for TTY/non-TTY progress output"
```

---

### Task 3: Rename generators to task collectors

**Files:**
- Modify: `build.py` — rename `generate_photoblog_images` → `collect_photoblog_tasks`, `generate_gallery_images` → `collect_gallery_tasks`; both return `list[tuple]` instead of writing files
- Modify: `tests/test_images.py` — update all call sites

The functions stop calling `resize_and_save` and instead return a list of `(source, output_path, max_width, fmt)` tuples. The `photo["index"]` assignment moves inside `collect_photoblog_tasks` (it's metadata, not I/O).

- [ ] **Step 1: Write failing tests for the new API**

Add to `tests/test_images.py`:

```python
def test_collect_photoblog_tasks_returns_tuples(tmp_path):
    from tests.helpers import make_test_image
    from build import collect_photoblog_tasks, scan_photoblog, PHOTOBLOG_SIZES, IMAGE_FORMATS
    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "photo.jpg")
    photos = scan_photoblog(src)
    out = tmp_path / "output" / "photoblog" / "photos"
    tasks = collect_photoblog_tasks(photos, out)
    # 1 photo x 3 sizes x 2 formats = 6 tasks
    assert len(tasks) == len(PHOTOBLOG_SIZES) * len(IMAGE_FORMATS)
    source, output_path, max_width, fmt = tasks[0]
    assert source == photos[0]["source"]
    assert isinstance(output_path, Path)
    assert isinstance(max_width, int)
    assert fmt in ("JPEG", "AVIF")


def test_collect_gallery_tasks_returns_tuples(tmp_path):
    from tests.helpers import make_test_image
    from build import collect_gallery_tasks, GALLERY_SIZES, IMAGE_FORMATS
    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "photo.jpg")
    photos = [{"source": src / "photo.jpg", "exif": {}}]
    out = tmp_path / "output" / "gallery" / "test" / "photos"
    tasks = collect_gallery_tasks(photos, out)
    # 1 photo x 4 sizes x 2 formats = 8 tasks
    assert len(tasks) == len(GALLERY_SIZES) * len(IMAGE_FORMATS)
    source, output_path, max_width, fmt = tasks[0]
    assert source == src / "photo.jpg"
    assert isinstance(output_path, Path)
```

- [ ] **Step 2: Run to verify the tests fail**

```
uv run pytest tests/test_images.py::test_collect_photoblog_tasks_returns_tuples tests/test_images.py::test_collect_gallery_tasks_returns_tuples -v
```

Expected: `FAILED` with `ImportError` (functions don't exist yet).

- [ ] **Step 3: Rename and refactor the generators in `build.py`**

Replace `generate_photoblog_images` (lines 180–193) with:

```python
def collect_photoblog_tasks(photos: list[dict], output_dir: Path) -> list[tuple]:
    """Return image tasks for photoblog photos. Sets photo['index'] as a side effect."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks = []
    for i, photo in enumerate(photos, 1):
        index = f"{i:03d}"
        photo["index"] = index
        for size in PHOTOBLOG_SIZES:
            for ext, fmt in IMAGE_FORMATS.items():
                out_path = output_dir / f"{index}-{size}.{ext}"
                tasks.append((photo["source"], out_path, size, fmt))
    return tasks
```

Replace `generate_gallery_images` (lines 195–204) with:

```python
def collect_gallery_tasks(photos: list[dict], output_dir: Path) -> list[tuple]:
    """Return image tasks for gallery photos."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks = []
    for photo in photos:
        stem = photo["source"].stem
        for size in GALLERY_SIZES:
            for ext, fmt in IMAGE_FORMATS.items():
                out_path = output_dir / f"{stem}-{size}.{ext}"
                tasks.append((photo["source"], out_path, size, fmt))
    return tasks
```

- [ ] **Step 4: Update existing tests in `tests/test_images.py` that call the old API**

Replace the four tests that called `generate_photoblog_images` / `generate_gallery_images` with versions that use the new collectors and execute tasks inline:

```python
def test_collect_photoblog_tasks_creates_all_sizes(tmp_path):
    from tests.helpers import make_test_image
    from build import collect_photoblog_tasks, scan_photoblog, resize_and_save
    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "photo.jpg", width=4000, height=3000)
    out = tmp_path / "output" / "photoblog" / "photos"
    photos = scan_photoblog(src)
    tasks = collect_photoblog_tasks(photos, out)
    for task in tasks:
        resize_and_save(*task)
    files = sorted(f.name for f in out.iterdir())
    assert "001-800.avif" in files
    assert "001-800.jpg" in files
    assert "001-1920.avif" in files
    assert "001-1920.jpg" in files
    assert "001-3200.avif" in files
    assert "001-3200.jpg" in files


def test_collect_gallery_tasks_creates_thumbnail_size(tmp_path):
    from tests.helpers import make_test_image
    from build import collect_gallery_tasks, resize_and_save
    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "photo.jpg", width=4000, height=3000)
    out = tmp_path / "output" / "gallery" / "test" / "photos"
    photos = [{"source": src / "photo.jpg", "exif": {}}]
    tasks = collect_gallery_tasks(photos, out)
    for task in tasks:
        resize_and_save(*task)
    files = sorted(f.name for f in out.iterdir())
    assert "photo-400.avif" in files
    assert "photo-400.jpg" in files
    assert "photo-800.avif" in files
    assert "photo-3200.jpg" in files
    assert len(files) == 8


def test_incremental_build_skips_existing(tmp_path):
    from tests.helpers import make_test_image
    from build import collect_photoblog_tasks, scan_photoblog, resize_and_save
    import time
    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "photo.jpg")
    out = tmp_path / "output"
    out.mkdir(parents=True)
    photos = scan_photoblog(src)
    tasks = collect_photoblog_tasks(photos, out)
    for task in tasks:
        resize_and_save(*task)
    first_mtime = (out / "001-800.jpg").stat().st_mtime
    time.sleep(0.1)
    for task in tasks:
        resize_and_save(*task)
    second_mtime = (out / "001-800.jpg").stat().st_mtime
    assert first_mtime == second_mtime


def test_generated_image_dimensions(tmp_path):
    from tests.helpers import make_test_image
    from build import collect_photoblog_tasks, scan_photoblog, resize_and_save
    from PIL import Image
    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "photo.jpg", width=4000, height=3000)
    out = tmp_path / "output"
    photos = scan_photoblog(src)
    tasks = collect_photoblog_tasks(photos, out)
    for task in tasks:
        resize_and_save(*task)
    img = Image.open(out / "001-800.jpg")
    assert img.width == 800
    assert img.height == 600
```

- [ ] **Step 5: Run the full test suite**

```
uv run pytest -v
```

Expected: all pass (including the two new tuple-return tests and the four updated tests).

- [ ] **Step 6: Commit**

```bash
git add build.py tests/test_images.py
git commit -m "refactor: rename generators to collect_*_tasks returning task tuples"
```

---

### Task 4: Add `run_image_tasks` and wire up `build_site`

**Files:**
- Modify: `build.py` — add `run_image_tasks`; update `build_site` to collect all tasks then execute in parallel

`run_image_tasks` takes a flat list of tasks and a `Reporter`, submits them to a `ThreadPoolExecutor`, and calls `reporter.report()` as each future completes. `build_site` collects tasks from `collect_photoblog_tasks` and all `collect_gallery_tasks` calls, then calls `run_image_tasks` once.

- [ ] **Step 1: Write a failing integration test for parallel execution**

Add to `tests/test_build.py`:

```python
def test_full_build_parallel_generates_all_images(tmp_path):
    """Parallel build produces same output as serial build."""
    import shutil
    from tests.helpers import make_test_image
    from build import build_site

    content = tmp_path / "content"
    pb = content / "photoblog"
    pb.mkdir(parents=True)
    make_test_image(pb / "photo1.jpg")
    make_test_image(pb / "photo2.jpg")

    gal = content / "galleries" / "mygal"
    gal.mkdir(parents=True)
    make_test_image(gal / "img1.jpg")
    make_test_image(gal / "img2.jpg")
    make_test_image(gal / "img3.jpg")

    project_root = tmp_path.parent.parent  # get actual project root
    from pathlib import Path
    real_root = Path(__file__).parent.parent
    shutil.copytree(real_root / "templates", tmp_path / "templates")
    shutil.copytree(real_root / "static", tmp_path / "static")

    build_site(tmp_path)

    out = tmp_path / "output"
    pb_photos = out / "photoblog" / "photos"
    # 2 photos x 3 sizes x 2 formats = 12 files
    assert len(list(pb_photos.iterdir())) == 12

    gal_photos = out / "gallery" / "mygal" / "photos"
    # 3 photos x 4 sizes x 2 formats = 24 files
    assert len(list(gal_photos.iterdir())) == 24
```

- [ ] **Step 2: Run to verify it fails (it won't, but confirm current behavior)**

```
uv run pytest tests/test_build.py::test_full_build_parallel_generates_all_images -v
```

This test may already pass (the counts were always produced). That's fine — it will serve as a regression guard after the refactor.

- [ ] **Step 3: Add `run_image_tasks` to `build.py`**

Add this function after `collect_gallery_tasks` and before `make_alt_text`:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed


def run_image_tasks(tasks: list[tuple], reporter: "Reporter"):
    """Execute image resize tasks in parallel using a thread pool."""
    with ThreadPoolExecutor() as pool:
        futures = {pool.submit(resize_and_save, *task): task for task in tasks}
        for future in as_completed(futures):
            path = future.result()  # re-raises any exception
            reporter.report(path)
```

Add `from concurrent.futures import ThreadPoolExecutor, as_completed` to the imports at the top of `build.py`.

- [ ] **Step 4: Update `build_site` to collect all tasks and run them in parallel**

Replace the image-generation section of `build_site` (currently lines 257–275) with:

```python
    # 2. Collect and run image tasks in parallel
    all_tasks: list[tuple] = []

    if photoblog_photos:
        pb_out = output_dir / "photoblog" / "photos"
        all_tasks.extend(collect_photoblog_tasks(photoblog_photos, pb_out))

    for gallery in galleries:
        gallery_out = output_dir / "gallery" / gallery["name"] / "photos"
        all_tasks.extend(collect_gallery_tasks(gallery["photos"], gallery_out))

        cover_path = gallery["cover"]
        if cover_path.stem.lower() == "_cover":
            cover_photos = [{"source": cover_path, "exif": {}}]
            all_tasks.extend(collect_gallery_tasks(cover_photos, gallery_out))

        gallery["cover_stem"] = cover_path.stem

    reporter = Reporter(total=len(all_tasks))
    run_image_tasks(all_tasks, reporter)
```

- [ ] **Step 5: Update the final summary line in `build_site`**

Replace:

```python
    print(f"Build complete: {len(photoblog_photos)} photoblog photos, {len(galleries)} galleries")
```

with:

```python
    reporter.finish(
        f"Build complete: {len(photoblog_photos)} photoblog photos, {len(galleries)} galleries"
    )
```

- [ ] **Step 6: Run the full test suite**

```
uv run pytest -v
```

Expected: all pass.

- [ ] **Step 7: Do a manual smoke test**

```
uv run python build.py
```

If a terminal: verify the status line updates in place without scrolling.
If piped: `uv run python build.py 2>&1 | head -20` — verify file names stream line by line.

- [ ] **Step 8: Commit**

```bash
git add build.py tests/test_build.py
git commit -m "feat: parallel image generation with TTY-aware progress reporting"
```

---

## Self-Review

**Spec coverage:**
- ✅ Parallelize output build — `ThreadPoolExecutor` in `run_image_tasks`
- ✅ Non-scrolling TTY progress — `Reporter` TTY mode with `\r`
- ✅ Line-per-file non-TTY output — `Reporter` non-TTY mode
- ✅ `resize_and_save` returns path — Task 1
- ✅ `Reporter` class — Task 2
- ✅ Task collectors — Task 3
- ✅ `build_site` wired up — Task 4

**Placeholder scan:** None found.

**Type consistency:**
- `collect_photoblog_tasks` / `collect_gallery_tasks` → `list[tuple]` — consistent across Tasks 3 and 4
- `Reporter(total, is_tty)` — same signature in tests (Task 2) and construction (Task 4)
- `resize_and_save(*task)` — matches `(source, output_path, max_width, fmt)` tuple shape defined in Task 3
- `reporter.report(path)` / `reporter.finish(summary)` — consistent across Tasks 2 and 4
