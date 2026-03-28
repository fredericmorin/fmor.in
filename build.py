#!/usr/bin/env python3
"""Static site builder for fmor.in photoblog and gallery."""

import json
import os
import re
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

import exifread
from PIL import Image

ACCEPTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff"}
PHOTOBLOG_SIZES = [400, 800, 1920, 3200]
GALLERY_SIZES = [400, 800, 1920, 3200]
IMAGE_FORMATS = {"avif": "AVIF", "jpg": "JPEG"}


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
        """Record a completed image task. Must be called from a single thread."""
        self._done += 1
        rel = str(path)
        if self._is_tty:
            try:
                cols = os.get_terminal_size(sys.stderr.fileno()).columns
            except (AttributeError, OSError):
                cols = 80
            line = f"[{self._done}/{self._total}] {rel}"
            if len(line) > cols:
                line = line[: cols - 1]
            print(f"\r{line}", end="", flush=True, file=sys.stderr)
        else:
            print(rel, file=sys.stderr)

    def finish(self, summary: str):
        if self._is_tty:
            try:
                cols = os.get_terminal_size(sys.stderr.fileno()).columns
            except (AttributeError, OSError):
                cols = 80
            print(f"\r{' ' * cols}\r{summary}", file=sys.stderr)
        else:
            print(summary, file=sys.stderr)

    def clear(self):
        """Clear the TTY status line (no-op in non-TTY mode). Call on error paths."""
        if self._is_tty:
            try:
                cols = os.get_terminal_size(sys.stderr.fileno()).columns
            except (AttributeError, OSError):
                cols = 80
            print(f"\r{' ' * cols}\r", end="", flush=True, file=sys.stderr)


def slugify(text: str) -> str:
    """Convert a filename stem to a URL-safe slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


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
            if field == "aperture" and "/" in value:
                try:
                    num, den = value.split("/")
                    value = f"{float(num) / float(den):g}"
                except (ValueError, ZeroDivisionError):
                    pass
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


def resize_and_save(source: Path, output_path: Path, max_width: int, fmt: str):
    """Resize image to max_width (preserving aspect ratio) and save."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Skip if output is newer than source
    if output_path.exists() and output_path.stat().st_mtime > source.stat().st_mtime:
        return output_path

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
    return output_path


def collect_photoblog_tasks(photos: list[dict], output_dir: Path) -> list[tuple]:
    """Return image tasks for photoblog photos. Sets photo['slug'] as a side effect."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks = []
    for photo in photos:
        slug = slugify(photo["source"].stem)
        photo["slug"] = slug
        for size in PHOTOBLOG_SIZES:
            for ext, fmt in IMAGE_FORMATS.items():
                out_path = output_dir / f"{slug}-{size}.{ext}"
                tasks.append((photo["source"], out_path, size, fmt))
    return tasks


def collect_gallery_tasks(photos: list[dict], output_dir: Path) -> list[tuple]:
    """Return image tasks for gallery photos."""
    output_dir.mkdir(parents=True, exist_ok=True)
    tasks = []
    for photo in photos:
        slug = slugify(photo["source"].stem)
        for size in GALLERY_SIZES:
            for ext, fmt in IMAGE_FORMATS.items():
                out_path = output_dir / f"{slug}-{size}.{ext}"
                tasks.append((photo["source"], out_path, size, fmt))
    return tasks


def run_image_tasks(tasks: list[tuple], reporter: "Reporter"):
    """Execute image resize tasks in parallel using a thread pool."""
    with ThreadPoolExecutor() as pool:
        futures = {pool.submit(resize_and_save, *task): task for task in tasks}
        try:
            for future in as_completed(futures):
                path = future.result()  # re-raises any exception
                reporter.report(path)
        except Exception:
            reporter.clear()
            raise


def make_alt_text(filename: str) -> str:
    """Generate alt text from filename: replace underscores/hyphens with spaces."""
    stem = Path(filename).stem
    return stem.replace("_", " ").replace("-", " ")


def build_photo_json(photos: list[dict], base_path: str, sizes: list[int]) -> str:
    """Build JSON manifest for JS consumption."""
    items = []
    for photo in photos:
        slug = photo.get("slug") or slugify(photo["source"].stem)
        items.append({
            "slug": slug,
            "base": f"{base_path}/{slug}",
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
        slug = slugify(photo["source"].stem)
        items.append({
            "base": f"/gallery/{gallery_name}/photos/{slug}",
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

        gallery["cover_stem"] = slugify(cover_path.stem)

    reporter = Reporter(total=len(all_tasks))
    run_image_tasks(all_tasks, reporter)

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
                "stem": slugify(p["source"].stem),
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

    reporter.finish(
        f"Build complete: {len(photoblog_photos)} photoblog photos, {len(galleries)} galleries"
    )


if __name__ == "__main__":
    build_site(Path("."))
