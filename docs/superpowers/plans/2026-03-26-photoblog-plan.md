# fmor.in Photoblog & Gallery — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a static photography website with a slideshow photoblog and grid-based gallery, generated from source photo folders by a Python build script.

**Architecture:** A Python build script (`build.py`) scans content folders, extracts EXIF metadata, generates responsive images (AVIF + JPEG at 3-4 sizes), and renders Jinja2 templates into a static site. The output is pure HTML/CSS/vanilla JS with no runtime dependencies.

**Tech Stack:** Python 3.12+, Pillow (10.1+), Jinja2, exifread, uv for package management

**Spec:** `docs/superpowers/specs/2026-03-26-photoblog-design.md`

---

## File Map

### Build system
| File | Responsibility |
|------|---------------|
| `pyproject.toml` | Project metadata, dependencies (Pillow, Jinja2, exifread) |
| `Makefile` | Build, clean, serve targets |
| `build.py` | Build orchestrator — scans, generates images, renders templates |

### Source content (not committed — user-provided)
| File | Responsibility |
|------|---------------|
| `content/photoblog/*.jpg` | Photoblog source photos |
| `content/galleries/<name>/*.jpg` | Gallery source photos per folder |

### Templates
| File | Responsibility |
|------|---------------|
| `templates/base.html` | Shared HTML shell: doctype, head (meta, OG, favicon, CSS), header, content block, JS |
| `templates/photoblog.html` | Slideshow: single photo view, EXIF bar, photo manifest JSON, nav zones |
| `templates/gallery_index.html` | Grid of gallery cover cards |
| `templates/gallery.html` | Thumbnail grid + lightbox overlay for a single gallery |
| `templates/partials/exif.html` | Reusable EXIF metadata block |
| `templates/index.html` | Meta-refresh redirect to /photoblog/ |

### Static assets
| File | Responsibility |
|------|---------------|
| `static/css/style.css` | All styling: dark theme, header, slideshow layout, grid, lightbox, EXIF bar, responsive breakpoints |
| `static/js/main.js` | All JS: slideshow navigation, lightbox, keyboard/hover/touch/swipe, hash routing, preloading |

### Tests
| File | Responsibility |
|------|---------------|
| `tests/__init__.py` | Makes tests a package for imports |
| `tests/conftest.py` | Shared fixtures: temp content dirs, sample images |
| `tests/helpers.py` | Shared test utilities: `make_test_image()` |
| `tests/test_scanner.py` | Tests for folder scanning, EXIF extraction, sort order |
| `tests/test_images.py` | Tests for responsive image generation |
| `tests/test_build.py` | Integration tests for full build pipeline |

---

## Task 1: Project scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `Makefile`
- Create: `.gitignore`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "fmor-in"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "Pillow>=10.1",
    "Jinja2>=3.1",
    "exifread>=3.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]
```

- [ ] **Step 2: Create Makefile**

```makefile
.PHONY: build clean serve

build:
	uv run python build.py

clean:
	rm -rf output

serve: build
	cd output && python -m http.server 8000
```

- [ ] **Step 3: Create .gitignore**

```
output/
content/
__pycache__/
*.pyc
.venv/
.superpowers/
```

- [ ] **Step 4: Create content directory structure with test photos**

```bash
mkdir -p content/photoblog content/galleries/sample
```

Use Pillow to create 2-3 small test JPEGs for development (no EXIF — the build handles missing EXIF gracefully by hiding the EXIF bar):

```bash
uv run python -c "
from PIL import Image
for i in range(3):
    img = Image.new('RGB', (4000, 3000), color=(i*80, 100, 150))
    img.save(f'content/photoblog/test-{i+1:03d}.jpg')
    img.save(f'content/galleries/sample/test-{i+1:03d}.jpg')
"
```

- [ ] **Step 5: Install dependencies**

```bash
uv sync
```

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml Makefile .gitignore
git commit -m "feat: project scaffolding with dependencies and Makefile"
```

Do NOT commit `content/` — these are test files for local development only.

---

## Task 2: Content scanner and EXIF extraction

**Files:**
- Create: `build.py` (initial version — scanner module only)
- Create: `tests/__init__.py`
- Create: `tests/helpers.py`
- Create: `tests/conftest.py`
- Create: `tests/test_scanner.py`

This task implements the `scan_content()` function that walks the content folders, extracts EXIF metadata, and returns structured photo manifests.

- [ ] **Step 1: Create tests/__init__.py, tests/helpers.py, and tests/conftest.py**

```python
# tests/__init__.py
# (empty — makes tests a package)
```

```python
# tests/helpers.py
from pathlib import Path
from PIL import Image


def make_test_image(path, width=4000, height=3000, color=(100, 100, 100)):
    """Create a test JPEG image. Images smaller than a target resize are not upscaled."""
    img = Image.new("RGB", (width, height), color=color)
    img.save(path, "JPEG")
    return path
```

```python
# tests/conftest.py
import pytest
from pathlib import Path


@pytest.fixture
def tmp_content(tmp_path):
    """Create a temporary content directory with test photos."""
    photoblog = tmp_path / "content" / "photoblog"
    photoblog.mkdir(parents=True)

    galleries = tmp_path / "content" / "galleries"
    (galleries / "alpha").mkdir(parents=True)
    (galleries / "beta").mkdir(parents=True)

    return tmp_path / "content"
```

- [ ] **Step 2: Write failing tests for scan_photoblog**

