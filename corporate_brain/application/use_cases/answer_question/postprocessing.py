"""Post-processing of raw model output: citation renumbering and follow-ups."""

import re
from typing import Iterable, Iterator

from langchain_core.documents import Document as LangChainDocument

from .models import Source
from .prompt import MAX_SUGGESTIONS, SUGGESTIONS_MARKER

SNIPPET_MAX_LENGTH = 300
DEBUG_SNIPPET_MAX_LENGTH = 160


def filter_marker_from_stream(pieces: Iterable[str]) -> Iterator[str]:
    """Yield ``pieces`` unchanged up to (excluding) ``SUGGESTIONS_MARKER``.

    Buffers just enough trailing text to detect the marker as it straddles
    chunk boundaries, so the marker and everything after it (the follow-up
    question block) never reaches the caller.
    """
    buffer = ""
    marker_prefix_len = len(SUGGESTIONS_MARKER) - 1
    marker_seen = False
    for piece in pieces:
        if not piece or marker_seen:
            continue
        buffer += piece
        if SUGGESTIONS_MARKER in buffer:
            marker_seen = True
            visible, _, _ = buffer.partition(SUGGESTIONS_MARKER)
            if visible:
                yield visible
            buffer = ""
            continue
        safe_len = max(0, len(buffer) - marker_prefix_len)
        if safe_len:
            yield buffer[:safe_len]
            buffer = buffer[safe_len:]
    if buffer and not marker_seen:
        yield buffer


def debug_snippet(text: str) -> str:
    snippet = " ".join(text.split())
    if len(snippet) > DEBUG_SNIPPET_MAX_LENGTH:
        return snippet[:DEBUG_SNIPPET_MAX_LENGTH].rstrip() + "…"
    return snippet


def parse_question_lines(text: str) -> list[str]:
    """Extract up to ``MAX_SUGGESTIONS`` questions from a bullet/numbered list."""
    questions: list[str] = []
    for line in text.splitlines():
        question = re.sub(r"^\s*(?:[-*]|\d+[.)])\s*", "", line).strip()
        if question:
            questions.append(question)
        if len(questions) == MAX_SUGGESTIONS:
            break
    return questions


def split_suggestions(raw_answer: str) -> tuple[str, list[str]]:
    """Separate the answer body from the trailing follow-up block.

    The model is asked to append ``SUGGESTIONS_MARKER`` followed by up to
    ``MAX_SUGGESTIONS`` bullet questions. When the marker is absent the
    answer is returned unchanged with no suggestions (no generic fallback).
    """
    if SUGGESTIONS_MARKER not in raw_answer:
        return raw_answer.strip(), []

    answer_part, _, suggestions_part = raw_answer.partition(SUGGESTIONS_MARKER)
    return answer_part.strip(), parse_question_lines(suggestions_part)


def renumber_citations(
    answer: str,
    numbered_docs: dict[int, LangChainDocument],
) -> tuple[str, list[Source]]:
    """Rewrite the ``[n]`` markers in ``answer`` to a contiguous ``1..N``
    sequence based on first appearance, and return the matching sources.

    The model cites documents by their original retrieval position (e.g.
    ``[3]``), which is confusing when only a subset is cited. This maps the
    cited originals to display numbers in the order they appear in the text,
    keeping the answer and the sources panel consistent and starting at 1.
    """
    original_numbers = [int(n) for n in re.findall(r"\[(\d+)\]", answer)]
    display_by_original: dict[int, int] = {}
    for original in original_numbers:
        if original in numbered_docs and original not in display_by_original:
            display_by_original[original] = len(display_by_original) + 1

    if not display_by_original:
        return answer, []

    def _replace(match: re.Match) -> str:
        original = int(match.group(1))
        display = display_by_original.get(original)
        return f"[{display}]" if display is not None else match.group(0)

    renumbered_answer = re.sub(r"\[(\d+)\]", _replace, answer)

    sources: list[Source] = []
    for original, display in display_by_original.items():
        document = numbered_docs[original]
        name = document.metadata.get("source", "unknown")
        snippet = " ".join(document.page_content.split())
        if len(snippet) > SNIPPET_MAX_LENGTH:
            snippet = snippet[:SNIPPET_MAX_LENGTH].rstrip() + "…"
        sources.append(
            Source(citation_number=display, document_name=name, snippet=snippet)
        )
    return renumbered_answer, sources


def postprocess_answer(
    raw_answer: str, numbered_docs: dict[int, LangChainDocument]
) -> tuple[str, list[Source], list[str]]:
    """Split off follow-ups and renumber citations on the complete answer text."""
    answer, suggested_questions = split_suggestions(raw_answer)
    answer, sources = renumber_citations(answer, numbered_docs)
    return answer, sources, suggested_questions
