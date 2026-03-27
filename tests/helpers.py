from pathlib import Path
from PIL import Image


def make_test_image(path, width=4000, height=3000, color=(100, 100, 100)):
    """Create a test JPEG image. Images smaller than a target resize are not upscaled."""
    img = Image.new("RGB", (width, height), color=color)
    img.save(path, "JPEG")
    return path
