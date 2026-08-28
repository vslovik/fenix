"""Score candidate sources by embedding similarity to a reference — either a source's own
recent content, or a specific matched signal item's text (relevance feedback: find more like
what actually scored well, not more like the aggregator you started with).

One-off discovery utility, not part of the recurring signal_scan.py loop.
"""

import feedparser
import requests

OLLAMA_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"


def embed(text: str) -> list[float]:
    response = requests.post(OLLAMA_URL, json={"model": EMBED_MODEL, "prompt": text}, timeout=30)
    response.raise_for_status()
    return response.json()["embedding"]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def sample_text(feed_url: str, n: int = 5) -> str:
    feed = feedparser.parse(feed_url)
    parts = []
    for entry in feed.entries[:n]:
        parts.append(entry.get("title", ""))
        parts.append(entry.get("summary", ""))
    return "\n".join(parts)


def rank(reference_name: str, reference_text: str, candidates: list[tuple[str, str]]) -> None:
    print(f"[reference] {reference_name}")
    ref_vector = embed(reference_text)

    results = []
    for name, url in candidates:
        print(f"[fetch] {name} — {url}")
        text = sample_text(url)
        if not text.strip():
            print("  ! no entries found, skipping")
            continue
        score = cosine_similarity(ref_vector, embed(text))
        results.append((score, name, url))

    results.sort(reverse=True)
    print(f"\nRanked by similarity to '{reference_name}' (actual fetched content):\n")
    for score, name, url in results:
        print(f"  {score:.3f}  {name}")


if __name__ == "__main__":
    # Relevance feedback: reference is the top-scoring signal item from signals_log.md
    # (score 0.657 against positions/my_target_role.md), not the generic Latent Space feed.
    top_signal_title = "Ontologies Are So Back: Why AI Agents Are Reviving the Semantic Web"
    top_signal_summary = sample_text("https://www.latent.space/feed", n=1)  # picks latest, override below

    # sample_text(n=1) grabs the newest post, not necessarily the top-scoring one — fetch the
    # specific article's own feed entry instead so the reference text is the actual match.
    feed = feedparser.parse("https://www.latent.space/feed")
    match = next((e for e in feed.entries if e.get("title") == top_signal_title), None)
    reference_text = f"{match.title}\n{match.summary}" if match else top_signal_title

    niche_candidates = [
        ("Ken Huang's Substack", "https://kenhuangus.substack.com/feed"),
        ("Context & Chaos", "https://contextandchaos.substack.com/feed"),
        ("WordLift Blog", "https://wordlift.io/blog/en/feed/"),
        ("Year of the Graph Newsletter", "https://yearofthegraph.xyz/feed/"),
    ]
    generic_candidates_for_contrast = [
        ("Simon Willison's Newsletter", "https://simonw.substack.com/feed"),
        ("ThursdAI", "https://sub.thursdai.news/feed"),
    ]

    rank(top_signal_title, reference_text, niche_candidates + generic_candidates_for_contrast)
