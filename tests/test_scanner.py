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