```python
# tests/test_scanner.py
from pathlib import Path
from tests.helpers import make_test_image


def test_scan_photoblog_finds_accepted_formats(tmp_content):
    pb = tmp_content / "photoblog"
    make_test_image(pb / "photo1.jpg")
    make_test_image(pb / "photo2.jpeg")
    make_test_image(pb / "photo3.png")
    (pb / "readme.txt").write_text("ignore me")

    from build import scan_photoblog
    photos = scan_photoblog(pb)
    assert len(photos) == 3
    assert all(p["source"].suffix in (".jpg", ".jpeg", ".png") for p in photos)


def test_scan_photoblog_sorted_by_filename_without_exif(tmp_content):
    pb = tmp_content / "photoblog"
    make_test_image(pb / "c-photo.jpg")
    make_test_image(pb / "a-photo.jpg")
    make_test_image(pb / "b-photo.jpg")

    from build import scan_photoblog
    photos = scan_photoblog(pb)
    # Without EXIF dates, falls back to filename sort
    stems = [p["source"].stem for p in photos]
    assert stems == ["a-photo", "b-photo", "c-photo"]


def test_scan_photoblog_empty_folder_returns_empty(tmp_content):
    pb = tmp_content / "photoblog"
    from build import scan_photoblog
    photos = scan_photoblog(pb)
    assert photos == []


def test_scan_galleries_finds_subfolders(tmp_content):
    make_test_image(tmp_content / "galleries" / "alpha" / "img1.jpg")
    make_test_image(tmp_content / "galleries" / "beta" / "img1.jpg")

    from build import scan_galleries
    galleries = scan_galleries(tmp_content / "galleries")
    assert len(galleries) == 2
    assert galleries[0]["name"] == "alpha"  # alphabetical
    assert galleries[1]["name"] == "beta"


def test_scan_galleries_skips_empty_folders(tmp_content, capsys):
    make_test_image(tmp_content / "galleries" / "alpha" / "img1.jpg")
    # beta is empty

    from build import scan_galleries
    galleries = scan_galleries(tmp_content / "galleries")
    assert len(galleries) == 1
    assert galleries[0]["name"] == "alpha"
    assert "beta" in capsys.readouterr().err  # warning on stderr


def test_scan_galleries_cover_override(tmp_content):
    make_test_image(tmp_content / "galleries" / "alpha" / "img1.jpg")
    make_test_image(tmp_content / "galleries" / "alpha" / "_cover.jpg")

    from build import scan_galleries
    galleries = scan_galleries(tmp_content / "galleries")
    assert galleries[0]["cover"].name == "_cover.jpg"
    # _cover should be excluded from photo list
    assert all(p["source"].stem != "_cover" for p in galleries[0]["photos"])


def test_scan_galleries_stem_collision_fails(tmp_content):
    make_test_image(tmp_content / "galleries" / "alpha" / "sunset.jpg")
    make_test_image(tmp_content / "galleries" / "alpha" / "sunset.png")

    from build import scan_galleries
    import pytest
    with pytest.raises(ValueError, match="stem collision"):
        scan_galleries(tmp_content / "galleries")
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
uv run python -m pytest tests/test_scanner.py -v
```

