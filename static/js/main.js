/* fmor.in — slideshow navigation */
(function () {
  "use strict";

  // --- Shared utilities ---

  function buildPicture(photo, sizes) {
    var avifSrcset = photo.sizes
      .map(function (s) {
        return photo.base + "-" + s + ".avif " + s + "w";
      })
      .join(", ");
    var jpgSrcset = photo.sizes
      .map(function (s) {
        return photo.base + "-" + s + ".jpg " + s + "w";
      })
      .join(", ");

    var fallbackSize =
      photo.sizes.indexOf(1920) !== -1 ? 1920 : photo.sizes[Math.floor(photo.sizes.length / 2)];
    return (
      '<source type="image/avif" srcset="' +
      avifSrcset +
      '" sizes="' +
      sizes +
      '">' +
      '<source type="image/jpeg" srcset="' +
      jpgSrcset +
      '" sizes="' +
      sizes +
      '">' +
      '<img src="' +
      photo.base +
      "-" +
      fallbackSize +
      '.jpg"' +
      ' alt="' +
      (photo.alt || "") +
      '">'
    );
  }

  function buildExif(exif, date) {
    if (!exif || Object.keys(exif).length === 0) return "";
    var fields = [];
    if (exif.camera) fields.push(exif.camera);
    if (exif.lens) fields.push(exif.lens);
    if (exif.focal_length) fields.push(exif.focal_length + "mm");
    if (exif.aperture) fields.push("\u0192/" + exif.aperture);
    if (exif.shutter_speed) fields.push(exif.shutter_speed + "s");
    if (exif.iso) fields.push("ISO " + exif.iso);
    // if (exif.white_balance) fields.push(exif.white_balance);
    // if (exif.metering) fields.push(exif.metering);
    // if (exif.exposure_comp) fields.push(exif.exposure_comp + " EV");

    var html = '<div class="exif-bar">';
    if (date) html += '<span class="exif-date">' + date + "</span>";
    html += '<span class="exif-fields">' + fields.join(" \u00b7 ") + "</span>";
    html += "</div>";
    return html;
  }

  var avifSupported = null;

  function detectAvif(callback) {
    if (avifSupported !== null) {
      callback(avifSupported);
      return;
    }
    var probe = new Image();
    probe.onload = function () {
      avifSupported = true;
      callback(true);
    };
    probe.onerror = function () {
      avifSupported = false;
      callback(false);
    };
    probe.src =
      "data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAABcAAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAIAAAACAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQAMAAAAABNjb2xybmNseAACAAIAAYAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAAB9tZGF0EgAKCBgABogQEAwgMg==";
  }

  function pickSize(sizes) {
    var cssWidth = window.innerWidth || document.documentElement.clientWidth;
    var dpr = window.devicePixelRatio || 1;
    var target = cssWidth * dpr;
    for (var i = 0; i < sizes.length; i++) {
      if (sizes[i] >= target) return sizes[i];
    }
    return sizes[sizes.length - 1];
  }

  function preloadImage(photo) {
    var size = pickSize(photo.sizes);
    detectAvif(function (avif) {
      var img = new Image();
      img.src = photo.base + "-" + size + (avif ? ".avif" : ".jpg");
    });
  }

  // --- Slideshow (Photoblog) ---

  var slideshowIndex = 0;
  var slideshowBasePath = "";
  var gridVisible = false;

  function initSlideshow() {
    if (!window.PHOTOS || window.PHOTOS.length === 0) return;

    slideshowBasePath = location.pathname;

    var hash = location.hash.replace("#", "");

    // Populate inline grid
    var gridEl = document.getElementById("photoblog-grid-thumbnails");
    if (gridEl) {
      gridEl.innerHTML = window.PHOTOS.map(function (photo, i) {
        return (
          '<div class="thumbnail" role="button" tabindex="0"' +
          ' aria-label="' +
          (photo.alt || "Photo " + (i + 1)) +
          '"' +
          ' onclick="navigateFromGrid(' +
          i +
          ')">' +
          "<picture>" +
          buildPicture(photo, "(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw") +
          "</picture>" +
          "</div>"
        );
      }).join("");
    }

    if (hash === "gallery" || !hash) {
      showPhotoblogGrid();
    } else {
      var idx = window.PHOTOS.findIndex(function (p) {
        return p.slug === hash;
      });
      if (idx !== -1) slideshowIndex = idx;
      showSlide(slideshowIndex);
    }

    window.addEventListener("popstate", function () {
      var h = location.hash.replace("#", "");
      if (h === "gallery") {
        showPhotoblogGrid();
      } else {
        var idx = window.PHOTOS.findIndex(function (p) {
          return p.slug === h;
        });
        if (idx !== -1) showSlide(idx);
      }
    });
  }

  function showSlide(index) {
    var photos = window.PHOTOS;
    if (!photos || index < 0 || index >= photos.length) return;

    slideshowIndex = index;
    var photo = photos[index];

    var picture = document.getElementById("photo-picture");
    if (picture) picture.innerHTML = buildPicture(photo, "100vw");

    var counter = document.getElementById("photo-counter");
    if (counter) counter.textContent = index + 1 + " / " + photos.length;

    var exifEl = document.getElementById("exif-container");
    if (exifEl) exifEl.innerHTML = buildExif(photo.exif, photo.date);

    history.replaceState(null, "", slideshowBasePath + "#" + photo.slug);

    // Preload adjacent only when slideshow is visible
    if (!gridVisible) {
      if (index > 0) preloadImage(photos[index - 1]);
      if (index < photos.length - 1) preloadImage(photos[index + 1]);
    }
  }

  window.navigatePhoto = function (delta) {
    var photos = window.PHOTOS;
    if (!photos) return;
    var next = slideshowIndex + delta;
    if (next >= 0 && next < photos.length) showSlide(next);
  };

  window.showPhotoblogGrid = function (e) {
    if (e) e.preventDefault();
    var slideshow = document.getElementById("slideshow");
    var gridView = document.getElementById("photoblog-grid-view");
    if (slideshow) slideshow.style.display = "none";
    if (gridView) gridView.style.display = "";
    gridVisible = true;
    history.replaceState(null, "", slideshowBasePath + "#gallery");
    var thumbs = document.querySelectorAll("#photoblog-grid-thumbnails .thumbnail");
    if (thumbs[slideshowIndex]) {
      thumbs[slideshowIndex].scrollIntoView({ block: "center", behavior: "instant" });
    }
  };

  window.hidePhotoblogGrid = function (e) {
    if (e) e.preventDefault();
    var slideshow = document.getElementById("slideshow");
    var gridView = document.getElementById("photoblog-grid-view");
    if (slideshow) slideshow.style.display = "";
    if (gridView) gridView.style.display = "none";
    gridVisible = false;
    var photo = window.PHOTOS && window.PHOTOS[slideshowIndex];
    history.replaceState(null, "", slideshowBasePath + (photo ? "#" + photo.slug : ""));
  };

  window.navigateFromGrid = function (index) {
    window.hidePhotoblogGrid();
    showSlide(index);
  };

  // --- Keyboard navigation ---

  document.addEventListener("keydown", function (e) {
    if (window.PHOTOS && !gridVisible) {
      if (e.key === "ArrowLeft") navigatePhoto(-1);
      if (e.key === "ArrowRight") navigatePhoto(1);
      if (e.key === "Escape") showPhotoblogGrid();
    }
  });

  // --- Encourage Safari to collapse its UI on landscape rotation ---

  window.addEventListener("orientationchange", function () {
    setTimeout(function () {
      window.scrollTo(0, 1);
      setTimeout(function () {
        window.scrollTo(0, 0);
      }, 50);
    }, 300);
  });

  // --- Init ---

  document.addEventListener("DOMContentLoaded", function () {
    if (window.PHOTOS) initSlideshow();
  });
})();
