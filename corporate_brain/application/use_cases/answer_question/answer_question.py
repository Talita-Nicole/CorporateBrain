"""Use case: retrieve context and generate a source-cited answer."""

import logging
from typing import Iterator

from langchain_core.documents import Document as LangChainDocument
from langchain_core.messages import AIMessage

from domain.entities.message import Message
from domain.interfaces.document_repository import DocumentRepository
from domain.interfaces.guardrail import Guardrail
from domain.interfaces.language_model import LanguageModel

from .models import AnswerResult, RetrievalDebug, RetrievedChunk, StreamingAnswer
from .postprocessing import (
    debug_snippet,
    filter_marker_from_stream,
    parse_question_lines,
    postprocess_answer,
)
from .prompt import (
    PORTUGUESE_LANGUAGE_LABEL,
    build_messages,
    build_numbered_context,
    build_starter_messages,
    detect_answer_language,
)

logger = logging.getLogger(__name__)

RETRIEVER_TOP_K = 4
# Cosine distance cutoff (0..2, lower = more similar). pgvector's default
# space is cosine — a chunk is kept as context only when its distance is at or
# below this value. Overridable per deployment via the MAX_RELEVANT_DISTANCE
# env var (wired in ``composition.build_dependencies``); tune it empirically
# against real in-scope / out-of-scope questions after switching vector store.
MAX_RELEVANT_DISTANCE = 0.6
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 200
STARTER_SAMPLE_SIZE = 8

REFUSAL_MESSAGE_EN = (
    "This request cannot be processed. Please ask a question about the "
    "indexed company documents."
)


