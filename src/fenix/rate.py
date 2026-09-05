"""Rate scan results by hand, then compare your judgement against the ranking.

The scan ranks incoming items against a position anchor. Nothing so far has ever
checked whether that ranking agrees with the person it is ranking for — every other
measurement in this repo is a proxy. This is the ground truth, and it can only come
from a human reading titles.

Two choices in here matter more than the code:

**Scores are hidden while you rate.** If you see the ranker's answer first you will
agree with it, and the labels stop being independent of the thing they are measuring.

**Items are shuffled.** The log is written in descending score order, so presenting
them in file order would leak the ranking even with the numbers removed.

Ratings are written to search/ratings.md — readable, diffable, and committed, because
a labelled set is worth more than the code that collected it and takes far longer to
rebuild.
"""

import random
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG_FILE = ROOT / "search" / "signals_log.md"
RATINGS_FILE = ROOT / "search" / "ratings.md"

SCAN_RE = re.compile(r"^## Scan — (\S+)")
POSITION_RE = re.compile(r"^### (\S+)")
ITEM_RE = re.compile(r"^- \*\*([0-9.]+)\*\* \[(.+)\]\((\S+)\) — (.*)$")

SCALE = {
    "2": "on target — would read this",
    "1": "borderline — interesting, not the target",
    "0": "off target",
}

HEADER = """# Ratings — human judgement of scan results

Written by `fenix rate`. Each block records what a person thought of one scan's
results, independently of how the anchor scored them: scores are hidden and the order
is shuffled during rating, so these labels are not downstream of the ranking.

| rating | meaning |
|---|---|
| **2** | on target — would read this |
| **1** | borderline — interesting, but not the target |
| **0** | off target |

This file is the only ground truth in the repo. Everything else — probe scores,
separation, drift — is a proxy for it.
"""


def parse_scans(text: str) -> list[dict]:
    """Every scored scan block in the log, oldest first.

    Blocks with no scored items are skipped: the earliest logged scans predate scoring
    and were grouped by source instead, so they parse to nothing and are not scans in
    the sense this command means.
    """
    scans, scan, position = [], None, None
    for line in text.splitlines():
        if match := SCAN_RE.match(line):
            scan = {"at": match.group(1), "positions": {}}
            scans.append(scan)
            position = None
        elif (match := POSITION_RE.match(line)) and scan is not None:
            position = match.group(1)
            scan["positions"][position] = []
        elif (match := ITEM_RE.match(line)) and position is not None:
            score, title, link, tail = match.groups()
            source, _, published = tail.partition(", ")
            scan["positions"][position].append({
                "score": float(score), "title": title, "link": link,
                "source": source, "published": published,
            })
    return [s for s in scans if any(s["positions"].values())]


def precision_at_k(ranked: list[dict], k: int, threshold: int = 2) -> tuple[int, int]:
    """How many of the top k the person rated at or above `threshold`, and how many exist.

    The denominator is min(k, total relevant): with only three relevant items in the
    set, 3/5 is a perfect score, and dividing by k would report it as a failure of the
    ranker rather than a property of the day's stream.
    """
    relevant = sum(1 for item in ranked if item["rating"] >= threshold)
    hits = sum(1 for item in ranked[:k] if item["rating"] >= threshold)
    return hits, min(k, relevant)


def report(ranked: list[dict], scan_at: str, position: str) -> None:
    """Print the ranking with the human labels beside it."""
    print(f"\n{position} — scan {scan_at}\n")
    for rank, item in enumerate(ranked, 1):
        mark = {2: "  ON", 1: "   ~", 0: "  off"}[item["rating"]]
        print(f"  {rank:>2}.  {item['score']:.3f} {mark}  {item['title'][:64]}")

    print()
    for k in (5, 10):
        if len(ranked) < k:
            continue
        hits, possible = precision_at_k(ranked, k)
        if possible:
            print(f"  precision@{k:<3} {hits}/{possible} of the on-target items are in the top {k}")

    on = [r for r, item in enumerate(ranked, 1) if item["rating"] == 2]
    if on:
        print(f"  on-target items sit at ranks: {', '.join(str(r) for r in on)}")
        if max(on) > len(ranked) / 2:
            print(f"  ! one is at rank {max(on)} of {len(ranked)} — the anchor is missing something it wants")
    else:
        print("  nothing was rated on target — either the sources are wrong or the day was quiet")


def rate() -> None:
    if not LOG_FILE.exists():
        print(f"No log at {LOG_FILE} — run `fenix scan` first.")
        return

    scans = parse_scans(LOG_FILE.read_text())
    if not scans:
        print("No scored scans in the log yet.")
        return

    scan = scans[-1]
    position, items = next(iter(scan["positions"].items()))
    print(f"Scan {scan['at']} — {position} — {len(items)} items")
    print("Scores are hidden and the order is shuffled, so your judgement stays independent.")
    print("  2 = on target · 1 = borderline · 0 = off target · s = skip · q = save and stop\n")

    order = items[:]
    random.shuffle(order)
    rated = []
    for n, item in enumerate(order, 1):
        print(f"[{n}/{len(order)}] {item['title']}")
        print(f"          {item['source']} · {item['published']}")
        while True:
            answer = input("          rating: ").strip().lower()
            if answer in SCALE:
                item["rating"] = int(answer)
                rated.append(item)
                break
            if answer == "s":
                break
            if answer == "q":
                write_ratings(scan["at"], position, rated)
                print(f"\nStopped. {len(rated)} rated, saved to {RATINGS_FILE}")
                return
            print("          2, 1, 0, s or q")
        print()

    write_ratings(scan["at"], position, rated)
    print(f"{len(rated)} rated, saved to {RATINGS_FILE}")
    report(sorted(rated, key=lambda i: i["score"], reverse=True), scan["at"], position)


def write_ratings(scan_at: str, position: str, rated: list[dict]) -> None:
    if not rated:
        return
    ranked = sorted(rated, key=lambda i: i["score"], reverse=True)
    lines = [f"\n## Scan — {scan_at} · {position}",
             f"Rated {date.today().isoformat()}. {len(rated)} items.\n",
             "| rating | score | rank | item |", "|---|---|---|---|"]
    for rank, item in enumerate(ranked, 1):
        lines.append(f"| {item['rating']} | {item['score']:.3f} | {rank} | "
                     f"[{item['title']}]({item['link']}) — {item['source']} |")

    if not RATINGS_FILE.exists():
        RATINGS_FILE.write_text(HEADER)
    with RATINGS_FILE.open("a") as f:
        f.write("\n".join(lines) + "\n")