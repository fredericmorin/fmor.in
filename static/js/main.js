/* fmor.in — slideshow & lightbox navigation */
(function () {
    "use strict";

    // --- Shared utilities ---

    function buildPicture(photo, sizes) {
        var avifSrcset = photo.sizes.map(function (s) {
            return photo.base + "-" + s + ".avif " + s + "w";
        }).join(", ");
        var jpgSrcset = photo.sizes.map(function (s) {
            return photo.base + "-" + s + ".jpg " + s + "w";
        }).join(", ");

        var fallbackSize = photo.sizes.indexOf(1920) !== -1 ? 1920 : photo.sizes[Math.floor(photo.sizes.length / 2)];
        return '<source type="image/avif" srcset="' + avifSrcset + '" sizes="' + sizes + '">' +
            '<source type="image/jpeg" srcset="' + jpgSrcset + '" sizes="' + sizes + '">' +
            '<img src="' + photo.base + '-' + fallbackSize + '.jpg"' +
            ' alt="' + (photo.alt || "") + '">';
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
        if (date) html += '<span class="exif-date">' + date + '</span>';
        html += '<span class="exif-fields">' + fields.join(" \u00b7 ") + '</span>';
        html += '</div>';
        return html;
    }

    var avifSupported = null;

    function detectAvif(callback) {
        if (avifSupported !== null) { callback(avifSupported); return; }
        var probe = new Image();
        probe.onload = function () { avifSupported = true; callback(true); };
        probe.onerror = function () { avifSupported = false; callback(false); };
        probe.src = "data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAABcAAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAIAAAACAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQAMAAAAABNjb2xybmNseAACAAIAAYAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAAB9tZGF0EgAKCBgABogQEAwgMg==";
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

    function initSlideshow() {
        if (!window.PHOTOS || window.PHOTOS.length === 0) return;

        var hash = location.hash.replace("#", "");
        if (hash) {
            var idx = window.PHOTOS.findIndex(function (p) { return p.slug === hash; });
            if (idx !== -1) slideshowIndex = idx;
        }

        showSlide(slideshowIndex);

        window.addEventListener("hashchange", function () {
            var h = location.hash.replace("#", "");
            var idx = window.PHOTOS.findIndex(function (p) { return p.slug === h; });
            if (idx !== -1) showSlide(idx);
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
        if (counter) counter.textContent = (index + 1) + " / " + photos.length;

        var exifEl = document.getElementById("exif-container");
        if (exifEl) exifEl.innerHTML = buildExif(photo.exif, photo.date);

        location.hash = "#" + photo.slug;

        // Preload adjacent
        if (index > 0) preloadImage(photos[index - 1]);
        if (index < photos.length - 1) preloadImage(photos[index + 1]);
    }

    window.navigatePhoto = function (delta) {
        var photos = window.PHOTOS;
        if (!photos) return;
        var next = slideshowIndex + delta;
        if (next >= 0 && next < photos.length) showSlide(next);
    };

    // --- Lightbox (Gallery) ---

    var lightboxIndex = 0;
    var lightboxOpen = false;
    var previousFocus = null;

    window.openLightbox = function (index) {
        if (!window.GALLERY_PHOTOS) return;
        previousFocus = document.activeElement;
        lightboxIndex = index;
        lightboxOpen = true;
        document.body.style.overflow = "hidden";

        var lb = document.getElementById("lightbox");
        if (lb) lb.classList.add("open");

        showLightboxPhoto(index);

        // Focus the close button for accessibility
        var closeBtn = document.querySelector(".lightbox-close");
        if (closeBtn) closeBtn.focus();
    };

    window.closeLightbox = function () {
        lightboxOpen = false;
        document.body.style.overflow = "";

        var lb = document.getElementById("lightbox");
        if (lb) lb.classList.remove("open");

        location.hash = "";

        if (previousFocus) previousFocus.focus();
    };

    window.navigateLightbox = function (delta) {
        var photos = window.GALLERY_PHOTOS;
        if (!photos) return;
        var next = lightboxIndex + delta;
        if (next >= 0 && next < photos.length) showLightboxPhoto(next);
    };

    function showLightboxPhoto(index) {
        var photos = window.GALLERY_PHOTOS;
        if (!photos || index < 0 || index >= photos.length) return;

        lightboxIndex = index;
        var photo = photos[index];

        var picture = document.getElementById("lightbox-picture");
        if (picture) picture.innerHTML = buildPicture(photo, "100vw");

        var counter = document.getElementById("lightbox-counter");
        if (counter) counter.textContent = (index + 1) + " / " + photos.length;

        var exifEl = document.getElementById("lightbox-exif");
        if (exifEl) exifEl.innerHTML = buildExif(photo.exif, photo.date);

        location.hash = "#" + (index + 1);

        // Preload adjacent
        if (index > 0) preloadImage(photos[index - 1]);
        if (index < photos.length - 1) preloadImage(photos[index + 1]);
    }

    // --- Focus trap for lightbox ---

    function trapFocus(e) {
        if (!lightboxOpen) return;
        if (e.key !== "Tab") return;

        var lb = document.getElementById("lightbox");
        var focusable = lb.querySelectorAll('button, [role="button"][tabindex="0"]');
        if (focusable.length === 0) return;

        var first = focusable[0];
        var last = focusable[focusable.length - 1];

        if (e.shiftKey) {
            if (document.activeElement === first) {
                e.preventDefault();
                last.focus();
            }
        } else {
            if (document.activeElement === last) {
                e.preventDefault();
                first.focus();
            }
        }
    }

    // --- Keyboard navigation ---

    document.addEventListener("keydown", function (e) {
        if (lightboxOpen) {
            trapFocus(e);
            if (e.key === "Escape") { closeLightbox(); return; }
            if (e.key === "ArrowLeft") { navigateLightbox(-1); return; }
            if (e.key === "ArrowRight") { navigateLightbox(1); return; }
            return;
        }

        if (window.PHOTOS) {
            if (e.key === "ArrowLeft") navigatePhoto(-1);
            if (e.key === "ArrowRight") navigatePhoto(1);
        }
    });


    // --- Lightbox backdrop click to close ---

    document.addEventListener("click", function (e) {
        if (!lightboxOpen) return;
        var lb = document.getElementById("lightbox");
        var photoArea = document.querySelector(".lightbox-photo");
        // Close if click is on the lightbox backdrop, not on a child interactive element
        if (e.target === lb || e.target === photoArea) closeLightbox();
    });

    // --- Lightbox hash deep-linking ---

    function checkGalleryHash() {
        if (!window.GALLERY_PHOTOS) return;
        var hash = parseInt(location.hash.replace("#", ""), 10);
        if (hash > 0 && hash <= window.GALLERY_PHOTOS.length) {
            openLightbox(hash - 1);
        }
    }

    // --- Init ---

    document.addEventListener("DOMContentLoaded", function () {
        if (window.PHOTOS) initSlideshow();
        if (window.GALLERY_PHOTOS) checkGalleryHash();
    });
})();
