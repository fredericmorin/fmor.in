#!/usr/bin/env python3
"""Static site builder for fmor.in photoblog and gallery."""

import sys
from pathlib import Path

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
