import json
import re
import shutil
from html import escape
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).parent
SOURCE = ROOT / "src"
OUTPUT = ROOT / "dist"
PAGE_IDS = ("home", "about", "making", "features", "gallery", "press", "contact", "thanks")
LOCALES = ("cs", "en", "de")


def read_json(path):
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def site_root_url(site):
    parsed = urlsplit(site.get("baseUrl", ""))
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("src/site.json must contain an absolute http(s) baseUrl")
    if parsed.query or parsed.fragment:
        raise ValueError("baseUrl must not include a query or fragment")
    return site["baseUrl"].rstrip("/") + "/"


def page_url_path(locale, page_id, pages):
    prefix = "" if locale == "cs" else locale + "/"
    slug = pages[locale][page_id]["slug"].strip("/")
    return prefix + (slug + "/" if slug else "")


def page_href(locale, page_id, pages):
    return "./" + page_url_path(locale, page_id, pages)


def nav_link(locale, page_id, current_page, pages, labels):
    current = ' aria-current="page"' if current_page == page_id else ""
    active = ' class="is-active"' if current_page == page_id else ""
    href = escape(page_href(locale, page_id, pages), quote=True)
    label = escape(labels["nav"][page_id])
    return '<li><a href="' + href + '" data-fast-nav' + active + current + ">" + label + "</a></li>"


def build_header(template, locale, page_id, pages, labels, locales):
    links = "\n".join(
        nav_link(locale, item, page_id, pages, labels)
        for item in PAGE_IDS
        if item not in ("home", "thanks")
    )
    language_links = []
    language_flags = {"cs": "🇨🇿", "en": "🇬🇧", "de": "🇩🇪"}
    for language in LOCALES:
        current = ' aria-current="true"' if language == locale else ""
        language_links.append(
            '<a href="' + escape(page_href(language, page_id, pages), quote=True)
            + '" hreflang="' + language + '" lang="' + language
            + '" data-fast-nav' + current + ">"
            + '<span aria-hidden="true">' + language_flags[language] + "</span> "
            + escape(locales[language]["languageName"]) + "</a>"
        )

    values = {
        "MENU_LABEL": labels["menuLabel"],
        "NAVIGATION_LABEL": labels["navigationLabel"],
        "LANGUAGE_LABEL": labels["languageLabel"],
        "CURRENT_LANGUAGE_FLAG": language_flags[locale],
        "CURRENT_LANGUAGE_NAME": escape(labels["languageName"]),
        "CONTACT_CTA": labels["contactCta"],
        "NAV_LINKS": links,
        "LANGUAGE_LINKS": "\n".join(language_links),
    }
    return replace_placeholders(template, values)


def build_footer(template, locale, pages, labels):
    link_items = []
    for page_id in PAGE_IDS:
        if page_id == "thanks":
            continue
        link_items.append(
            '<li><a href="' + escape(page_href(locale, page_id, pages), quote=True)
            + '" data-fast-nav>' + escape(labels["nav"][page_id]) + "</a></li>"
        )
    values = {
        "FOOTER_INTRO": labels["footerIntro"],
        "FOOTER_PAGES_TITLE": labels["footerPagesTitle"],
        "FOOTER_CONTACT_TITLE": labels["footerContactTitle"],
        "FOOTER_PAGE_LINKS": "\n".join(link_items),
        "WORKSHOP_LABEL": labels["workshopLabel"],
        "FOOTER_TAGLINE": labels["footerTagline"],
    }
    return replace_placeholders(template, values)


def replace_placeholders(template, values):
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", value)
    unresolved = re.findall(r"\{\{[A-Z_]+\}\}", template)
    if unresolved:
        raise ValueError("Unresolved layout placeholders: " + ", ".join(unresolved))
    return template


def rewrite_page_links(markup, locale, pages):
    def replace_anchor(match):
        tag = match.group(0)
        page_match = re.search(r'\sdata-page-id="([^"]+)"', tag)
        if not page_match:
            return tag
        destination = page_match.group(1)
        if destination not in PAGE_IDS:
            raise ValueError("Unknown page link: " + destination)
        href = escape(page_href(locale, destination, pages), quote=True)
        tag = re.sub(r'\shref="[^"]*"', ' href="' + href + '"', tag, count=1)
        tag = re.sub(r'\sdata-page-id="[^"]*"', "", tag, count=1)
        if "data-fast-nav" not in tag:
            tag = tag[:-1] + " data-fast-nav>"
        return tag

    return re.sub(r"<a\b[^>]*>", replace_anchor, markup)


