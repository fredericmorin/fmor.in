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


def test_resize_and_save_returns_output_path(tmp_path):
    from build import resize_and_save
    src = tmp_path / "src.jpg"
    make_test_image(src, width=200, height=200)
    out = tmp_path / "out-100.jpg"
    result = resize_and_save(src, out, 100, "JPEG")
    assert result == out
