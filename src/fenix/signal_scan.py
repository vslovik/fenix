"""Fetch new items from signal sources, rank by similarity to each file in positions/, log all.

Generalized (2026-08-15): not just "your job search" — any position (your own target role, a
role you're recruiting for, anything) is a file in positions/, scored against the same
incoming stream in one run. Each new item's embedding is computed once and compared against
every position vector (cheap — no extra network calls per position).

Local embeddings via Ollama (nomic-embed-text), no API keys, no rate limits.
See sources.yaml for the seed list, positions/README.md for the position-file format.
"""

import json
import re
from pathlib import Path

import feedparser
import yaml

from .embedding import cosine_similarity, embed

ROOT = Path(__file__).resolve().parents[2]
SEARCH_DIR = ROOT / "search"
SOURCES_FILE = SEARCH_DIR / "sources.yaml"
STATE_FILE = ROOT / ".state" / "signal_scan_seen.json"
LOG_FILE = SEARCH_DIR / "signals_log.md"
POSITIONS_DIR = SEARCH_DIR / "positions"


def load_positions() -> dict:
    """Returns {name: {"tags": [...], "vector": [...]}} for every .md file in positions/."""
    positions = {}
    for path in sorted(POSITIONS_DIR.glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text()
        tags = []
        frontmatter_match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
        if frontmatter_match:
            front = yaml.safe_load(frontmatter_match.group(1)) or {}
            tags = front.get("tags", [])
            text = text[frontmatter_match.end():]
        positions[path.stem] = {"tags": tags, "vector": embed(text)}
    return positions


def load_sources() -> dict:
    return yaml.safe_load(SOURCES_FILE.read_text())


def load_seen() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_seen(seen: dict) -> None:
    STATE_FILE.parent.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(seen, indent=2))


def scan() -> None:
    sources = load_sources()
    seen = load_seen()
    positions = load_positions()
    if not positions:
        print("No position files found in positions/ — nothing to score against.")
        return

    new_entries = []  # each: {source, title, link, published, scores: {position_name: score}}

    for source in sources.get("signal_sources", []):
        name = source["name"]
        if source.get("status") != "active":
            print(f"[skip] {name} — status: {source.get('status')} "
                  f"({source.get('note', 'no reason given')})")
            continue

        print(f"[fetch] {name} — {source['url']}")
        feed = feedparser.parse(source["url"])
        if feed.bozo and not feed.entries:
            print(f"  ! failed to parse feed for {name}: {feed.bozo_exception}")
            continue

        seen_ids = set(seen.get(name, []))
        new_ids = []
        for entry in feed.entries:
            entry_id = entry.get("id") or entry.get("link")
            if not entry_id or entry_id in seen_ids:
                continue
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            item_vector = embed(f"{title}\n{summary}")
            scores = {pname: cosine_similarity(p["vector"], item_vector)
                      for pname, p in positions.items()}
            new_entries.append({
                "source": name, "title": title, "link": entry.get("link", ""),
                "published": entry.get("published", ""), "scores": scores,
            })
            new_ids.append(entry_id)

        if new_ids:
            seen.setdefault(name, []).extend(new_ids)
        print(f"  {len(new_ids)} new item(s)")

    if new_entries:
        append_to_log(new_entries, positions)
    save_seen(seen)


def append_to_log(entries: list[dict], positions: dict) -> None:
    from datetime import datetime, timezone

    lines = [f"\n## Scan — {datetime.now(timezone.utc).isoformat(timespec='minutes')}",
             f"({len(entries)} new item(s) this run)\n"]
    for pname, pdata in positions.items():
        tag_str = f" ({', '.join(pdata['tags'])})" if pdata["tags"] else ""
        lines.append(f"### {pname}{tag_str}\n")
        ranked = sorted(entries, key=lambda e: e["scores"][pname], reverse=True)
        for entry in ranked:
            lines.append(f"- **{entry['scores'][pname]:.3f}** [{entry['title']}]({entry['link']}) "
                          f"— {entry['source']}, {entry['published']}")
        lines.append("")

    with LOG_FILE.open("a") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    scan()
