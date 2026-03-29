# tests/test_images.py
from pathlib import Path
from tests.helpers import make_test_image


def test_collect_photoblog_tasks_returns_tuples(tmp_path):
    from build import collect_photoblog_tasks, scan_photoblog, PHOTOBLOG_SIZES, IMAGE_FORMATS

    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "photo.jpg")
    photos = scan_photoblog(src)
    out = tmp_path / "output" / "photoblog" / "photos"
    tasks = collect_photoblog_tasks(photos, out)
    # 1 photo x 4 sizes x 2 formats = 8 tasks
    assert len(tasks) == len(PHOTOBLOG_SIZES) * len(IMAGE_FORMATS)
    source, output_path, max_width, fmt = tasks[0]
    assert source == photos[0]["source"]
    assert isinstance(output_path, Path)
    assert isinstance(max_width, int)
    assert fmt in ("JPEG", "AVIF")


def test_collect_gallery_tasks_returns_tuples(tmp_path):
    from build import collect_gallery_tasks, GALLERY_SIZES, IMAGE_FORMATS

    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "photo.jpg")
    photos = [{"source": src / "photo.jpg", "exif": {}}]
    out = tmp_path / "output" / "gallery" / "test" / "photos"
    tasks = collect_gallery_tasks(photos, out)
    # 1 photo x 4 sizes x 2 formats = 8 tasks
    assert len(tasks) == len(GALLERY_SIZES) * len(IMAGE_FORMATS)
    source, output_path, max_width, fmt = tasks[0]
    assert source == src / "photo.jpg"
    assert isinstance(output_path, Path)


def test_collect_photoblog_tasks_creates_all_sizes(tmp_path):
    from build import collect_photoblog_tasks, scan_photoblog, resize_and_save

    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "photo.jpg", width=4000, height=3000)
    out = tmp_path / "output" / "photoblog" / "photos"
    photos = scan_photoblog(src)
    tasks = collect_photoblog_tasks(photos, out)
    for task in tasks:
        resize_and_save(*task)
    files = sorted(f.name for f in out.iterdir())
    assert "photo-400.avif" in files
    assert "photo-400.jpg" in files
    assert "photo-800.avif" in files
    assert "photo-800.jpg" in files
    assert "photo-1920.avif" in files
    assert "photo-1920.jpg" in files
    assert "photo-3200.avif" in files
    assert "photo-3200.jpg" in files


def test_collect_gallery_tasks_creates_thumbnail_size(tmp_path):
    from build import collect_gallery_tasks, resize_and_save

    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "photo.jpg", width=4000, height=3000)
    out = tmp_path / "output" / "gallery" / "test" / "photos"
    photos = [{"source": src / "photo.jpg", "exif": {}}]
    tasks = collect_gallery_tasks(photos, out)
    for task in tasks:
        resize_and_save(*task)
    files = sorted(f.name for f in out.iterdir())
    assert "photo-400.avif" in files
    assert "photo-400.jpg" in files
    assert "photo-800.avif" in files
    assert "photo-3200.jpg" in files
    assert len(files) == 8


def test_incremental_build_skips_existing(tmp_path):
    from build import collect_photoblog_tasks, scan_photoblog, resize_and_save
    import time

    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "photo.jpg")
    out = tmp_path / "output"
    out.mkdir(parents=True)
    photos = scan_photoblog(src)
    tasks = collect_photoblog_tasks(photos, out)
    for task in tasks:
        resize_and_save(*task)
    first_mtime = (out / "photo-800.jpg").stat().st_mtime
    time.sleep(0.1)
    for task in tasks:
        resize_and_save(*task)
    second_mtime = (out / "photo-800.jpg").stat().st_mtime
    assert first_mtime == second_mtime


def test_generated_image_dimensions(tmp_path):
    from build import collect_photoblog_tasks, scan_photoblog, resize_and_save
    from PIL import Image

    src = tmp_path / "src"
    src.mkdir()
    make_test_image(src / "photo.jpg", width=4000, height=3000)
    out = tmp_path / "output"
    photos = scan_photoblog(src)
    tasks = collect_photoblog_tasks(photos, out)
    for task in tasks:
        resize_and_save(*task)
    img = Image.open(out / "photo-800.jpg")
    assert img.width == 800
    assert img.height == 600


def test_resize_and_save_returns_output_path(tmp_path):
    from build import resize_and_save

    src = tmp_path / "src.jpg"
    make_test_image(src, width=200, height=200)
    out = tmp_path / "out-100.jpg"
    result = resize_and_save(src, out, 100, "JPEG")
    assert result == out


def test_reporter_non_tty_prints_lines(tmp_path, capsys):
    from build import Reporter

    r = Reporter(total=3, is_tty=False)
    r.report(tmp_path / "a.jpg")
    r.report(tmp_path / "b.avif")
    captured = capsys.readouterr()
    lines = captured.err.strip().splitlines()
    assert len(lines) == 2
    assert "a.jpg" in lines[0]
    assert "b.avif" in lines[1]


def test_reporter_non_tty_finish_prints_summary(capsys):
    from build import Reporter

    r = Reporter(total=5, is_tty=False)
    r.finish("Build complete: 5 files")
    captured = capsys.readouterr()
    assert "Build complete: 5 files" in captured.err


def test_reporter_tty_overwrites_line(tmp_path, capsys, monkeypatch):
    from build import Reporter

    r = Reporter(total=3, is_tty=True)
    r.report(tmp_path / "a.jpg")
    r.report(tmp_path / "b.avif")
    captured = capsys.readouterr()
    # Should use \r, not \n between updates
    assert "\r" in captured.err
    # Should not have two newline-separated file lines
    newline_lines = [line for line in captured.err.split("\n") if line.strip()]
    assert len(newline_lines) <= 1


def test_reporter_tty_finish_clears_line(capsys):
    from build import Reporter

    r = Reporter(total=2, is_tty=True)
    r.finish("Done")
    captured = capsys.readouterr()
    assert "Done" in captured.err