Expected: all tests FAIL with `ImportError` (build module doesn't have these functions yet).

- [ ] **Step 4: Implement scan_photoblog and scan_galleries in build.py**

```python
#!/usr/bin/env python3
"""Static site builder for fmor.in photoblog and gallery."""

import sys
from pathlib import Path

import exifread

ACCEPTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff"}


def extract_exif(photo_path: Path) -> dict:
    """Extract EXIF metadata from a photo. Returns dict of display fields."""
    try:
        with open(photo_path, "rb") as f:
            tags = exifread.process_file(f, details=False)
    except Exception:
        return {}

    def get(key):
        tag = tags.get(key)
        return str(tag) if tag else None

    exif = {}
    field_map = {
        "camera": "Image Model",
        "make": "Image Make",
        "lens": "EXIF LensModel",
        "focal_length": "EXIF FocalLength",
        "aperture": "EXIF FNumber",
        "shutter_speed": "EXIF ExposureTime",
        "iso": "EXIF ISOSpeedRatings",
        "date": "EXIF DateTimeOriginal",
        "white_balance": "EXIF WhiteBalance",
        "metering": "EXIF MeteringMode",
        "exposure_comp": "EXIF ExposureBiasValue",
    }
    for field, tag_name in field_map.items():
        value = get(tag_name)
        if value:
            exif[field] = value

    return exif


def get_sort_key(photo: dict) -> tuple:
    """Sort key: EXIF date (newest first), then filename ascending as tiebreaker.

    Returns a tuple that sorts correctly with a single ascending sort:
    - Photos with dates come before photos without dates
    - Dates are inverted so newest sorts first in ascending order
    - Filename is ascending for tiebreaking
    """
    from datetime import datetime

    date = photo.get("exif", {}).get("date", "")
    if not date:
        try:
            mtime = photo["source"].stat().st_mtime
            date = datetime.fromtimestamp(mtime).strftime("%Y:%m:%d %H:%M:%S")
        except OSError:
            date = ""

    # Invert date characters for newest-first in ascending sort
    # ord max for printable ASCII is ~126, so subtract from 126
    inverted_date = "".join(chr(126 - ord(c)) for c in date) if date else ""

    # (no_date sorts last, inverted_date for newest-first, filename ascending)
    return (not bool(date), inverted_date, photo["source"].name)


def scan_photoblog(photoblog_dir: Path) -> list[dict]:
    """Scan photoblog folder and return sorted list of photo dicts."""
    if not photoblog_dir.exists():
        return []

    photos = []
    for f in sorted(photoblog_dir.iterdir()):
        if f.is_file() and f.suffix.lower() in ACCEPTED_EXTENSIONS:
            photos.append({
                "source": f,
                "exif": extract_exif(f),
            })

    photos.sort(key=get_sort_key)
    return photos


def scan_galleries(galleries_dir: Path) -> list[dict]:
    """Scan gallery folders and return sorted list of gallery dicts."""
    if not galleries_dir.exists():
        return []

    galleries = []
    for folder in sorted(galleries_dir.iterdir()):
        if not folder.is_dir():
            continue

        cover = None
        photos = []
        stems_seen = {}

        for f in sorted(folder.iterdir()):
            if not f.is_file() or f.suffix.lower() not in ACCEPTED_EXTENSIONS:
                continue

            if f.stem.lower() == "_cover":
                cover = f
                continue

            stem_lower = f.stem.lower()
            if stem_lower in stems_seen:
                raise ValueError(
                    f"stem collision in gallery '{folder.name}': "
                    f"'{stems_seen[stem_lower].name}' and '{f.name}'"
                )
            stems_seen[stem_lower] = f

            photos.append({
                "source": f,
                "exif": extract_exif(f),
            })

        if not photos:
            print(f"Warning: gallery '{folder.name}' is empty, skipping", file=sys.stderr)
            continue

        photos.sort(key=get_sort_key)

        if cover is None:
            cover = photos[0]["source"]

        galleries.append({
            "name": folder.name,
            "path": folder,
            "cover": cover,
            "photos": photos,
            "count": len(photos),
        })

    return galleries
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run python -m pytest tests/test_scanner.py -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add build.py tests/__init__.py tests/helpers.py tests/conftest.py tests/test_scanner.py
git commit -m "feat: content scanner with EXIF extraction and gallery support"
```

---

## Task 3: Responsive image generation

**Files:**
- Modify: `build.py` (add `generate_images()`)
- Create: `tests/test_images.py`

- [ ] **Step 1: Write failing tests for image generation**

```python
# tests/test_images.py
from pathlib import Path
from tests.helpers import make_test_image


def test_generate_photoblog_images_creates_all_sizes(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "photo.jpg", width=4000, height=3000)

    out = tmp_path / "output" / "photoblog" / "photos"

    from build import generate_photoblog_images, scan_photoblog
    photos = scan_photoblog(src)
    generate_photoblog_images(photos, out)

    # 3 sizes x 2 formats = 6 files
    files = sorted(f.name for f in out.iterdir())
    assert "001-800.avif" in files
    assert "001-800.jpg" in files
    assert "001-1920.avif" in files
    assert "001-1920.jpg" in files
    assert "001-3200.avif" in files
    assert "001-3200.jpg" in files


def test_generate_gallery_images_creates_thumbnail_size(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "photo.jpg", width=4000, height=3000)

    out = tmp_path / "output" / "gallery" / "test" / "photos"

    from build import generate_gallery_images
    photos = [{"source": src / "photo.jpg", "exif": {}}]
    generate_gallery_images(photos, out)

    files = sorted(f.name for f in out.iterdir())
    # 4 sizes x 2 formats = 8 files
    assert "photo-400.avif" in files
    assert "photo-400.jpg" in files
    assert "photo-800.avif" in files
    assert "photo-3200.jpg" in files
    assert len(files) == 8


def test_incremental_build_skips_existing(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "photo.jpg")

    out = tmp_path / "output"
    out.mkdir(parents=True)

    from build import generate_photoblog_images, scan_photoblog
    photos = scan_photoblog(src)

    generate_photoblog_images(photos, out)
    first_mtime = (out / "001-800.jpg").stat().st_mtime

    # Run again — should skip
    import time; time.sleep(0.1)
    generate_photoblog_images(photos, out)
    second_mtime = (out / "001-800.jpg").stat().st_mtime

    assert first_mtime == second_mtime


def test_generated_image_dimensions(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "photo.jpg", width=4000, height=3000)

    out = tmp_path / "output"

    from build import generate_photoblog_images, scan_photoblog
    from PIL import Image
    photos = scan_photoblog(src)
    generate_photoblog_images(photos, out)

    img = Image.open(out / "001-800.jpg")
    assert img.width == 800
    assert img.height == 600  # 4:3 aspect preserved
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run python -m pytest tests/test_images.py -v
```

Expected: FAIL with `ImportError`.

- [ ] **Step 3: Implement image generation in build.py**

Add these functions to `build.py`:

```python
from PIL import Image

PHOTOBLOG_SIZES = [800, 1920, 3200]
GALLERY_SIZES = [400, 800, 1920, 3200]
IMAGE_FORMATS = {"avif": "AVIF", "jpg": "JPEG"}


def resize_and_save(source: Path, output_path: Path, max_width: int, fmt: str):
    """Resize image to max_width (preserving aspect ratio) and save."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Skip if output is newer than source
    if output_path.exists() and output_path.stat().st_mtime > source.stat().st_mtime:
        return

    with Image.open(source) as img:
        if img.width > max_width:
            ratio = max_width / img.width
            new_height = int(img.height * ratio)
            img = img.resize((max_width, new_height), Image.LANCZOS)

        # Convert to RGB if necessary (e.g., RGBA PNGs)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

        save_kwargs = {}
        if fmt == "JPEG":
            save_kwargs["quality"] = 85
            save_kwargs["optimize"] = True
        elif fmt == "AVIF":
            save_kwargs["quality"] = 65

        img.save(output_path, fmt, **save_kwargs)


def generate_photoblog_images(photos: list[dict], output_dir: Path):
    """Generate responsive images for photoblog photos."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, photo in enumerate(photos, 1):
        index = f"{i:03d}"
        for size in PHOTOBLOG_SIZES:
            for ext, fmt in IMAGE_FORMATS.items():
                out_path = output_dir / f"{index}-{size}.{ext}"
                resize_and_save(photo["source"], out_path, size, fmt)

        # Store output paths for template rendering
        photo["index"] = index


def generate_gallery_images(photos: list[dict], output_dir: Path):
    """Generate responsive images for gallery photos (includes 400px thumbnail)."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for photo in photos:
        stem = photo["source"].stem
        for size in GALLERY_SIZES:
            for ext, fmt in IMAGE_FORMATS.items():
                out_path = output_dir / f"{stem}-{size}.{ext}"
                resize_and_save(photo["source"], out_path, size, fmt)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run python -m pytest tests/test_images.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add build.py tests/test_images.py
git commit -m "feat: responsive image generation with AVIF/JPEG and incremental builds"
```

---

## Task 4: Jinja2 templates — base layout, header, and landing page

**Files:**
- Create: `templates/base.html`
- Create: `templates/partials/exif.html`
- Create: `templates/index.html`

- [ ] **Step 1: Create templates/base.html**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}fmor.in{% endblock %}</title>
    <link rel="icon" href="/static/favicon.ico" type="image/x-icon">
    <link rel="stylesheet" href="/static/css/style.css">
    <meta property="og:title" content="{% block og_title %}fmor.in{% endblock %}">
    <meta property="og:type" content="website">
    {% block og_image %}{% endblock %}
    {% block head_extra %}{% endblock %}
</head>
<body>
    <header class="site-header">
        <a href="/" class="site-name">fmor.in</a>
        <nav class="site-nav">
            <a href="/photoblog/" class="{% if section == 'photoblog' %}active{% endif %}" aria-label="Photoblog">Photoblog</a>
            <a href="/gallery/" class="{% if section == 'gallery' %}active{% endif %}" aria-label="Gallery">Gallery</a>
        </nav>
    </header>
    <main>
        {% block content %}{% endblock %}
    </main>
    <script src="/static/js/main.js"></script>
