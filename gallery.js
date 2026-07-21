/* ==========================================================================
   Lightbox pro galerii – bez závislostí
   Klik na obrázek jej zvětší přes celou obrazovku.
   Ovládání: šipky ←/→ pro procházení, Esc pro zavření, klik mimo obrázek zavře.
   ========================================================================== */
(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        var gallery = document.querySelector(".gallery");
        if (!gallery) return;

        // Sesbírej pouze položky, které obsahují skutečný obrázek
        var items = Array.prototype.filter.call(
            gallery.querySelectorAll(".gallery__item"),
            function (item) { return item.querySelector("img"); }
        );
        if (!items.length) return;

        // Data pro lightbox (plná verze přes data-full, jinak src)
        var slides = items.map(function (item) {
            var img = item.querySelector("img");
            var cap = item.querySelector(".gallery__cap");
            return {
                src: img.getAttribute("data-full") || img.src,
                alt: img.alt || "",
                caption: cap ? cap.textContent.trim() : (img.alt || "")
            };
        });

        // Zpřístupni položky a doplň ikonu lupy
        var zoomIcon = '<span class="gallery__zoom" aria-hidden="true">' +
            '<svg viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="6.5" stroke="currentColor" stroke-width="1.6"/>' +
            '<path d="M16 16l4 4M11 8.5v5M8.5 11h5" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/></svg></span>';

        items.forEach(function (item, index) {
            item.classList.add("is-zoomable");
            item.setAttribute("tabindex", "0");
            item.setAttribute("role", "button");
            item.setAttribute("aria-label", "Zvětšit obrázek: " + slides[index].caption);
            item.insertAdjacentHTML("beforeend", zoomIcon);

            item.addEventListener("click", function () { open(index); });
            item.addEventListener("keydown", function (e) {
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    open(index);
                }
            });
        });

        // Sestav lightbox
        var lb = document.createElement("div");
        lb.className = "lightbox";
        lb.setAttribute("role", "dialog");
        lb.setAttribute("aria-modal", "true");
        lb.setAttribute("aria-label", "Zvětšený obrázek");
        lb.innerHTML =
            '<div class="lightbox__backdrop" data-close></div>' +
            '<button class="lightbox__btn lightbox__close" type="button" aria-label="Zavřít">' +
                '<svg viewBox="0 0 24 24" fill="none"><path d="M6 6l12 12M18 6L6 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>' +
            '</button>' +
            '<button class="lightbox__btn lightbox__prev" type="button" aria-label="Předchozí">' +
                '<svg viewBox="0 0 24 24" fill="none"><path d="M15 5l-7 7 7 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>' +
            '</button>' +
            '<button class="lightbox__btn lightbox__next" type="button" aria-label="Další">' +
                '<svg viewBox="0 0 24 24" fill="none"><path d="M9 5l7 7-7 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>' +
            '</button>' +
            '<figure class="lightbox__stage">' +
                '<img class="lightbox__img" src="" alt="">' +
                '<figcaption class="lightbox__cap"></figcaption>' +
                '<span class="lightbox__counter"></span>' +
            '</figure>';
        document.body.appendChild(lb);

        var imgEl = lb.querySelector(".lightbox__img");
        var capEl = lb.querySelector(".lightbox__cap");
        var counterEl = lb.querySelector(".lightbox__counter");
        var btnPrev = lb.querySelector(".lightbox__prev");
        var btnNext = lb.querySelector(".lightbox__next");
        var current = 0;
        var lastFocused = null;

        // Skryj navigaci, pokud je jen jeden obrázek
        if (slides.length < 2) {
            btnPrev.style.display = "none";
            btnNext.style.display = "none";
        }

        function render() {
            var s = slides[current];
            imgEl.src = s.src;
            imgEl.alt = s.alt;
            capEl.textContent = s.caption;
            counterEl.textContent = (current + 1) + " / " + slides.length;
        }

        function open(index) {
            current = index;
            lastFocused = document.activeElement;
            render();
            lb.classList.add("is-open");
            document.documentElement.style.overflow = "hidden";
            document.addEventListener("keydown", onKey);
            lb.querySelector(".lightbox__close").focus();
        }

        function close() {
            lb.classList.remove("is-open");
            document.documentElement.style.overflow = "";
            document.removeEventListener("keydown", onKey);
            imgEl.src = "";
            if (lastFocused && typeof lastFocused.focus === "function") lastFocused.focus();
        }

        function next() { current = (current + 1) % slides.length; render(); }
        function prev() { current = (current - 1 + slides.length) % slides.length; render(); }

        function onKey(e) {
            if (e.key === "Escape") close();
            else if (e.key === "ArrowRight") next();
            else if (e.key === "ArrowLeft") prev();
        }

        btnNext.addEventListener("click", next);
        btnPrev.addEventListener("click", prev);
        lb.querySelector(".lightbox__close").addEventListener("click", close);
        lb.querySelectorAll("[data-close]").forEach(function (el) {
            el.addEventListener("click", close);
        });
    });
})();
