# Photoblog Gallery View Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/photoblog/gallery/` page showing all photoblog photos as a thumbnail grid with lightbox, linked from the main photoblog slideshow.

**Architecture:** Reuse the existing gallery thumbnail+lightbox pattern. Add a 400px size to photoblog image generation so thumbnails are appropriately sized. Render a new `photoblog_gallery.html` template to `output/photoblog/gallery/index.html`. Link the slideshow and gallery views to each other.

**Tech Stack:** Python/Jinja2 (build.py), vanilla JS (main.js lightbox — no changes needed), CSS grid (style.css — existing classes reused).

---

## File Map

| File | Change |
|------|--------|
| `build.py` | Add 400 to `PHOTOBLOG_SIZES`; render new template in `build_site()` |
| `templates/photoblog_gallery.html` | New — thumbnail grid + lightbox for photoblog photos |
| `templates/photoblog.html` | Add link to gallery view |
| `tests/test_build.py` | Update size assertion; add test for gallery page output |

---

### Task 1: Add 400px size to photoblog image generation

**Files:**
- Modify: `build.py:18`
- Modify: `tests/test_build.py:71`

- [ ] **Step 1: Write the failing test**

In `tests/test_build.py`, update `test_full_build_parallel_generates_all_images` — the size count changes from 3 to 4:

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

    real_root = Path(__file__).parent.parent
    shutil.copytree(real_root / "templates", tmp_path / "templates")
    shutil.copytree(real_root / "static", tmp_path / "static")

    build_site(tmp_path)

    out = tmp_path / "output"
    pb_photos = out / "photoblog" / "photos"
    # 2 photos x 4 sizes x 2 formats = 16 files
    assert len(list(pb_photos.iterdir())) == 16

    gal_photos = out / "gallery" / "mygal" / "photos"
    # 3 photos x 4 sizes x 2 formats = 24 files
    assert len(list(gal_photos.iterdir())) == 24
```

- [ ] **Step 2: Run test to verify it fails**

```
pytest tests/test_build.py::test_full_build_parallel_generates_all_images -v
```

Expected: FAIL — `assert 12 == 16`

- [ ] **Step 3: Add 400 to PHOTOBLOG_SIZES in build.py**

Change line 18 from:

```python
PHOTOBLOG_SIZES = [800, 1920, 3200]
```

to:

```python
PHOTOBLOG_SIZES = [400, 800, 1920, 3200]
```

- [ ] **Step 4: Run test to verify it passes**

```
pytest tests/test_build.py::test_full_build_parallel_generates_all_images -v
```

Expected: PASS

- [ ] **Step 5: Run full test suite to check nothing regressed**

```
pytest -v
```

Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add build.py tests/test_build.py
git commit -m "feat: add 400px size to photoblog image generation for gallery thumbnails"
```

---

### Task 2: Create the photoblog gallery template

**Files:**
- Create: `templates/photoblog_gallery.html`

The template reuses existing CSS classes: `.gallery-header`, `.gallery-back`, `.gallery-title`, `.thumbnail-grid`, `.thumbnail`, `.lightbox`, and all lightbox-related classes. The JS lightbox is driven by `window.GALLERY_PHOTOS`.

- [ ] **Step 1: Create `templates/photoblog_gallery.html`**

```html
{% extends "base.html" %}

{% block title %}Photoblog — Gallery — fmor.in{% endblock %}
{% block og_title %}Photoblog — Gallery — fmor.in{% endblock %}

{% block head_extra %}
<script>
    window.GALLERY_PHOTOS = {{ photos_json | safe }};
</script>
{% endblock %}

{% block content %}
<div class="gallery-header">
    <a href="/photoblog/" class="gallery-back" aria-label="Back to slideshow">← Slideshow</a>
    <span class="gallery-sep">·</span>
    <h1 class="gallery-title">Photoblog</h1>
</div>

<div class="thumbnail-grid">
    {% for photo in photos %}
    <div class="thumbnail" data-index="{{ loop.index0 }}" onclick="openLightbox({{ loop.index0 }})" role="button" aria-label="View {{ photo.alt }}" tabindex="0">
        <picture>
            <source type="image/avif"
                srcset="/photoblog/photos/{{ photo.slug }}-400.avif 400w, /photoblog/photos/{{ photo.slug }}-800.avif 800w"
                sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw">
            <source type="image/jpeg"
                srcset="/photoblog/photos/{{ photo.slug }}-400.jpg 400w, /photoblog/photos/{{ photo.slug }}-800.jpg 800w"
                sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw">
            <img
                src="/photoblog/photos/{{ photo.slug }}-400.jpg"
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

- [ ] **Step 2: Visually verify the template is syntactically valid Jinja2**

Check that:
- `{% extends %}`, `{% block %}`, `{% endblock %}`, `{% for %}`, `{% endfor %}` are all balanced
- All Jinja2 variables reference fields that will be passed: `photos_json`, `photo.slug`, `photo.alt`, `loop.index0`

No command to run — review manually.

- [ ] **Step 3: Commit**

```bash
git add templates/photoblog_gallery.html
git commit -m "feat: add photoblog_gallery.html template with thumbnail grid and lightbox"
```

---

### Task 3: Render the gallery page in build.py

**Files:**
- Modify: `build.py` — `build_site()` function, after the existing photoblog render block (~line 356–366)

The `collect_photoblog_tasks` function sets `photo["slug"]` as a side-effect when it runs (line 244). By the time we render templates, slugs are present on all photoblog photos. `photos_json` is already built and assigned. We need to build `photo_data` (slug + alt) and render the new template.

- [ ] **Step 1: Write the failing test**

Add to `tests/test_build.py`:

```python
def test_photoblog_gallery_page_is_generated(tmp_path):
    """build_site() creates photoblog/gallery/index.html."""
    import shutil
    from build import build_site

    content = tmp_path / "content"
    pb = content / "photoblog"
    pb.mkdir(parents=True)
    make_test_image(pb / "photo1.jpg")
    make_test_image(pb / "photo2.jpg")

    project_root = Path(__file__).parent.parent
    shutil.copytree(project_root / "templates", tmp_path / "templates")
    shutil.copytree(project_root / "static", tmp_path / "static")

    build_site(tmp_path)

    output = tmp_path / "output"
    gallery_page = output / "photoblog" / "gallery" / "index.html"
    assert gallery_page.exists()

    content_html = gallery_page.read_text()
    assert "GALLERY_PHOTOS" in content_html
    assert "thumbnail-grid" in content_html
    assert "photo1" in content_html or "photo2" in content_html
