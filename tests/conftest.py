import pytest


@pytest.fixture
def tmp_content(tmp_path):
    """Create a temporary content directory with test photos."""
    photoblog = tmp_path / "content" / "photoblog"
    photoblog.mkdir(parents=True)

    galleries = tmp_path / "content" / "galleries"
    (galleries / "alpha").mkdir(parents=True)
    (galleries / "beta").mkdir(parents=True)

    return tmp_path / "content"
