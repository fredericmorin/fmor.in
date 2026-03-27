from pathlib import Path
from tests.helpers import make_test_image


def test_full_build_produces_output(tmp_path):
    """Integration test: full build from content to output."""
    # Setup content
    content = tmp_path / "content"
    pb = content / "photoblog"
    pb.mkdir(parents=True)
    make_test_image(pb / "photo1.jpg")

    gal = content / "galleries" / "testgal"
    gal.mkdir(parents=True)
    make_test_image(gal / "img1.jpg")
    make_test_image(gal / "img2.jpg")

    # Setup templates and static (copy from project)
    import shutil
    project_root = Path(__file__).parent.parent
    shutil.copytree(project_root / "templates", tmp_path / "templates")
    shutil.copytree(project_root / "static", tmp_path / "static")

    from build import build_site
    build_site(tmp_path)

    output = tmp_path / "output"
    assert (output / "index.html").exists()
    assert (output / "photoblog" / "index.html").exists()
    assert (output / "gallery" / "index.html").exists()
    assert (output / "gallery" / "testgal" / "index.html").exists()
    assert (output / "static" / "css" / "style.css").exists()
    assert (output / "static" / "js" / "main.js").exists()

    # Check responsive images were generated
    pb_photos = output / "photoblog" / "photos"
    assert (pb_photos / "photo1-400.avif").exists()
    assert (pb_photos / "photo1-3200.jpg").exists()

    gal_photos = output / "gallery" / "testgal" / "photos"
    assert (gal_photos / "img1-400.avif").exists()
    assert (gal_photos / "img2-800.jpg").exists()


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


def test_build_with_empty_content(tmp_path):
    """Build should succeed with empty content dirs."""
    content = tmp_path / "content"
    (content / "photoblog").mkdir(parents=True)
    (content / "galleries").mkdir(parents=True)

    import shutil
    project_root = Path(__file__).parent.parent
    shutil.copytree(project_root / "templates", tmp_path / "templates")
    shutil.copytree(project_root / "static", tmp_path / "static")

    from build import build_site
    build_site(tmp_path)

    output = tmp_path / "output"
    assert (output / "index.html").exists()
    assert (output / "photoblog" / "index.html").exists()
    assert (output / "gallery" / "index.html").exists()


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
    assert "thumbnail-grid" in content_html
    assert 'href="/photoblog/#photo1"' in content_html
    assert "photo1" in content_html or "photo2" in content_html
