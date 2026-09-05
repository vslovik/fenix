"""Score every position anchor against labelled probe postings.

The method in lessons/embedding-anchors.md, made repeatable. A probe is a short synthetic
posting in search/probes/, marked `want: true` or `want: false`. The unwanted ones are the
control: an edit that lifts the wanted scores and the unwanted ones alike has changed the
anchor's verbosity, not its aim, and without a control every edit looks like an improvement.

Three numbers, because a ranking on its own hides things:

    separation   mean(wanted) - mean(unwanted)    is the anchor aimed at all
    margin       min(wanted)  - max(unwanted)     is a clean cutoff possible
    inversions   wanted/unwanted pairs out of order, out of every such pair

Separation can look healthy while a single unwanted probe sits in the middle of the wanted
ones; margin is the number that catches that, and it is the one that decides whether a
threshold could ever be used to filter automatically.

Each run is compared against the previous one and then replaces it, so the before/after the
lesson asks for is the default rather than something to remember. Nothing here touches the
network beyond the local embedding calls, and nothing here reads the corpus — the point is a
measurement that holds still while the anchor changes.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from .embedding import cosine_similarity, embed
from .signal_scan import load_positions, split_frontmatter

ROOT = Path(__file__).resolve().parents[2]
PROBES_DIR = ROOT / "search" / "probes"
BASELINE_FILE = ROOT / ".state" / "score_baseline.json"


def load_probes() -> list[dict]:
    """Returns [{"name", "label", "want", "vector"}] for every .md file in probes/."""
    probes = []
    for path in sorted(PROBES_DIR.glob("*.md")):
        if path.name == "README.md":
            continue
        front, body = split_frontmatter(path.read_text())
        probes.append({
            "name": path.stem,
            "label": front.get("label", path.stem),
            "want": bool(front.get("want", True)),
            "vector": embed(body),
        })
    return probes


def metrics(scored: list[tuple[float, bool]]) -> dict | None:
    """Separation, margin and inversion count over (score, want) pairs.

    Returns None when one of the two groups is empty — with no control there is nothing to
    measure against, and reporting a number anyway would be worse than reporting none.
    """
    wanted = [s for s, want in scored if want]
    unwanted = [s for s, want in scored if not want]
    if not wanted or not unwanted:
        return None
    inversions = sum(1 for w in wanted for u in unwanted if u > w)
    return {
        "wanted_mean": sum(wanted) / len(wanted),
        "unwanted_mean": sum(unwanted) / len(unwanted),
        "separation": sum(wanted) / len(wanted) - sum(unwanted) / len(unwanted),
        "margin": min(wanted) - max(unwanted),
        "inversions": inversions,
        "pairs": len(wanted) * len(unwanted),
    }


def load_baseline() -> dict:
    if BASELINE_FILE.exists():
        return json.loads(BASELINE_FILE.read_text())
    return {}


def save_baseline(scores: dict) -> None:
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_FILE.write_text(json.dumps(
        {"run_at": datetime.now(timezone.utc).isoformat(timespec="minutes"), "scores": scores},
        indent=2,
    ))


def score(save: bool = True) -> None:
    positions = load_positions()
    if not positions:
        print("No position files in search/positions/ — nothing to score.")
        return

    probes = load_probes()
    if not probes:
        print("No probe files in search/probes/ — nothing to score against.")
        print("See search/probes/README.md for the format.")
        return

    baseline = load_baseline()
    previous = baseline.get("scores", {})
    if previous:
        print(f"comparing against the run at {baseline.get('run_at', 'unknown time')}\n")

    label_width = max(len(p["label"]) for p in probes)
    current = {}

    for name, position in positions.items():
        tags = f"  ({', '.join(position['tags'])})" if position["tags"] else ""
        print(f"{name}{tags}  {position['chars']:,} chars\n")

        ranked = sorted(
            ((cosine_similarity(position["vector"], p["vector"]), p) for p in probes),
            key=lambda row: row[0],
            reverse=True,
        )
        current[name] = {p["name"]: value for value, p in ranked}
        was = previous.get(name, {})

        for value, probe in ranked:
            mark = "want" if probe["want"] else "SKIP"
            delta = ""
            if probe["name"] in was:
                change = value - was[probe["name"]]
                delta = f"   {change:+.3f}" if abs(change) >= 0.0005 else "     ----"
            print(f"  {value:.3f}  {mark}  {probe['label']:<{label_width}}{delta}")

        summary = metrics([(value, p["want"]) for value, p in ranked])
        print()
        if summary is None:
            print("  every probe points the same way — add a control before trusting this")
        else:
            print(f"  separation  {summary['separation']:+.3f}   "
                  f"wanted {summary['wanted_mean']:.3f} / unwanted {summary['unwanted_mean']:.3f}")
            print(f"  margin      {summary['margin']:+.3f}   " + (
                "clean gap between the groups" if summary["margin"] > 0
                else "the groups overlap — no threshold separates them"))
            print(f"  inversions  {summary['inversions']}/{summary['pairs']} pairs out of order")
        print()

    if save:
        save_baseline(current)
