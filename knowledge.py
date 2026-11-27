import math
import re
from functools import lru_cache
from pathlib import Path

from .ollama_client import embed

_GUIDE_PATH = Path(__file__).resolve().parent.parent / "data" / "it_operations_guide.md"
_MIN_SIMILARITY = 0.4
_NO_ANSWER = {
    "title": "No relevant information found",
    "content": "I couldn't find relevant information in the IT operations guide. Please contact the IT service desk.",
    "score": 0.0,
}


@lru_cache(maxsize=1)
def _load_sections():
    guide = _GUIDE_PATH.read_text(encoding="utf-8")
    headings = list(re.finditer(r"(?m)^#{1,6}\s+(.+?)\s*$", guide))
    sections = []

    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(guide)
        content = guide[heading.end():end].strip()
        if content:
            title = heading.group(1).strip()
            sections.append((title, content, embed(f"{title}\n{content}")))

    return sections


def _cosine_similarity(left, right):
    if len(left) != len(right):
        raise ValueError("Embedding vectors must have the same dimensions")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def search_it_guide(question):
    if not isinstance(question, str) or not question.strip():
        raise ValueError("question must be a non-empty string")

    sections = _load_sections()
    if not sections:
        return _NO_ANSWER.copy()

    question_embedding = embed(question.strip())
    best_section = max(
        sections,
        key=lambda section: _cosine_similarity(question_embedding, section[2]),
    )
    title, content, section_embedding = best_section
    score = _cosine_similarity(question_embedding, section_embedding)

    if score < _MIN_SIMILARITY:
        return {**_NO_ANSWER, "score": score}
    return {"title": title, "content": content, "score": score}