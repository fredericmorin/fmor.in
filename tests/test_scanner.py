from pathlib import Path
import pytest
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
    with pytest.raises(ValueError, match="stem collision"):
        scan_galleries(tmp_content / "galleries")


# ---------------------------------------------------------------------------
# EXIF override tests
# ---------------------------------------------------------------------------

def test_load_exif_override_no_sidecar(tmp_path):
    photo = tmp_path / "photo.jpg"
    make_test_image(photo)

    from build import load_exif_override
    assert load_exif_override(photo) == {}


def test_load_exif_override_overrides_fields(tmp_path):
    photo = tmp_path / "photo.jpg"
    make_test_image(photo)
    (tmp_path / "photo.yaml").write_text("camera: Leica M6\nlens: Summicron 50mm\n")

    from build import load_exif_override
    override = load_exif_override(photo)
    assert override["camera"] == "Leica M6"
    assert override["lens"] == "Summicron 50mm"


def test_load_exif_override_extra_fields(tmp_path):
    photo = tmp_path / "photo.jpg"
    make_test_image(photo)
    (tmp_path / "photo.yaml").write_text("title: Golden hour\ncaption: Nice shot\n")

    from build import load_exif_override
    override = load_exif_override(photo)
    assert override["title"] == "Golden hour"
    assert override["caption"] == "Nice shot"


def test_load_exif_override_invalid_yaml_warns(tmp_path, capsys):
    photo = tmp_path / "photo.jpg"
    make_test_image(photo)
    (tmp_path / "photo.yaml").write_text("key: [unclosed")

    from build import load_exif_override
    result = load_exif_override(photo)
    assert result == {}
    assert "Warning" in capsys.readouterr().err


def test_scan_photoblog_applies_exif_override(tmp_content):
    pb = tmp_content / "photoblog"
    make_test_image(pb / "shot.jpg")
    (pb / "shot.yaml").write_text("camera: Film Camera\ntitle: My shot\n")

    from build import scan_photoblog
    photos = scan_photoblog(pb)
    assert len(photos) == 1
    assert photos[0]["exif"]["camera"] == "Film Camera"
    assert photos[0]["exif"]["title"] == "My shot"


def test_scan_galleries_applies_exif_override(tmp_content):
    gal = tmp_content / "galleries" / "trip"
    gal.mkdir(parents=True, exist_ok=True)
    make_test_image(gal / "img1.jpg")
    (gal / "img1.yaml").write_text("camera: Override Cam\n")

    from build import scan_galleries
    galleries = scan_galleries(tmp_content / "galleries")
    assert galleries[0]["photos"][0]["exif"]["camera"] == "Override Cam"


def test_exif_override_merged_over_extracted(tmp_path):
    """Override values replace EXIF-extracted values for the same key."""
    photo = tmp_path / "photo.jpg"
    make_test_image(photo)
    (tmp_path / "photo.yaml").write_text("camera: Manual Override\n")

    from build import extract_exif, load_exif_override
    exif = extract_exif(photo)
    exif.update(load_exif_override(photo))
    assert exif["camera"] == "Manual Override"


# ---------------------------------------------------------------------------
# EXIF date slug tests
# ---------------------------------------------------------------------------

def test_photo_slug_uses_exif_date(tmp_path):
    """photo_slug() returns a slugified datetime when EXIF date is present."""
    from build import photo_slug
    photo = {
        "source": tmp_path / "IMG_1234.jpg",
        "exif": {"date": "2024:06:15 09:30:00"},
    }
    assert photo_slug(photo) == "20240615-093000"


def test_photo_slug_falls_back_to_filename(tmp_path):
    """photo_slug() falls back to slugified filename stem when no EXIF date."""
    from build import photo_slug
    photo = {
        "source": tmp_path / "My_Great Photo.jpg",
        "exif": {},
    }
    assert photo_slug(photo) == "my-great-photo"


def test_photo_slug_falls_back_on_missing_exif(tmp_path):
    """photo_slug() falls back to filename when exif key is absent."""
    from build import photo_slug
    photo = {"source": tmp_path / "sunset.jpg"}
    assert photo_slug(photo) == "sunset"


def test_collect_photoblog_tasks_uses_exif_date_slug(tmp_path):
    """collect_photoblog_tasks() uses EXIF date for output filename slug."""
    from build import collect_photoblog_tasks
    from tests.helpers import make_test_image

    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "IMG_1234.jpg")
    photos = [{"source": src / "IMG_1234.jpg", "exif": {"date": "2023:12:01 14:00:00"}}]
    out = tmp_path / "output" / "photoblog" / "photos"
    tasks = collect_photoblog_tasks(photos, out)

    slugs = {task[1].stem for task in tasks}
    assert all(stem.startswith("20231201-140000-") for stem in slugs)
    assert photos[0]["slug"] == "20231201-140000"


def test_collect_gallery_tasks_uses_exif_date_slug(tmp_path):
    """collect_gallery_tasks() uses EXIF date for output filename slug."""
    from build import collect_gallery_tasks
    from tests.helpers import make_test_image

    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "IMG_5678.jpg")
    photos = [{"source": src / "IMG_5678.jpg", "exif": {"date": "2024:03:20 18:45:30"}}]
    out = tmp_path / "output" / "gallery" / "test" / "photos"
    tasks = collect_gallery_tasks(photos, out)

    slugs = {task[1].stem for task in tasks}
    assert all(stem.startswith("20240320-184530-") for stem in slugs)
    assert photos[0]["slug"] == "20240320-184530"
