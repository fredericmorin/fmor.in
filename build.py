#!/usr/bin/env python3
"""Static site builder for fmor.in photoblog and gallery."""

import json
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

import exifread
from PIL import Image

ACCEPTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tiff"}
PHOTOBLOG_SIZES = [800, 1920, 3200]
GALLERY_SIZES = [400, 800, 1920, 3200]
IMAGE_FORMATS = {"avif": "AVIF", "jpg": "JPEG"}


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
