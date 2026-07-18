#!/usr/bin/env python3
from __future__ import annotations

import html
import re
from datetime import datetime
from email.utils import format_datetime
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


def volume_number_pages(entry: dict[str, str]) -> str:
    fields = [
        ("Volume", bib_text(entry.get("volume"))),
        ("Number", bib_text(entry.get("number"))),
        ("Pages", bib_text(entry.get("pages")).replace("--", "–")),
    ]
    if any(value == "To appear" for _, value in fields):
        return "To appear"
    return ", ".join(f"{label} {value}" for label, value in fields if value)


def load_publications() -> list[dict[str, str]]:
    with (DATA_DIR / "mingyu_publications.bib").open(encoding="utf-8") as handle:
        database = bibtexparser.load(handle)

    publications = []
    for entry in database.entries:
        authors = split_authors(entry.get("author", ""))
        publications.append({
            "authors_html": ", ".join(highlight_author(author) for author in authors),
            "title": bib_text(entry.get("title")),
            "venue": bib_text(entry.get("journal") or entry.get("booktitle")),
            "volume_number_pages": volume_number_pages(entry),
            "year": bib_text(entry.get("year")),
            "ranking": bib_text(entry.get("note")),
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
    template = env.get_template("index.html.j2")
    html_text = template.render(
        news=load_yaml("news"),
        students=load_yaml("students"),
        presentations=load_yaml("presentations"),
        services=load_yaml("services"),
        grants=load_yaml("grants"),
        publications=load_publications(),
        last_updated=format_datetime(datetime.now().astimezone()),
    )
    (GENERATED_DIR / "index.html").write_text(html_text, encoding="utf-8")


def main() -> None:
    render_site()
    print(f"Generated {GENERATED_DIR / 'index.html'}")


if __name__ == "__main__":
    main()