```

- [ ] **Step 2: Run test to verify it fails**

```
pytest tests/test_build.py::test_photoblog_gallery_page_is_generated -v
```

Expected: FAIL — `AssertionError: assert False` (file does not exist)

- [ ] **Step 3: Add the render block to build_site() in build.py**

After the photoblog block (after line ~366, where `output/photoblog/index.html` is written), add:

```python
    # Photoblog gallery view
    (output_dir / "photoblog" / "gallery").mkdir(parents=True, exist_ok=True)
    pbg_tmpl = env.get_template("photoblog_gallery.html")
    pb_photo_data = [
        {"slug": p["slug"], "alt": make_alt_text(p["source"].name)}
        for p in photoblog_photos
    ]
    (output_dir / "photoblog" / "gallery" / "index.html").write_text(
        pbg_tmpl.render(
            section="photoblog",
            photos=pb_photo_data,
            photos_json=photos_json,
        )
    )
```

The exact location in `build_site()`: insert after line 366 (after the `(output_dir / "photoblog" / "index.html").write_text(...)` call) and before the gallery index block.

- [ ] **Step 4: Run test to verify it passes**

```
pytest tests/test_build.py::test_photoblog_gallery_page_is_generated -v
```

Expected: PASS

- [ ] **Step 5: Run full test suite**

```
pytest -v
```

Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add build.py tests/test_build.py
git commit -m "feat: render photoblog gallery page at /photoblog/gallery/"
```

---

### Task 4: Link the slideshow and gallery views

**Files:**
- Modify: `templates/photoblog.html` — add a link to the gallery view

The photoblog slideshow template has a `.slideshow` container with `.photo-counter` in the top-right. We add a "Gallery" link inside the slideshow, positioned at the top-left of the photo area as a small nav element. Existing CSS already handles `.gallery-back` styling (muted color, hover to lighter).

- [ ] **Step 1: Add the gallery link to photoblog.html**

In `templates/photoblog.html`, inside `{% block content %}`, replace:

```html
<div class="slideshow" id="slideshow" data-section="photoblog">
    <div class="slideshow-photo">
```

with:

```html
<div class="slideshow" id="slideshow" data-section="photoblog">
    <div class="slideshow-photo">
        <a href="/photoblog/gallery/" class="gallery-back photoblog-gallery-link" aria-label="View all photos as gallery">Grid</a>
```

> The `.gallery-back` class gives it the existing muted link style. `.photoblog-gallery-link` is added so CSS can position it.

- [ ] **Step 2: Add CSS to position the link**

In `static/css/style.css`, after the `.photo-counter` rule (~line 160), add:

```css
.photoblog-gallery-link {
    position: absolute;
    top: 12px;
    left: 20px;
    font-size: 11px;
    color: #555;
    z-index: 5;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.photoblog-gallery-link:hover {
    color: #aaa;
}
```

- [ ] **Step 3: Run full build to verify the link renders**

```
python build.py
```

Expected: exits without error; `output/photoblog/index.html` contains `href="/photoblog/gallery/"`.

Verify:
```
grep -q 'href="/photoblog/gallery/"' output/photoblog/index.html && echo "OK"
```

Expected output: `OK`

- [ ] **Step 4: Run the full test suite**

```
pytest -v
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add templates/photoblog.html static/css/style.css
git commit -m "feat: add gallery view link to photoblog slideshow"
```

---

## Self-Review

**Spec coverage:**
- "view all the photos in the photoblog section as a gallery" → Task 2+3: new `/photoblog/gallery/` page with thumbnail grid ✓
- Photos open in lightbox → Task 2: lightbox block reused from gallery.html ✓
- Navigation back to slideshow → Task 4: "Grid" link on slideshow; "← Slideshow" link on gallery page ✓
- Images sized appropriately for thumbnails → Task 1: 400px added to PHOTOBLOG_SIZES ✓
- Tests updated → Tasks 1, 3 ✓

**Placeholder scan:** No TBDs, TODOs, or hand-wavy steps. All code blocks are complete.

**Type consistency:**
- `photo.slug` in template matches `photo_data` dict key `"slug"` ✓
- `photo.alt` in template matches `photo_data` dict key `"alt"` ✓
- `photos_json` rendered into `window.GALLERY_PHOTOS` — same format the lightbox JS reads (`base`, `sizes`, `exif`, `date`, `alt`) ✓
- Lightbox JS functions (`openLightbox`, `closeLightbox`, `navigateLightbox`) unchanged, referenced correctly ✓
