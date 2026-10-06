#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from datetime import datetime
from email.utils import format_datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import bibtexparser
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
TEMPLATE_DIR = ROOT / "templates"
GENERATED_DIR = ROOT


def load_yaml(name: str) -> list[dict[str, Any]]:
    path = DATA_DIR / f"{name}.yaml"
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, list):
        raise ValueError(f"{path} must contain a top-level list")
    return data


def bib_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.replace("{", "").replace("}", "").split())


def split_authors(author_field: str) -> list[str]:
    return [bib_text(part) for part in re.split(r"\s+and\s+", author_field) if part.strip()]


def highlight_author(author: str) -> str:
    escaped = html.escape(author)
    assert author != "Guo, Mingyu"
    if author == "Mingyu Guo":
        return f"<strong>{escaped}</strong>"
    return escaped


def load_publications() -> list[dict[str, str | bool]]:
    with (DATA_DIR / "mingyu_publications.bib").open(encoding="utf-8") as handle:
        database = bibtexparser.load(handle)

    publications = []
    for entry in database.entries:
        selected = bib_text(entry.get("selected", "false")).lower()
        if selected not in {"true", "false"}:
            raise ValueError(f"{entry['ID']}: selected must be true or false")
        authors = split_authors(entry.get("author", ""))
        venue = bib_text(entry.get("journal") or entry.get("booktitle") or entry.get("school"))
        notes = [part.strip() for part in bib_text(entry.get("note")).split(",") if part.strip()]
        ranking = next((part for part in notes if part.startswith(("CORE ", "CCF-", "ERA-", "ABDC "))), "")
        publications.append({
            "selected": selected == "true",
            "authors_html": ", ".join(highlight_author(author) for author in authors),
            "title": bib_text(entry.get("title")),
            "venue": venue,
            "venue_short": bib_text(entry.get("venue_short")) or venue,
            "year": bib_text(entry.get("year")),
            "ranking": ranking,
            "notes": ", ".join(part for part in notes if part != ranking),
            "clarification": bib_text(entry.get("clarification")),
            "summary": bib_text(entry.get("summary")),
            "link": bib_text(entry.get("url")),
        })
    return publications


def render_site() -> None:
    GENERATED_DIR.mkdir(exist_ok=True)
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html", "xml", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    publications = load_publications()
    stylesheet_version = sha256((ROOT / "static" / "site.css").read_bytes()).hexdigest()[:12]
    last_updated = format_datetime(datetime.now().astimezone())
    html_text = env.get_template("index.html.j2").render(
        highlights=load_yaml("highlights"),
        news=load_yaml("news"),
        students=load_yaml("students"),
        presentations=load_yaml("presentations"),
        services=load_yaml("services"),
        grants=load_yaml("grants"),
        publications=[paper for paper in publications if paper["selected"]],
        stylesheet_version=stylesheet_version,
        last_updated=last_updated,
    )
    (GENERATED_DIR / "index.html").write_text(html_text, encoding="utf-8")
    publications_html = env.get_template("publications.html.j2").render(
        publications=publications,
        stylesheet_version=stylesheet_version,
        last_updated=last_updated,
    )
    (GENERATED_DIR / "publications.html").write_text(publications_html, encoding="utf-8")


def main() -> None:
    render_site()
    print(f"Generated {GENERATED_DIR / 'index.html'}")
    print(f"Generated {GENERATED_DIR / 'publications.html'}")


if __name__ == "__main__":
    main()
