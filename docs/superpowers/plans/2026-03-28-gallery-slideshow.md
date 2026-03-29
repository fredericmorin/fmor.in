# Gallery Slideshow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the gallery page's Jinja2-rendered grid + lightbox with the same slideshow/grid UX as the photoblog.

**Architecture:** `gallery.html` mirrors `photoblog.html`'s HTML structure and uses `window.PHOTOS`; `build.py` switches to `build_photo_json` for gallery pages; the lightbox code in `main.js` is deleted since `initSlideshow()` already handles gallery pages once they set `window.PHOTOS`.

**Tech Stack:** Jinja2 templates, vanilla JS (IIFE), Python build script, pytest

---

## File Map

| File | Change |
|---|---|
| `tests/test_build.py` | Add `test_gallery_page_uses_slideshow_pattern` |
| `templates/gallery.html` | Replace grid+lightbox with slideshow+grid structure; `GALLERY_PHOTOS` → `PHOTOS` |
| `build.py` | Gallery loop: call `build_photo_json` instead of `build_gallery_photo_json`; delete `build_gallery_photo_json` |
| `static/js/main.js` | Delete lightbox section (lines 176–304) and clean up `DOMContentLoaded` init |

---

## Task 1: Add failing tests

**Files:**
- Modify: `tests/test_build.py`

- [ ] **Step 1: Add the test**

Append to `tests/test_build.py`:

```python
def test_gallery_page_uses_slideshow_pattern(tmp_path):
    """Gallery page HTML should use the photoblog slideshow UX, not a lightbox."""
    import shutil
    from build import build_site

    content = tmp_path / "content"
    gal = content / "galleries" / "mygal"
    gal.mkdir(parents=True)
    make_test_image(gal / "shot1.jpg")
    make_test_image(gal / "shot2.jpg")

    project_root = Path(__file__).parent.parent
    shutil.copytree(project_root / "templates", tmp_path / "templates")
    shutil.copytree(project_root / "static", tmp_path / "static")

    build_site(tmp_path)

    html = (tmp_path / "output" / "gallery" / "mygal" / "index.html").read_text()

    # Uses slideshow manifest key, not lightbox key
    assert "window.PHOTOS" in html
    assert "window.GALLERY_PHOTOS" not in html

    # Has slideshow and grid containers
    assert 'id="slideshow"' in html
    assert 'id="photoblog-grid-view"' in html
    assert 'id="photoblog-grid-thumbnails"' in html

    # No lightbox
    assert 'id="lightbox"' not in html

    # JSON manifest includes slug field (required for hash navigation)
    import json
    script_start = html.index("window.PHOTOS = ") + len("window.PHOTOS = ")
    script_end = html.index(";", script_start)
    photos_data = json.loads(html[script_start:script_end])
    assert len(photos_data) == 2
    assert all("slug" in p for p in photos_data)
    assert all(p["base"].startswith("/gallery/mygal/photos/") for p in photos_data)
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
uv run pytest tests/test_build.py::test_gallery_page_uses_slideshow_pattern -v
```

Expected: FAIL — `assert "window.PHOTOS" in html` fails because current code outputs `window.GALLERY_PHOTOS`.

---

## Task 2: Update `gallery.html`

**Files:**
- Modify: `templates/gallery.html`

- [ ] **Step 3: Replace gallery.html with slideshow structure**

Replace the entire file contents with:

```html
{% extends "base.html" %}

{% block title %}{{ gallery_name | replace('_', ' ') | replace('-', ' ') | title }} — fmor.in{% endblock %}
{% block og_title %}{{ gallery_name | replace('_', ' ') | replace('-', ' ') | title }} — fmor.in{% endblock %}
{% block og_image %}
{% if photos %}
<meta property="og:image" content="/gallery/{{ gallery_name }}/photos/{{ photos[0].slug }}-1920.jpg">
{% endif %}
{% endblock %}

{% block head_extra %}
<script>
    window.PHOTOS = {{ photos_json | safe }};
</script>
{% endblock %}

{% block content %}
<div class="gallery-header">
    <a href="/gallery/" class="gallery-back" aria-label="Back to galleries">← Galleries</a>
    <span class="gallery-sep">·</span>
    <h1 class="gallery-title">{{ gallery_name | replace('_', ' ') | replace('-', ' ') | title }}</h1>
</div>

<div class="slideshow" id="slideshow" data-section="gallery">
    <div class="slideshow-photo">
        <a href="#gallery" class="gallery-back photoblog-gallery-link" aria-label="View all photos as gallery" onclick="showPhotoblogGrid(event)">Grid</a>
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

<div id="photoblog-grid-view" style="display:none">
    <div class="thumbnail-grid" id="photoblog-grid-thumbnails"></div>
</div>
{% endblock %}
```