def build_document(locale, page_id, page, content, templates, locales, pages, site_root):
    labels = locales[locale]
    canonical = site_root + page_url_path(locale, page_id, pages)
    alternates = []
    for alternate_locale in LOCALES:
        alternates.append(
            '    <link rel="alternate" hreflang="' + alternate_locale
            + '" href="' + escape(
                site_root + page_url_path(alternate_locale, page_id, pages),
                quote=True,
            ) + '">'
        )
    alternates.append(
        '    <link rel="alternate" hreflang="x-default" href="'
        + escape(site_root + page_url_path("cs", page_id, pages), quote=True) + '">'
    )
    head = (
        "<!DOCTYPE html>\n<html lang=\"" + escape(labels["htmlLang"], quote=True) + "\">\n"
        + "<head>\n"
        + '    <base href="' + escape(site_root, quote=True) + '">\n'
        + templates["head"]
        + "\n    <title>" + escape(page["title"]) + "</title>\n"
        + '    <meta name="description" content="'
        + escape(page["description"], quote=True) + '">\n'
        + '    <meta name="robots" content="'
        + escape(page["robots"], quote=True) + '">\n'
        + '    <link rel="canonical" href="' + escape(canonical, quote=True) + '">\n'
        + "\n".join(alternates)
        + "\n</head>\n"
    )
    header = build_header(templates["header"], locale, page_id, pages, labels, locales)
    footer = build_footer(templates["footer"], locale, pages, labels)
    header = rewrite_page_links(header, locale, pages)
    footer = rewrite_page_links(footer, locale, pages)
    content = rewrite_page_links(content, locale, pages)
    header = re.sub(
        r'class="header(?![^"]*\bheader--solid)([^"]*)"',
        lambda match: 'class="header header--solid' + match.group(1) + '"'
        if page_id != "home" else match.group(0),
        header,
        count=1,
    )
    content = content.replace(
        'name="redirect" value="#dekujeme"',
        'name="redirect" value="'
        + escape(site_root + page_url_path(locale, "thanks", pages), quote=True)
        + '"',
    )
    if page_id == "home":
        hero = re.search(r'<section\b[^>]*class="hero"[^>]*>', content)
        if not hero:
            raise ValueError("The home page must contain a .hero section")
        content = content[:hero.end()] + "\n" + header + content[hero.end():]
    document = (
        head + "<body>\n"
        + ("" if page_id == "home" else header + "\n")
        + '<main id="page-content">\n' + content + "\n</main>\n"
        + footer
        + '\n<script src="gallery.js" defer></script>\n'
        + '<script src="site-router.js" defer></script>\n'
        + "</body>\n</html>\n"
    )
    return document, canonical


def validate_sources(locales, pages):
    if set(locales) != set(LOCALES) or set(pages) != set(LOCALES):
        raise ValueError("The site must define exactly the cs, en and de locales")
    for locale in LOCALES:
        if set(pages[locale]) != set(PAGE_IDS):
            raise ValueError("Page ids do not match in " + locale + "/pages.json")
        for page_id in PAGE_IDS:
            source = SOURCE / "pages" / locale / (page_id + ".html")
            page = pages[locale][page_id]
            if not source.is_file() or not source.read_text(encoding="utf-8").strip():
                raise ValueError("Missing or empty page source: " + str(source))
            if not page.get("title") or not page.get("description") or "slug" not in page:
                raise ValueError("Incomplete metadata for " + locale + "/" + page_id)


def main():
    site = read_json(SOURCE / "site.json")
    site_root = site_root_url(site)
    locales = read_json(SOURCE / "locales.json")
    pages = {
        locale: read_json(SOURCE / "pages" / locale / "pages.json")
        for locale in LOCALES
    }
    validate_sources(locales, pages)
    templates = {
        name: (SOURCE / "partials" / (name + ".html")).read_text(encoding="utf-8")
        for name in ("head", "header", "footer")
    }

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir()
    for name in ("style.css", "gallery.js", "site-router.js"):
        shutil.copy2(ROOT / name, OUTPUT / name)
    for asset in (ROOT / "img").rglob("*"):
        if asset.is_file():
            target = OUTPUT / "img" / asset.relative_to(ROOT / "img")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(asset, target)

    sitemap_urls = []
    for locale in LOCALES:
        for page_id in PAGE_IDS:
            page = pages[locale][page_id]
            content = (SOURCE / "pages" / locale / (page_id + ".html")).read_text(
                encoding="utf-8"
            ).strip()
            document, canonical = build_document(
                locale, page_id, page, content, templates, locales, pages, site_root
            )
            path = page_url_path(locale, page_id, pages)
            target_dir = OUTPUT / path.rstrip("/") if path else OUTPUT
            target_dir.mkdir(parents=True, exist_ok=True)
            (target_dir / "index.html").write_text(document, encoding="utf-8")
            if page["robots"] != "noindex":
                sitemap_urls.append((locale, page_id, canonical))

    sitemap_entries = []
    for locale, page_id, canonical in sitemap_urls:
        alternates = "".join(
            '<xhtml:link rel="alternate" hreflang="' + alternate_locale
            + '" href="' + escape(
                site_root + page_url_path(alternate_locale, page_id, pages)
            ) + '"/>'
            for alternate_locale in LOCALES
        )
        sitemap_entries.append(
            "  <url><loc>" + escape(canonical) + "</loc>" + alternates + "</url>\n"
        )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
        + "".join(sitemap_entries)
        + "</urlset>\n"
    )
    (OUTPUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (OUTPUT / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nSitemap: " + site_root + "sitemap.xml\n",
        encoding="utf-8",
    )
    hostname = urlsplit(site_root).hostname
    if hostname and not hostname.endswith("github.io"):
        (OUTPUT / "CNAME").write_text(hostname + "\n", encoding="utf-8")
    (OUTPUT / ".nojekyll").write_text("", encoding="utf-8")
    print("Built", len(LOCALES) * len(PAGE_IDS), "static pages in", OUTPUT)


if __name__ == "__main__":
    main()
