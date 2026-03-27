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
    assert (pb_photos / "001-800.avif").exists()
    assert (pb_photos / "001-3200.jpg").exists()

    gal_photos = output / "gallery" / "testgal" / "photos"
    assert (gal_photos / "img1-400.avif").exists()
    assert (gal_photos / "img2-800.jpg").exists()


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
