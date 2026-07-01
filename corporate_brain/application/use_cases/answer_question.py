"""Use case: retrieve context and generate a source-cited answer."""

import logging
import re
from dataclasses import dataclass

from langchain_core.documents import Document as LangChainDocument
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langdetect import LangDetectException, detect_langs

from domain.entities.message import Message
from domain.interfaces.document_repository import DocumentRepository
from domain.interfaces.language_model import LanguageModel

logger = logging.getLogger(__name__)

RETRIEVER_TOP_K = 4
SNIPPET_MAX_LENGTH = 300
ENGLISH_LANGUAGE_CODE = "en"
ENGLISH_CONFIDENCE_THRESHOLD = 0.85


@dataclass
class Source:
    """A document excerpt that supported an answer."""

    citation_number: int
    document_name: str
    snippet: str


@dataclass
class AnswerResult:
    """The generated answer together with its supporting sources."""

    answer: str
    sources: list[Source]


class AnswerQuestion:
    """Answers a question over the indexed documents with conversation memory."""

    def __init__(
        self,
        repository: DocumentRepository,
        language_model: LanguageModel,
    ) -> None:
        self._repository = repository
        self._language_model = language_model

    def execute(self, question: str, history: list[Message]) -> AnswerResult:
        """Generate an answer for ``question`` grounded in retrieved context."""
        answer_language = self._detect_answer_language(question)
        retriever = self._repository.as_retriever(search_kwargs={"k": RETRIEVER_TOP_K})
        documents = retriever.invoke(question)
        numbered_docs = {i + 1: doc for i, doc in enumerate(documents)}
        numbered_context = self._build_numbered_context(numbered_docs)

        messages = self._build_messages(
            answer_language=answer_language,
            numbered_context=numbered_context,
            question=question,
            history=history,
        )
        chat_model = self._language_model.as_langchain_chat_model()
        response = chat_model.invoke(messages)
        answer = str(response.content)

        answer, sources = self._renumber_citations(answer, numbered_docs)
        logger.info(
            "Answered question in %s; %d source(s) cited", answer_language, len(sources)
        )
        return AnswerResult(answer=answer, sources=sources)

    @staticmethod
    def _detect_answer_language(question: str) -> str:
        try:
            langs = detect_langs(question)
            top = langs[0]
            if top.lang == ENGLISH_LANGUAGE_CODE and top.prob >= ENGLISH_CONFIDENCE_THRESHOLD:
                return "English"
        except LangDetectException:
            pass
        return "Portuguese (pt-BR)"

    @staticmethod
    def _build_numbered_context(numbered_docs: dict[int, LangChainDocument]) -> str:
        parts = []
        for number, doc in numbered_docs.items():
            parts.append(f"[{number}] {doc.page_content}")
        return "\n\n".join(parts)

    @classmethod
    def _build_messages(
        cls,
        answer_language: str,
        numbered_context: str,
        question: str,
        history: list[Message],
    ) -> list:
        """Assemble the chat message list: system prompt, history, then the
        numbered context together with the current question."""
        system_prompt = (
            "You are a helpful corporate knowledge assistant. Answer questions "
            "based strictly on the context provided below. If the answer is not "
            "found in the context, say so clearly — do not invent information.\n\n"
            f"Always respond in {answer_language}.\n\n"
            "Each excerpt is prefixed with a number like [1], [2], etc. "
            "When you use information from an excerpt, cite its number inline, "
            "e.g. 'According to the document [1]...'. Only cite numbers that "
            "appear in the context."
        )
        messages: list = [SystemMessage(content=system_prompt)]
        messages.extend(cls._history_to_messages(history))
        messages.append(
            HumanMessage(
                content=(
                    f"Context:\n{numbered_context}\n\n"
                    f"Question:\n{question}"
                )
            )
        )
        return messages

    @staticmethod
    def _history_to_messages(history: list[Message]) -> list:
        converted: list = []
        for message in history:
            if message.role == "user":
                converted.append(HumanMessage(content=message.content))
            elif message.role == "assistant":
                converted.append(AIMessage(content=message.content))
        return converted

    @classmethod
    def _renumber_citations(
        cls,
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
