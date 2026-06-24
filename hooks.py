"""MkDocs hooks for SEO / LLM artifacts."""

from __future__ import annotations

import shutil
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, tostring


def on_post_build(config, **kwargs) -> None:
    site_dir = Path(config["site_dir"])
    root = Path(config["config_file_path"]).parent
    site_url = config["site_url"].rstrip("/")

    for name in ("llms.txt", ".nojekyll"):
        src = root / name
        if src.is_file():
            shutil.copy2(src, site_dir / name)

    urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
    for html in sorted(site_dir.rglob("*.html")):
        if html.name == "404.html":
            continue
        rel = html.relative_to(site_dir).as_posix()
        if rel == "index.html":
            loc = f"{site_url}/"
        elif rel.endswith("/index.html"):
            loc = f"{site_url}/{rel.removesuffix('index.html').rstrip('/')}/"
        else:
            loc = f"{site_url}/{rel}"
        url = SubElement(urlset, "url")
        SubElement(url, "loc").text = loc

    (site_dir / "sitemap.xml").write_bytes(
        b'<?xml version="1.0" encoding="UTF-8"?>\n' + tostring(urlset, encoding="utf-8")
    )
