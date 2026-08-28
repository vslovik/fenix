"""Local embeddings and generation via Ollama. No API keys, no rate limits."""

import requests

OLLAMA_HOST = "http://localhost:11434"
EMBED_URL = f"{OLLAMA_HOST}/api/embeddings"
GENERATE_URL = f"{OLLAMA_HOST}/api/generate"

EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "qwen2.5:7b"


def embed(text: str) -> list[float]:
    response = requests.post(
        EMBED_URL, json={"model": EMBED_MODEL, "prompt": text}, timeout=60
    )
    response.raise_for_status()
    return response.json()["embedding"]


def generate(prompt: str, model: str = CHAT_MODEL, temperature: float = 0.1) -> str:
    """One-shot completion. Low temperature: this is extraction, not writing."""
    response = requests.post(
        GENERATE_URL,
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        },
        timeout=300,
    )
    response.raise_for_status()
    return response.json()["response"].strip()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0