class AnswerQuestion:
    """Answers a question over the indexed documents with conversation memory."""

    def __init__(
        self,
        repository: DocumentRepository,
        language_model: LanguageModel,
        guardrail: Guardrail | None = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        embedding_model_name: str = "unknown",
        max_relevant_distance: float = MAX_RELEVANT_DISTANCE,
    ) -> None:
        self._repository = repository
        self._language_model = language_model
        self._guardrail = guardrail
        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap
        self._embedding_model_name = embedding_model_name
        self._max_relevant_distance = max_relevant_distance

    def execute(
        self,
        question: str,
        history: list[Message],
        selected_sources: list[str] | None = None,
        debug: bool = False,
        assistant_name: str = "Knowledge Base",
    ) -> AnswerResult:
        """Generate an answer for ``question`` grounded in retrieved context.

        When ``selected_sources`` is a non-empty list, retrieval is restricted
        to those source files. An empty list or ``None`` searches all indexed
        documents (default behavior).

        The answer language always matches the question's detected language
        — there is no override.

        When a guardrail is configured and flags ``question`` as an obvious
        prompt-injection attempt, the LLM is never called — a safe refusal is
        returned immediately and the attempt is logged.

        ``debug=True`` populates ``AnswerResult.retrieval_debug`` from data
        already computed during retrieval/generation (no extra LLM call).
        """
        if self._guardrail is not None and self._guardrail.screen_question(question):
            logger.warning("Guardrail refused question: %r", question)
            return AnswerResult(
                answer=REFUSAL_MESSAGE_EN,
                sources=[],
                suggested_questions=[],
                refused=True,
            )

        scored_documents, numbered_docs, messages = self._prepare_generation(
            question, history, selected_sources, assistant_name
        )
        chat_model = self._language_model.as_langchain_chat_model()
        response = chat_model.invoke(messages)
        raw_answer = str(response.content)

        answer, sources, suggested_questions = postprocess_answer(
            raw_answer, numbered_docs
        )
        retrieval_debug = (
            self._build_retrieval_debug(scored_documents, response, chat_model)
            if debug
            else None
        )
        return AnswerResult(
            answer=answer,
            sources=sources,
            suggested_questions=suggested_questions,
            retrieval_debug=retrieval_debug,
        )

    def execute_streaming(
        self,
        question: str,
        history: list[Message],
        selected_sources: list[str] | None = None,
        debug: bool = False,
        assistant_name: str = "Knowledge Base",
    ) -> StreamingAnswer:
        """Like ``execute``, but returns a ``StreamingAnswer`` for progressive rendering.

        Consume ``StreamingAnswer.tokens()`` fully (e.g. via ``st.write_stream``)
        before reading ``.result`` — citation renumbering and follow-up
        extraction only run once the full text has arrived, so ``.result`` is
        ``None`` until the token generator is exhausted.

        The ``###FOLLOW_UP###`` marker and everything after it is withheld
        from the token stream (buffered, not yielded) so the user never sees
        the raw marker or the follow-up question list appear inline in the
        answer while it streams.
        """
        streaming_answer = StreamingAnswer()

        if self._guardrail is not None and self._guardrail.screen_question(question):
            logger.warning("Guardrail refused question: %r", question)
            streaming_answer.result = AnswerResult(
                answer=REFUSAL_MESSAGE_EN,
                sources=[],
                suggested_questions=[],
                refused=True,
            )
            streaming_answer._token_generator = iter((REFUSAL_MESSAGE_EN,))
            return streaming_answer

        scored_documents, numbered_docs, messages = self._prepare_generation(
            question, history, selected_sources, assistant_name
        )
        chat_model = self._language_model.as_langchain_chat_model()

        def _generate() -> Iterator[str]:
            raw_chunks: list[str] = []
            merged_chunk = None

            def _pieces() -> Iterator[str]:
                nonlocal merged_chunk
                for chunk in self._language_model.stream(messages):
                    merged_chunk = chunk if merged_chunk is None else merged_chunk + chunk
                    piece = str(chunk.content)
                    if piece:
                        raw_chunks.append(piece)
                        yield piece

            yield from filter_marker_from_stream(_pieces())

            raw_answer = "".join(raw_chunks)
            answer, sources, suggested_questions = postprocess_answer(
                raw_answer, numbered_docs
            )
            retrieval_debug = (
                self._build_retrieval_debug(scored_documents, merged_chunk, chat_model)
                if debug and merged_chunk is not None
                else None
            )
            streaming_answer.result = AnswerResult(
                answer=answer,
                sources=sources,
                suggested_questions=suggested_questions,
                retrieval_debug=retrieval_debug,
            )
            logger.info(
                "Streamed answer; %d source(s) cited, %d suggestion(s)",
                len(sources),
                len(suggested_questions),
            )

        streaming_answer._token_generator = _generate()
        return streaming_answer

    def _prepare_generation(
        self,
        question: str,
        history: list[Message],
        selected_sources: list[str] | None,
        assistant_name: str,
    ) -> tuple[list[tuple[LangChainDocument, float]], dict[int, LangChainDocument], list]:
        """Shared retrieval + prompt-assembly step for ``execute``/``execute_streaming``."""
        resolved_language = detect_answer_language(question)
        source_filter = {"source": {"$in": selected_sources}} if selected_sources else None
        scored_documents = self._repository.similarity_search_with_score(
            question, k=RETRIEVER_TOP_K, filter=source_filter
        )
        documents = [
            doc
            for doc, distance in scored_documents
            if distance <= self._max_relevant_distance
        ]
        numbered_docs = {i + 1: doc for i, doc in enumerate(documents)}
        numbered_context = build_numbered_context(numbered_docs)
        messages = build_messages(
            answer_language=resolved_language,
            numbered_context=numbered_context,
            question=question,
            history=history,
            assistant_name=assistant_name,
        )
        return scored_documents, numbered_docs, messages

    def _build_retrieval_debug(
        self,
        scored_documents: list[tuple[LangChainDocument, float]],
        response: AIMessage,
        chat_model,
    ) -> RetrievalDebug:
        """Assemble debug metadata from data already computed during ``execute``.

        No additional LLM or embedding call is made — token counts come from
        the same ``response`` already generated, and chunk scores from the
        same retrieval already performed.
        """
        retrieved_chunks = [
            RetrievedChunk(
                document_name=doc.metadata.get("source", "unknown"),
                distance=distance,
                passed_threshold=distance <= self._max_relevant_distance,
                snippet=debug_snippet(doc.page_content),
            )
            for doc, distance in scored_documents
        ]
        usage = getattr(response, "usage_metadata", None) or {}
        return RetrievalDebug(
            retrieved_chunks=retrieved_chunks,
            top_k=RETRIEVER_TOP_K,
            max_relevant_distance=self._max_relevant_distance,
            chunk_size=self._chunk_size,
            chunk_overlap=self._chunk_overlap,
            embedding_model=self._embedding_model_name,
            chat_model=getattr(chat_model, "model_name", None)
            or getattr(chat_model, "model", "unknown"),
            input_tokens=usage.get("input_tokens"),
            output_tokens=usage.get("output_tokens"),
            total_tokens=usage.get("total_tokens"),
        )

    def suggest_starters(
        self,
        selected_sources: list[str] | None = None,
        ui_language: str = PORTUGUESE_LANGUAGE_LABEL,
    ) -> list[str]:
        """Propose starter questions from the indexed documents, with no chat yet.

        Samples a handful of chunks (scoped to ``selected_sources`` when given)
        and asks the model for questions a new user might open with. Returns an
        empty list when nothing is indexed, so the UI shows no chips.

        ``ui_language`` (one of ``PORTUGUESE_LANGUAGE_LABEL``/
        ``ENGLISH_LANGUAGE_LABEL``) pins the questions to the interface
        language setting rather than letting them drift with whatever
        language the sampled document excerpts happen to be written in — this
        is unlike ``execute``'s answer language, which intentionally mirrors
        the question instead.
        """
        texts = self._repository.sample_texts(
            limit=STARTER_SAMPLE_SIZE, sources=selected_sources or None
        )
        if not texts:
            return []

        context = "\n\n".join(texts)
        messages = build_starter_messages(context, ui_language)
        chat_model = self._language_model.as_langchain_chat_model()
        response = chat_model.invoke(messages)
        starters = parse_question_lines(str(response.content))
        logger.info("Generated %d starter suggestion(s)", len(starters))
        return starters
