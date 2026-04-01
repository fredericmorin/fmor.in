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
    assert (output / "static" / "dist" / "bundle.css").exists()
    assert (output / "static" / "dist" / "bundle.js").exists()

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


def test_gallery_page_uses_spa_shell(tmp_path):
    """Gallery page HTML should be a SPA shell with preload hints for gallery data."""
    import shutil
    import json
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

    # SPA shell structure
    assert '<div id="app"></div>' in html
    assert "/static/dist/bundle.js" in html
    assert "/static/dist/bundle.css" in html

    # Preloads both gallery index and individual gallery data
    assert "__PRELOAD__" in html
    assert '"/data/gallery-index.json"' in html
    assert '"/data/galleries/mygal.json"' in html

    # JSON data file was written with correct structure
    data = json.loads((tmp_path / "output" / "data" / "galleries" / "mygal.json").read_text())
    assert len(data) == 2
    assert all("slug" in p for p in data)
    assert all(p["base"].startswith("/gallery/mygal/photos/") for p in data)