</body>
</html>
```

- [ ] **Step 2: Create templates/partials/exif.html**

```html
{# Expects: exif (dict), photo_date (string|None) #}
{% if exif %}
<div class="exif-bar">
    {% if photo_date %}<span class="exif-date">{{ photo_date }}</span>{% endif %}
    <span class="exif-fields">
        {% set fields = [] %}
        {% if exif.camera %}{% set _ = fields.append(exif.camera) %}{% endif %}
        {% if exif.lens %}{% set _ = fields.append(exif.lens) %}{% endif %}
        {% if exif.focal_length %}{% set _ = fields.append(exif.focal_length + "mm") %}{% endif %}
        {% if exif.aperture %}{% set _ = fields.append("ƒ/" + exif.aperture) %}{% endif %}
        {% if exif.shutter_speed %}{% set _ = fields.append(exif.shutter_speed + "s") %}{% endif %}
        {% if exif.iso %}{% set _ = fields.append("ISO " + exif.iso) %}{% endif %}
        {% if exif.white_balance %}{% set _ = fields.append(exif.white_balance) %}{% endif %}
        {% if exif.metering %}{% set _ = fields.append(exif.metering) %}{% endif %}
        {% if exif.exposure_comp %}{% set _ = fields.append(exif.exposure_comp + " EV") %}{% endif %}
        {{ fields | join(" · ") }}
    </span>
</div>
{% endif %}
```

- [ ] **Step 3: Create templates/index.html (landing redirect)**

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0;url=/photoblog/">
    <title>fmor.in</title>
</head>
<body></body>
</html>
```

- [ ] **Step 4: Commit**

```bash
git add templates/
git commit -m "feat: base template with header, EXIF partial, and landing redirect"
```

---

## Task 5: CSS — dark theme, header, EXIF bar, responsive grid

**Files:**
- Create: `static/css/style.css`

- [ ] **Step 1: Create static/css/style.css**

```css
/* === Reset & Base === */
*, *::before, *::after {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

html, body {
    height: 100%;
    background: #111;
    color: #ccc;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 14px;
    line-height: 1.4;
}

a {
    color: inherit;
    text-decoration: none;
}

/* === Header === */
.site-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 40px;
    background: #111;
    border-bottom: 1px solid #2a2a2a;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 20px;
    z-index: 100;
}

.site-name {
    font-size: 14px;
    font-weight: 600;
    color: #ccc;
    letter-spacing: 1px;
}

.site-nav {
    display: flex;
    gap: 24px;
}

.site-nav a {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #777;
    padding-bottom: 2px;
}

.site-nav a.active {
    color: #fff;
    border-bottom: 1px solid #fff;
}

.site-nav a:hover {
    color: #aaa;
}

.site-nav a:focus-visible {
    outline: 1px solid #fff;
    outline-offset: 4px;
}

/* === Main content push below header === */
main {
    padding-top: 40px;
}

/* === Slideshow (Photoblog) === */
.slideshow {
    height: calc(100vh - 40px);
    display: flex;
    flex-direction: column;
    background: #111;
    position: relative;
}

.slideshow-photo {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    overflow: hidden;
}

.slideshow-photo picture {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
}

.slideshow-photo img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
}

.slideshow-photo img:focus-visible {
    outline: none;
}

/* Nav hover zones */
.nav-zone {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 20%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    z-index: 10;
    opacity: 0;
    transition: opacity 0.2s;
}

.nav-zone:hover {
    opacity: 1;
}

.nav-zone:focus-visible {
    opacity: 1;
    outline: 1px solid #fff;
    outline-offset: -4px;
}

.nav-zone--prev {
    left: 0;
}

.nav-zone--next {
    right: 0;
}

.nav-zone .arrow {
    color: rgba(255, 255, 255, 0.6);
    font-size: 48px;
    user-select: none;
}

/* Photo counter */
.photo-counter {
    position: absolute;
    top: 12px;
    right: 20px;
    color: #555;
    font-size: 11px;
    z-index: 5;
}

/* === EXIF Bar === */
.exif-bar {
    background: #111;
    border-top: 1px solid #2a2a2a;
    padding: 6px 20px;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 6px;
    flex-shrink: 0;
}

.exif-date {
    color: #555;
    font-size: 10px;
    margin-right: auto;
}

.exif-fields {
    color: #666;
    font-size: 10px;
}

/* === Gallery Index === */
.gallery-grid {
    padding: 24px;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
}

.gallery-card {
    aspect-ratio: 4/3;
    border-radius: 3px;
    overflow: hidden;
    position: relative;
    cursor: pointer;
}

.gallery-card img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.gallery-card-info {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(transparent, rgba(0,0,0,0.7));
    padding: 24px 14px 10px;
}

.gallery-card-name {
    color: #eee;
    font-size: 13px;
    font-weight: 500;
}

.gallery-card-count {
    color: #888;
    font-size: 10px;
    margin-top: 2px;
}

/* === Gallery Page (thumbnails) === */
.gallery-header {
    padding: 16px 24px 8px;
    display: flex;
    align-items: center;
    gap: 12px;
}

.gallery-back {
    color: #666;
    font-size: 13px;
}

.gallery-back:hover {
    color: #aaa;
}

.gallery-back:focus-visible {
    outline: 1px solid #fff;
    outline-offset: 2px;
}

.gallery-title {
    color: #ccc;
    font-size: 15px;
    font-weight: 500;
}

.gallery-sep {
    color: #444;
}

.thumbnail-grid {
    padding: 8px 24px 24px;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
}

.thumbnail {
    aspect-ratio: 1;
    border-radius: 2px;
    overflow: hidden;
    cursor: pointer;
}

.thumbnail img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.thumbnail:focus-visible {
    outline: 2px solid #fff;
    outline-offset: 2px;
}

/* === Lightbox === */
.lightbox {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.95);
    z-index: 200;
    display: none;
    flex-direction: column;
}

.lightbox.open {
    display: flex;
}

.lightbox-close {
    position: absolute;
    top: 12px;
    right: 20px;
    z-index: 210;
    color: #666;
    font-size: 20px;
    cursor: pointer;
    background: none;
    border: none;
    font-family: inherit;
}

.lightbox-close:hover {
    color: #aaa;
}

.lightbox-close:focus-visible {
    outline: 1px solid #fff;
    outline-offset: 4px;
}

.lightbox-photo {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
}

.lightbox-photo picture {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
}

.lightbox-photo img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
}

.lightbox .exif-bar {
    background: rgba(17, 17, 17, 0.9);
}

/* === Responsive === */
@media (min-width: 768px) {
    .gallery-grid {
        grid-template-columns: repeat(3, 1fr);
    }
    .thumbnail-grid {
        grid-template-columns: repeat(3, 1fr);
    }
}

@media (min-width: 1200px) {
    .thumbnail-grid {
        grid-template-columns: repeat(4, 1fr);
    }
}

@media (max-width: 767px) {
    .site-header {
        height: auto;
        flex-wrap: wrap;
        padding: 8px 16px;
        gap: 4px;
    }
    main {
        padding-top: 60px;
    }
    .slideshow {
        height: calc(100vh - 60px);
    }
}

/* === Reduced motion === */
@media (prefers-reduced-motion: reduce) {
    .nav-zone {
        transition: none;
    }
}
```

- [ ] **Step 2: Commit**

```bash
git add static/
git commit -m "feat: dark theme CSS with header, slideshow, grid, lightbox, and responsive breakpoints"
```

---

## Task 6: Photoblog template

**Files:**
- Create: `templates/photoblog.html`

- [ ] **Step 1: Create templates/photoblog.html**

```html
{% extends "base.html" %}

{% block title %}Photoblog — fmor.in{% endblock %}
{% block og_title %}Photoblog — fmor.in{% endblock %}
{% block og_image %}
{% if photos %}
<meta property="og:image" content="/photoblog/photos/{{ photos[0].index }}-1920.jpg">
{% endif %}
{% endblock %}

{% block head_extra %}
<script>
    window.PHOTOS = {{ photos_json | safe }};
</script>
{% endblock %}

{% block content %}
<div class="slideshow" id="slideshow" data-section="photoblog">
    <div class="slideshow-photo">
        <div class="nav-zone nav-zone--prev" onclick="navigatePhoto(-1)" role="button" aria-label="Previous photo" tabindex="0">
            <span class="arrow">‹</span>
        </div>

        <picture id="photo-picture">
            {# Populated by JS from PHOTOS manifest #}
        </picture>

        <div class="nav-zone nav-zone--next" onclick="navigatePhoto(1)" role="button" aria-label="Next photo" tabindex="0">
            <span class="arrow">›</span>
        </div>

        <div class="photo-counter" id="photo-counter"></div>
    </div>

    <div id="exif-container"></div>
</div>
{% endblock %}
```

- [ ] **Step 2: Commit**

```bash
git add templates/photoblog.html
git commit -m "feat: photoblog slideshow template with JSON manifest and nav zones"
```

---

## Task 7: Gallery templates

**Files:**
- Create: `templates/gallery_index.html`
- Create: `templates/gallery.html`

- [ ] **Step 1: Create templates/gallery_index.html**

```html
{% extends "base.html" %}

{% block title %}Gallery — fmor.in{% endblock %}
{% block og_title %}Gallery — fmor.in{% endblock %}
{% block og_image %}
{% if galleries %}
<meta property="og:image" content="/gallery/{{ galleries[0].name }}/photos/{{ galleries[0].cover_stem }}-1920.jpg">
{% endif %}
{% endblock %}

{% block content %}
<div class="gallery-grid">
    {% for gallery in galleries %}
    <a href="/gallery/{{ gallery.name }}/" class="gallery-card">
        <picture>
            <source type="image/avif"
                srcset="/gallery/{{ gallery.name }}/photos/{{ gallery.cover_stem }}-400.avif 400w, /gallery/{{ gallery.name }}/photos/{{ gallery.cover_stem }}-800.avif 800w, /gallery/{{ gallery.name }}/photos/{{ gallery.cover_stem }}-1920.avif 1920w"
                sizes="(max-width: 768px) 50vw, 33vw">
            <img
                src="/gallery/{{ gallery.name }}/photos/{{ gallery.cover_stem }}-800.jpg"
                srcset="/gallery/{{ gallery.name }}/photos/{{ gallery.cover_stem }}-400.jpg 400w, /gallery/{{ gallery.name }}/photos/{{ gallery.cover_stem }}-800.jpg 800w, /gallery/{{ gallery.name }}/photos/{{ gallery.cover_stem }}-1920.jpg 1920w"
                sizes="(max-width: 768px) 50vw, 33vw"
                alt="{{ gallery.name | replace('_', ' ') | replace('-', ' ') }}"
                loading="lazy">
        </picture>
        <div class="gallery-card-info">
            <div class="gallery-card-name">{{ gallery.name | replace('_', ' ') | replace('-', ' ') | title }}</div>
            <div class="gallery-card-count">{{ gallery.count }} photo{{ 's' if gallery.count != 1 }}</div>
        </div>
    </a>
    {% endfor %}
</div>
{% endblock %}
```

- [ ] **Step 2: Create templates/gallery.html**

```html
{% extends "base.html" %}

{% block title %}{{ gallery_name | replace('_', ' ') | replace('-', ' ') | title }} — fmor.in{% endblock %}
{% block og_title %}{{ gallery_name | replace('_', ' ') | replace('-', ' ') | title }} — fmor.in{% endblock %}
{% block og_image %}
{% if photos %}
<meta property="og:image" content="/gallery/{{ gallery_name }}/photos/{{ photos[0].stem }}-1920.jpg">
{% endif %}
{% endblock %}

{% block head_extra %}
<script>
    window.GALLERY_PHOTOS = {{ photos_json | safe }};
</script>
{% endblock %}

{% block content %}
<div class="gallery-header">
    <a href="/gallery/" class="gallery-back" aria-label="Back to galleries">← Galleries</a>
    <span class="gallery-sep">·</span>
    <h1 class="gallery-title">{{ gallery_name | replace('_', ' ') | replace('-', ' ') | title }}</h1>
</div>

<div class="thumbnail-grid">
    {% for photo in photos %}
    <div class="thumbnail" data-index="{{ loop.index0 }}" onclick="openLightbox({{ loop.index0 }})" role="button" aria-label="View {{ photo.alt }}" tabindex="0">
        <picture>
            <source type="image/avif"
                srcset="/gallery/{{ gallery_name }}/photos/{{ photo.stem }}-400.avif 400w, /gallery/{{ gallery_name }}/photos/{{ photo.stem }}-800.avif 800w"
                sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw">
            <img
                src="/gallery/{{ gallery_name }}/photos/{{ photo.stem }}-400.jpg"
                srcset="/gallery/{{ gallery_name }}/photos/{{ photo.stem }}-400.jpg 400w, /gallery/{{ gallery_name }}/photos/{{ photo.stem }}-800.jpg 800w"
                sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw"
                alt="{{ photo.alt }}"
                loading="lazy">
        </picture>
    </div>
    {% endfor %}
</div>

<!-- Lightbox -->
<div class="lightbox" id="lightbox" role="dialog" aria-label="Photo viewer" aria-modal="true">
    <button class="lightbox-close" onclick="closeLightbox()" aria-label="Close lightbox">✕</button>

    <div class="lightbox-photo">
        <div class="nav-zone nav-zone--prev" onclick="navigateLightbox(-1)" role="button" aria-label="Previous photo" tabindex="0">
            <span class="arrow">‹</span>
        </div>

        <picture id="lightbox-picture"></picture>

        <div class="nav-zone nav-zone--next" onclick="navigateLightbox(1)" role="button" aria-label="Next photo" tabindex="0">
            <span class="arrow">›</span>
        </div>

        <div class="photo-counter" id="lightbox-counter"></div>
    </div>

    <div id="lightbox-exif"></div>
</div>
{% endblock %}
```

- [ ] **Step 3: Commit**

```bash
git add templates/gallery_index.html templates/gallery.html
git commit -m "feat: gallery index and gallery page templates with lightbox"
```

---

## Task 8: JavaScript — slideshow, lightbox, navigation

**Files:**
- Create: `static/js/main.js`

- [ ] **Step 1: Create static/js/main.js**

```javascript
/* fmor.in — slideshow & lightbox navigation */
(function () {
    "use strict";

    // --- Shared utilities ---

    function buildPicture(photo, sizes) {
        var avifSrcset = photo.sizes.map(function (s) {
            return photo.base + "-" + s + ".avif " + s + "w";
        }).join(", ");
        var jpgSrcset = photo.sizes.map(function (s) {
            return photo.base + "-" + s + ".jpg " + s + "w";
        }).join(", ");

        // Find the 1920 size for fallback, or use the middle size
        var fallbackSize = photo.sizes.indexOf(1920) !== -1 ? 1920 : photo.sizes[Math.floor(photo.sizes.length / 2)];
        return '<source type="image/avif" srcset="' + avifSrcset + '" sizes="' + sizes + '">' +
            '<img src="' + photo.base + '-' + fallbackSize + '.jpg"' +
            ' srcset="' + jpgSrcset + '"' +
            ' sizes="' + sizes + '"' +
            ' alt="' + (photo.alt || "") + '">';
    }

    function buildExif(exif, date) {
        if (!exif || Object.keys(exif).length === 0) return "";
        var fields = [];
        if (exif.camera) fields.push(exif.camera);
        if (exif.lens) fields.push(exif.lens);
        if (exif.focal_length) fields.push(exif.focal_length + "mm");
        if (exif.aperture) fields.push("\u0192/" + exif.aperture);
        if (exif.shutter_speed) fields.push(exif.shutter_speed + "s");
        if (exif.iso) fields.push("ISO " + exif.iso);
        if (exif.white_balance) fields.push(exif.white_balance);
        if (exif.metering) fields.push(exif.metering);
        if (exif.exposure_comp) fields.push(exif.exposure_comp + " EV");

        var html = '<div class="exif-bar">';
        if (date) html += '<span class="exif-date">' + date + '</span>';
        html += '<span class="exif-fields">' + fields.join(" \u00b7 ") + '</span>';
        html += '</div>';
        return html;
    }

    function preloadImage(src) {
        var img = new Image();
        img.src = src;
    }

    // --- Slideshow (Photoblog) ---

    var slideshowIndex = 0;

    function initSlideshow() {
        if (!window.PHOTOS || window.PHOTOS.length === 0) return;

        var hash = parseInt(location.hash.replace("#", ""), 10);
        if (hash > 0 && hash <= window.PHOTOS.length) {
            slideshowIndex = hash - 1;
        }

        showSlide(slideshowIndex);

        window.addEventListener("hashchange", function () {
            var h = parseInt(location.hash.replace("#", ""), 10);
            if (h > 0 && h <= window.PHOTOS.length) {
                slideshowIndex = h - 1;
                showSlide(slideshowIndex);
            }
        });
    }

    function showSlide(index) {
        var photos = window.PHOTOS;
        if (!photos || index < 0 || index >= photos.length) return;

        slideshowIndex = index;
        var photo = photos[index];

        var picture = document.getElementById("photo-picture");
        if (picture) picture.innerHTML = buildPicture(photo, "100vw");

        var counter = document.getElementById("photo-counter");
        if (counter) counter.textContent = (index + 1) + " / " + photos.length;

        var exifEl = document.getElementById("exif-container");
        if (exifEl) exifEl.innerHTML = buildExif(photo.exif, photo.date);

        location.hash = "#" + (index + 1);

        // Preload adjacent
        if (index > 0) preloadImage(photos[index - 1].base + "-1920.jpg");
        if (index < photos.length - 1) preloadImage(photos[index + 1].base + "-1920.jpg");
    }

    window.navigatePhoto = function (delta) {
        var photos = window.PHOTOS;
        if (!photos) return;
        var next = slideshowIndex + delta;
        if (next >= 0 && next < photos.length) showSlide(next);
    };

    // --- Lightbox (Gallery) ---

    var lightboxIndex = 0;
    var lightboxOpen = false;
    var previousFocus = null;

    window.openLightbox = function (index) {
        if (!window.GALLERY_PHOTOS) return;
        previousFocus = document.activeElement;
        lightboxIndex = index;
        lightboxOpen = true;
        document.body.style.overflow = "hidden";

        var lb = document.getElementById("lightbox");
        if (lb) lb.classList.add("open");

        showLightboxPhoto(index);

        // Focus the close button for accessibility
        var closeBtn = document.querySelector(".lightbox-close");
        if (closeBtn) closeBtn.focus();
    };

    window.closeLightbox = function () {
        lightboxOpen = false;
        document.body.style.overflow = "";

        var lb = document.getElementById("lightbox");
        if (lb) lb.classList.remove("open");

        location.hash = "";

        if (previousFocus) previousFocus.focus();
    };

    window.navigateLightbox = function (delta) {
        var photos = window.GALLERY_PHOTOS;
        if (!photos) return;
        var next = lightboxIndex + delta;
        if (next >= 0 && next < photos.length) showLightboxPhoto(next);
    };

    function showLightboxPhoto(index) {
        var photos = window.GALLERY_PHOTOS;
        if (!photos || index < 0 || index >= photos.length) return;

        lightboxIndex = index;
        var photo = photos[index];

        var picture = document.getElementById("lightbox-picture");
        if (picture) picture.innerHTML = buildPicture(photo, "100vw");

        var counter = document.getElementById("lightbox-counter");
        if (counter) counter.textContent = (index + 1) + " / " + photos.length;

        var exifEl = document.getElementById("lightbox-exif");
        if (exifEl) exifEl.innerHTML = buildExif(photo.exif, photo.date);

        location.hash = "#" + (index + 1);

        // Preload adjacent
        if (index > 0) preloadImage(photos[index - 1].base + "-1920.jpg");
        if (index < photos.length - 1) preloadImage(photos[index + 1].base + "-1920.jpg");
    }

    // --- Focus trap for lightbox ---

    function trapFocus(e) {
        if (!lightboxOpen) return;
        if (e.key !== "Tab") return;

        var lb = document.getElementById("lightbox");
        var focusable = lb.querySelectorAll('button, [role="button"][tabindex="0"]');
        if (focusable.length === 0) return;

        var first = focusable[0];
        var last = focusable[focusable.length - 1];

        if (e.shiftKey) {
            if (document.activeElement === first) {
                e.preventDefault();
                last.focus();
            }
        } else {
            if (document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        }
    }

    // --- Keyboard navigation ---

    document.addEventListener("keydown", function (e) {
        if (lightboxOpen) {
            trapFocus(e);
            if (e.key === "Escape") { closeLightbox(); return; }
            if (e.key === "ArrowLeft") { navigateLightbox(-1); return; }
            if (e.key === "ArrowRight") { navigateLightbox(1); return; }
            return;
        }

        if (window.PHOTOS) {
            if (e.key === "ArrowLeft") navigatePhoto(-1);
            if (e.key === "ArrowRight") navigatePhoto(1);
        }
    });

    // --- Touch/swipe navigation ---

    var touchStartX = 0;
    var touchStartY = 0;

    document.addEventListener("touchstart", function (e) {
        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });

    document.addEventListener("touchend", function (e) {
        var dx = e.changedTouches[0].screenX - touchStartX;
        var dy = e.changedTouches[0].screenY - touchStartY;

        // Only trigger if horizontal swipe is dominant and > 50px
        if (Math.abs(dx) < 50 || Math.abs(dy) > Math.abs(dx)) return;

        var delta = dx > 0 ? -1 : 1;

        if (lightboxOpen) {
            navigateLightbox(delta);
        } else if (window.PHOTOS) {
            navigatePhoto(delta);
        }
    }, { passive: true });

    // --- Lightbox backdrop click to close ---

    document.addEventListener("click", function (e) {
        if (!lightboxOpen) return;
        var lb = document.getElementById("lightbox");
        var photoArea = document.querySelector(".lightbox-photo");
        // Close if click is on the lightbox backdrop, not on a child interactive element
        if (e.target === lb || e.target === photoArea) closeLightbox();
    });

    // --- Lightbox hash deep-linking ---

    function checkGalleryHash() {
        if (!window.GALLERY_PHOTOS) return;
        var hash = parseInt(location.hash.replace("#", ""), 10);
        if (hash > 0 && hash <= window.GALLERY_PHOTOS.length) {
            openLightbox(hash - 1);
        }
    }

    // --- Init ---

    document.addEventListener("DOMContentLoaded", function () {
        if (window.PHOTOS) initSlideshow();
        if (window.GALLERY_PHOTOS) checkGalleryHash();
    });
})();
```

- [ ] **Step 2: Commit**

```bash
git add static/js/main.js
git commit -m "feat: vanilla JS for slideshow navigation, lightbox, keyboard/touch/swipe support"
```

---

## Task 9: Build orchestrator — template rendering and full pipeline

**Files:**
- Modify: `build.py` (add template rendering and `main()`)
- Create: `tests/test_build.py`

- [ ] **Step 1: Write failing integration test**

```python
# tests/test_build.py
from pathlib import Path
from tests.helpers import make_test_image


def test_full_build_produces_output(tmp_path):
    """Integration test: full build from content to output."""
    # Setup content
    content = tmp_path / "content"
    pb = content / "photoblog"
    pb.mkdir(parents=True)
    make_test_image(pb / "photo1.jpg")

    gal = content / "galleries" / "testgal"
    gal.mkdir(parents=True)
    make_test_image(gal / "img1.jpg")
    make_test_image(gal / "img2.jpg")

    # Setup templates and static (copy from project)
    import shutil
    project_root = Path(__file__).parent.parent
    shutil.copytree(project_root / "templates", tmp_path / "templates")
    shutil.copytree(project_root / "static", tmp_path / "static")

    from build import build_site
    build_site(tmp_path)

    output = tmp_path / "output"
    assert (output / "index.html").exists()
    assert (output / "photoblog" / "index.html").exists()
    assert (output / "gallery" / "index.html").exists()
    assert (output / "gallery" / "testgal" / "index.html").exists()
    assert (output / "static" / "css" / "style.css").exists()
    assert (output / "static" / "js" / "main.js").exists()

    # Check responsive images were generated
    pb_photos = output / "photoblog" / "photos"
    assert (pb_photos / "001-800.avif").exists()
    assert (pb_photos / "001-3200.jpg").exists()

    gal_photos = output / "gallery" / "testgal" / "photos"
    assert (gal_photos / "img1-400.avif").exists()
    assert (gal_photos / "img2-800.jpg").exists()


def test_build_with_empty_content(tmp_path):
    """Build should succeed with empty content dirs."""
    content = tmp_path / "content"
    (content / "photoblog").mkdir(parents=True)
    (content / "galleries").mkdir(parents=True)

    import shutil
    project_root = Path(__file__).parent.parent
    shutil.copytree(project_root / "templates", tmp_path / "templates")
    shutil.copytree(project_root / "static", tmp_path / "static")

    from build import build_site
    build_site(tmp_path)

    output = tmp_path / "output"
    assert (output / "index.html").exists()
    assert (output / "photoblog" / "index.html").exists()
    assert (output / "gallery" / "index.html").exists()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run python -m pytest tests/test_build.py -v
```

Expected: FAIL with `ImportError` (`build_site` doesn't exist yet).

- [ ] **Step 3: Implement build_site() and template rendering in build.py**

Add to `build.py`:

```python
import json
import shutil
from jinja2 import Environment, FileSystemLoader


def make_alt_text(filename: str) -> str:
    """Generate alt text from filename: replace underscores/hyphens with spaces."""
    stem = Path(filename).stem
    return stem.replace("_", " ").replace("-", " ")


def build_photo_json(photos: list[dict], base_path: str, sizes: list[int]) -> str:
    """Build JSON manifest for JS consumption."""
    items = []
    for photo in photos:
        index = photo.get("index", photo["source"].stem)
        items.append({
            "base": f"{base_path}/{index}",
            "sizes": sizes,
            "exif": photo.get("exif", {}),
            "date": photo.get("exif", {}).get("date", ""),
            "alt": make_alt_text(photo["source"].name),
        })
    return json.dumps(items)


def build_gallery_photo_json(photos: list[dict], gallery_name: str) -> str:
    """Build JSON manifest for gallery lightbox."""
    items = []
    for photo in photos:
        stem = photo["source"].stem
        items.append({
            "base": f"/gallery/{gallery_name}/photos/{stem}",
            "sizes": GALLERY_SIZES,
            "exif": photo.get("exif", {}),
            "date": photo.get("exif", {}).get("date", ""),
            "alt": make_alt_text(photo["source"].name),
        })
    return json.dumps(items)


def build_site(project_root: Path):
    """Main build function: scan, generate images, render templates."""
    content_dir = project_root / "content"
    output_dir = project_root / "output"
    template_dir = project_root / "templates"
    static_dir = project_root / "static"

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Scan content
    photoblog_photos = scan_photoblog(content_dir / "photoblog")
    galleries = scan_galleries(content_dir / "galleries")

    # 2. Generate responsive images
    if photoblog_photos:
        generate_photoblog_images(
            photoblog_photos,
            output_dir / "photoblog" / "photos",
        )

    for gallery in galleries:
        gallery_out = output_dir / "gallery" / gallery["name"] / "photos"
        generate_gallery_images(gallery["photos"], gallery_out)

        # Generate cover image if it's a separate _cover file
        cover_path = gallery["cover"]
        if cover_path.stem.lower() == "_cover":
            # Generate cover sizes into the gallery photos dir
            cover_photos = [{"source": cover_path, "exif": {}}]
            generate_gallery_images(cover_photos, gallery_out)

        # Store cover stem for templates
        gallery["cover_stem"] = cover_path.stem

    # 3. Render templates
    env = Environment(loader=FileSystemLoader(str(template_dir)))

    # Landing page
    index_tmpl = env.get_template("index.html")
    (output_dir / "index.html").write_text(index_tmpl.render())

    # Photoblog
    (output_dir / "photoblog").mkdir(parents=True, exist_ok=True)
    pb_tmpl = env.get_template("photoblog.html")
    photos_json = build_photo_json(photoblog_photos, "/photoblog/photos", PHOTOBLOG_SIZES)
    (output_dir / "photoblog" / "index.html").write_text(
        pb_tmpl.render(
            section="photoblog",
            photos=photoblog_photos,
            photos_json=photos_json,
        )
    )

    # Gallery index
    (output_dir / "gallery").mkdir(parents=True, exist_ok=True)
    gi_tmpl = env.get_template("gallery_index.html")
    (output_dir / "gallery" / "index.html").write_text(
        gi_tmpl.render(section="gallery", galleries=galleries)
    )

    # Individual gallery pages
    g_tmpl = env.get_template("gallery.html")
    for gallery in galleries:
        gal_out = output_dir / "gallery" / gallery["name"]
        gal_out.mkdir(parents=True, exist_ok=True)

        photo_data = []
        for p in gallery["photos"]:
            photo_data.append({
                "stem": p["source"].stem,
                "alt": make_alt_text(p["source"].name),
                "exif": p.get("exif", {}),
            })

        photos_json = build_gallery_photo_json(gallery["photos"], gallery["name"])
        (gal_out / "index.html").write_text(
            g_tmpl.render(
                section="gallery",
                gallery_name=gallery["name"],
                photos=photo_data,
                photos_json=photos_json,
            )
        )

    # 4. Copy static assets
    static_out = output_dir / "static"
    if static_out.exists():
        shutil.rmtree(static_out)
    shutil.copytree(str(static_dir), str(static_out))

    # Copy favicon to root if it exists
    favicon = static_dir / "favicon.ico"
    if favicon.exists():
        shutil.copy2(str(favicon), str(output_dir / "favicon.ico"))

    print(f"Build complete: {len(photoblog_photos)} photoblog photos, {len(galleries)} galleries")


if __name__ == "__main__":
    build_site(Path("."))
```

- [ ] **Step 4: Run integration tests**

```bash
uv run python -m pytest tests/test_build.py -v
```

Expected: all tests PASS.

- [ ] **Step 5: Run full test suite**

```bash
uv run python -m pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```bash
git add build.py tests/test_build.py
git commit -m "feat: build orchestrator with template rendering and full pipeline"
```

---

## Task 10: End-to-end smoke test

**Files:**
- No new files — uses existing content + build

- [ ] **Step 1: Create test content if not already present**

```bash
mkdir -p content/photoblog content/galleries/sample
```

Ensure at least 2-3 test images exist in each folder (from Task 1).

- [ ] **Step 2: Run the build**

```bash
make build
```

Expected: output directory populated with HTML, CSS, JS, and responsive images.

- [ ] **Step 3: Verify output structure**

```bash
ls -la output/
ls -la output/photoblog/
ls -la output/photoblog/photos/
ls -la output/gallery/
ls -la output/static/css/
ls -la output/static/js/
```

Verify all expected files exist.

- [ ] **Step 4: Serve and check in browser**

```bash
make serve
```

Open `http://localhost:8000` in browser. Verify:
- Redirects to `/photoblog/`
- Slideshow shows first photo, arrow navigation works
- EXIF bar displays (or is hidden if no EXIF)
- Gallery index shows the sample gallery
- Clicking gallery shows thumbnail grid
- Clicking thumbnail opens lightbox
- Keyboard navigation (left/right arrows) works
- Escape closes lightbox

- [ ] **Step 5: Commit any fixes needed**

If any adjustments were needed during smoke test, review changes with `git diff` and commit specific files:

```bash
git status
# Review and add only the files you changed:
git add build.py templates/ static/
git commit -m "fix: adjustments from end-to-end smoke test"
```
