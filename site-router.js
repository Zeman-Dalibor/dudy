"use strict";

(function () {
    const cache = new Map();
    let navigationId = 0;
    const siteBase = new URL(document.querySelector("base").href);

    function isSiteUrl(url) {
        return url.origin === siteBase.origin &&
            url.pathname.indexOf(siteBase.pathname) === 0;
    }

    function loadPage(url) {
        const key = url.href;
        if (!cache.has(key)) {
            const request = fetch(key).then(function (response) {
                if (!response.ok) {
                    throw new Error("Page request failed: " + response.status);
                }
                return response.text();
            }).then(function (html) {
                const page = new DOMParser().parseFromString(html, "text/html");
                if (!page.querySelector("#page-content") || !page.title) {
                    throw new Error("The requested URL did not return a site page");
                }
                return page;
            });
            cache.set(key, request.catch(function (error) {
                cache.delete(key);
                throw error;
            }));
        }
        return cache.get(key);
    }

    function updateMetadata(page) {
        document.title = page.title;
        document.documentElement.lang = page.documentElement.lang;
        ["description", "robots"].forEach(function (name) {
            const next = page.querySelector('meta[name="' + name + '"]');
            let current = document.querySelector('meta[name="' + name + '"]');
            if (!next) {
                if (current) current.remove();
                return;
            }
            if (!current) {
                current = document.createElement("meta");
                current.name = name;
                document.head.appendChild(current);
            }
            current.content = next.content;
        });

        document.head.querySelectorAll('link[rel="canonical"], link[rel="alternate"]')
            .forEach(function (link) {
                link.remove();
            });
        page.head.querySelectorAll('link[rel="canonical"], link[rel="alternate"]')
            .forEach(function (link) {
                document.head.appendChild(link.cloneNode(true));
            });
    }

    function initMediaFavicons() {
        document.querySelectorAll(
            'a.media-link[href^="http://"], a.media-link[href^="https://"], ' +
            '.media-award__links a[href^="http://"], .media-award__links a[href^="https://"]'
        ).forEach(function (link) {
            if (link.querySelector(".link-favicon")) return;
            const favicon = document.createElement("img");
            favicon.className = "link-favicon";
            favicon.src = "https://www.google.com/s2/favicons?domain=" +
                encodeURIComponent(new URL(link.href).hostname) + "&sz=32";
            favicon.alt = "";
            favicon.setAttribute("aria-hidden", "true");
            favicon.width = 32;
            favicon.height = 32;
            favicon.loading = "lazy";
            favicon.decoding = "async";
            link.prepend(favicon);
        });
    }

    async function navigate(url, addHistory) {
        const requestId = ++navigationId;
        document.documentElement.setAttribute("aria-busy", "true");
        try {
            const page = await loadPage(url);
            if (requestId !== navigationId) return;
            if (addHistory) window.history.pushState({}, "", url);
            document.body.innerHTML = page.body.innerHTML;
            updateMetadata(page);
            if (typeof window.initGallery === "function") window.initGallery();
            initMediaFavicons();
            window.scrollTo(0, 0);
        } catch (error) {
            console.error("Could not load the requested page without reloading.", error);
            window.location.assign(url.href);
        } finally {
            if (requestId === navigationId) {
                document.documentElement.removeAttribute("aria-busy");
            }
        }
    }

    function pageLink(target) {
        if (!target || target.target === "_blank" || target.hasAttribute("download")) {
            return null;
        }
        const url = new URL(target.href, window.location.href);
        return isSiteUrl(url) ? url : null;
    }

    document.addEventListener("click", function (event) {
        if (event.defaultPrevented || event.button !== 0 ||
            event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;

        const link = event.target.closest("a[data-fast-nav][href]");
        const url = pageLink(link);
        if (!url || url.href === window.location.href) return;

        event.preventDefault();
        navigate(url, true);
    });

    function prefetchLink(event) {
        const link = event.target.closest("a[data-fast-nav][href]");
        const url = pageLink(link);
        if (url) {
            loadPage(url).catch(function (error) {
                console.error("Could not prefetch the requested page.", error);
            });
        }
    }

    document.addEventListener("pointerover", prefetchLink);
    document.addEventListener("focusin", prefetchLink);
    window.addEventListener("popstate", function () {
        const url = new URL(window.location.href);
        if (isSiteUrl(url)) navigate(url, false);
    });
})();
