import requests

from .config import CHAT_MODEL, EMBED_MODEL, OLLAMA_BASE_URL

_TIMEOUT = (5, 120)


def _post(endpoint, payload):
    url = f"{OLLAMA_BASE_URL.rstrip('/')}{endpoint}"
    try:
        response = requests.post(url, json=payload, timeout=_TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise RuntimeError(f"Ollama request timed out: {url}") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc

    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError(f"Ollama returned invalid JSON: {url}") from exc


def generate(prompt):
    result = _post(
        "/api/generate",
        {"model": CHAT_MODEL, "prompt": prompt, "stream": False},
    )
    text = result.get("response")
    if not isinstance(text, str):
        raise RuntimeError("Ollama generate response is missing a text response")
    return text


def embed(text):
    result = _post("/api/embed", {"model": EMBED_MODEL, "input": text})
    embeddings = result.get("embeddings")
    if not isinstance(embeddings, list) or not embeddings:
        raise RuntimeError("Ollama embed response is missing embeddings")
    return embeddings[0]