---

## Task 3: Update `build.py`

**Files:**
- Modify: `build.py`

- [ ] **Step 4: Switch gallery pages to `build_photo_json`**

In `build_site`, find the individual gallery pages loop (around line 457). Replace:

```python
        photos_json = build_gallery_photo_json(gallery["photos"], gallery["name"])
```

With:

```python
        photos_json = build_photo_json(gallery["photos"], f"/gallery/{gallery['name']}/photos", GALLERY_SIZES)
```

- [ ] **Step 5: Delete `build_gallery_photo_json`**

Remove the entire function (lines 366–378):

```python
def build_gallery_photo_json(photos: list[dict], gallery_name: str) -> str:
    """Build JSON manifest for gallery lightbox."""
    items = []
    for photo in photos:
        slug = photo.get("slug") or photo_slug(photo)
        items.append({
            "base": f"/gallery/{gallery_name}/photos/{slug}",
            "sizes": GALLERY_SIZES,
            "exif": photo.get("exif", {}),
            "date": photo.get("exif", {}).get("date", ""),
            "alt": make_alt_text(photo["source"].name),
        })
    return json.dumps(items)
```

- [ ] **Step 6: Run the target test and full suite**

```bash
uv run pytest tests/test_build.py::test_gallery_page_uses_slideshow_pattern -v
```

Expected: PASS.

```bash
uv run pytest -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit**

```bash
git add templates/gallery.html build.py tests/test_build.py
git commit -m "feat: gallery page uses photoblog slideshow UX"
```

---

## Task 4: Remove lightbox from `main.js`

**Files:**
- Modify: `static/js/main.js`

No automated test exists for JS source content; verify with grep after editing.

- [ ] **Step 8: Delete the lightbox section**

Remove lines 176–304 (from `// --- Lightbox (Gallery) ---` through the closing `}`  of `checkGalleryHash`). That is, delete everything from:

```js
    // --- Lightbox (Gallery) ---
```

…down to and including:

```js
    }
```

(the closing brace of `checkGalleryHash`).

Also remove the lightbox branch from the `keydown` handler. Change:

```js
    document.addEventListener("keydown", function (e) {
        if (lightboxOpen) {
            trapFocus(e);
            if (e.key === "Escape") { closeLightbox(); return; }
            if (e.key === "ArrowLeft") { navigateLightbox(-1); return; }
            if (e.key === "ArrowRight") { navigateLightbox(1); return; }
            return;
        }

        if (window.PHOTOS && !gridVisible) {
            if (e.key === "ArrowLeft") navigatePhoto(-1);
            if (e.key === "ArrowRight") navigatePhoto(1);
            if (e.key === "Escape") showPhotoblogGrid();
        }
    });
```

To:

```js
    document.addEventListener("keydown", function (e) {
        if (window.PHOTOS && !gridVisible) {
            if (e.key === "ArrowLeft") navigatePhoto(-1);
            if (e.key === "ArrowRight") navigatePhoto(1);
            if (e.key === "Escape") showPhotoblogGrid();
        }
    });
```

Remove the backdrop-click listener entirely:

```js
    // --- Lightbox backdrop click to close ---

    document.addEventListener("click", function (e) {
        if (!lightboxOpen) return;
        var lb = document.getElementById("lightbox");
        var photoArea = document.querySelector(".lightbox-photo");
        // Close if click is on the lightbox backdrop, not on a child interactive element
        if (e.target === lb || e.target === photoArea) closeLightbox();
    });
```

Update the `DOMContentLoaded` init block. Change:

```js
    document.addEventListener("DOMContentLoaded", function () {
        if (window.PHOTOS) initSlideshow();
        if (window.GALLERY_PHOTOS) checkGalleryHash();
    });
```

To:

```js
    document.addEventListener("DOMContentLoaded", function () {
        if (window.PHOTOS) initSlideshow();
    });
```

- [ ] **Step 9: Verify no lightbox references remain**

```bash
grep -n "lightbox\|GALLERY_PHOTOS\|checkGalleryHash\|trapFocus" static/js/main.js
```

Expected: no output (zero matches).

- [ ] **Step 10: Run full test suite**

```bash
uv run pytest -v
```

Expected: all tests pass.

- [ ] **Step 11: Commit**

```bash
git add static/js/main.js
git commit -m "chore: remove lightbox JS, gallery now uses initSlideshow"
```
