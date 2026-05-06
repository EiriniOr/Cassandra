"""Knowledge fetcher — find articles and save them into the memory raw/ dir
so the wiki maintainer can ingest them later.
"""

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

import requests

RAW = Path.home() / "cassandra-memory" / "raw"


def _slugify(text: str, max_len: int = 60) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower()).strip()
    text = re.sub(r"[-\s]+", "-", text)
    return text[:max_len].strip("-") or "untitled"


def arxiv_search(query: str, max_results: int = 5) -> str:
    url = f"http://export.arxiv.org/api/query?search_query=all:{quote_plus(query)}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except Exception as exc:
        return f"Error: {exc}"
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(resp.text)
    entries = root.findall("a:entry", ns)
    if not entries:
        return f"No arXiv results for '{query}'"
    lines = [f"arXiv results for '{query}':\n"]
    for e in entries:
        title = (e.findtext("a:title", "", ns) or "").strip().replace("\n", " ")
        summary = (
            (e.findtext("a:summary", "", ns) or "").strip().replace("\n", " ")[:300]
        )
        link = e.findtext("a:id", "", ns)
        authors = ", ".join(
            a.findtext("a:name", "", ns) for a in e.findall("a:author", ns)
        )
        published = e.findtext("a:published", "", ns)[:10]
        lines.append(
            f"\n• {title}\n  {authors} — {published}\n  {link}\n  {summary}..."
        )
    return "\n".join(lines)


def hn_top(n: int = 10) -> str:
    try:
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10
        ).json()[:n]
        stories = []
        for sid in ids:
            try:
                s = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=10
                ).json()
                stories.append(s)
            except Exception:
                continue
    except Exception as exc:
        return f"Error: {exc}"
    lines = ["Hacker News top stories:\n"]
    for s in stories:
        title = s.get("title", "(no title)")
        url = s.get("url", f"https://news.ycombinator.com/item?id={s.get('id')}")
        score = s.get("score", 0)
        comments = s.get("descendants", 0)
        lines.append(f"\n• {title}\n  {score} pts, {comments} comments\n  {url}")
    return "\n".join(lines)


def save_article(url: str, project_tag: str = "", note: str = "") -> str:
    """Fetch a URL and save it to ~/cassandra-memory/raw/ as markdown.
    Tag with project for later retrieval.
    """
    RAW.mkdir(parents=True, exist_ok=True)
    try:
        resp = requests.get(url, timeout=20, headers={"User-Agent": "Cassandra/1.0"})
        resp.raise_for_status()
        body = resp.text
    except Exception as exc:
        return f"Error fetching {url}: {exc}"

    title_match = re.search(r"<title[^>]*>([^<]+)</title>", body, re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else url

    body = re.sub(
        r"<script[^>]*>.*?</script>", "", body, flags=re.DOTALL | re.IGNORECASE
    )
    body = re.sub(r"<style[^>]*>.*?</style>", "", body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    if len(body) > 30000:
        body = body[:30000] + "\n\n[truncated]"

    stamp = datetime.now().strftime("%Y-%m-%d")
    slug = _slugify(title)
    path = RAW / f"{stamp}-{slug}.md"

    frontmatter = f"""---
title: {title}
url: {url}
saved: {stamp}
project: {project_tag or "unsorted"}
---

"""
    note_block = f"\n**Why saved:** {note}\n\n" if note else ""
    path.write_text(frontmatter + note_block + body)
    return f"Saved to {path.relative_to(Path.home())} (project: {project_tag or 'unsorted'})"


ARXIV_SCHEMA = {
    "name": "arxiv_search",
    "description": "Search arXiv for recent papers on a topic.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "max_results": {"type": "integer", "description": "default 5"},
        },
        "required": ["query"],
    },
}

HN_SCHEMA = {
    "name": "hn_top",
    "description": "Get top Hacker News stories.",
    "input_schema": {
        "type": "object",
        "properties": {"n": {"type": "integer", "description": "default 10"}},
    },
}

SAVE_SCHEMA = {
    "name": "save_article",
    "description": (
        "Fetch a URL and save it to memory raw/ as markdown for later wiki ingestion. "
        "Tag with project_tag (e.g. 'data_suite', 'cassandra-tools') so you can retrieve "
        "all sources for a project later. Use note to record why it's worth saving."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string"},
            "project_tag": {"type": "string", "description": "Project this relates to"},
            "note": {"type": "string", "description": "Why this is worth keeping"},
        },
        "required": ["url"],
    },
}
