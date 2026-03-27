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
