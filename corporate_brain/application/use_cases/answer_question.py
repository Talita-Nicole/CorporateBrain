"""Use case: retrieve context and generate a source-cited answer."""

import logging
from dataclasses import dataclass

from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_core.documents import Document as LangChainDocument
from langchain_core.prompts import PromptTemplate
from langdetect import LangDetectException, detect

from domain.entities.message import Message
from domain.interfaces.document_repository import DocumentRepository
from domain.interfaces.language_model import LanguageModel

logger = logging.getLogger(__name__)

RETRIEVER_TOP_K = 4
SNIPPET_MAX_LENGTH = 300
PORTUGUESE_LANGUAGE_CODE = "pt"


@dataclass
class Source:
    """A document excerpt that supported an answer."""

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
        memory = self._load_memory(history)
        chain = ConversationalRetrievalChain.from_llm(
            llm=self._language_model.as_langchain_chat_model(),
            retriever=self._repository.as_retriever(
                search_kwargs={"k": RETRIEVER_TOP_K}
            ),
            memory=memory,
            return_source_documents=True,
            combine_docs_chain_kwargs={"prompt": self._build_prompt(answer_language)},
        )
        result = chain.invoke({"question": question})
        logger.info("Answered question in %s", answer_language)
        return AnswerResult(
            answer=result["answer"],
            sources=self._build_sources(result.get("source_documents", [])),
        )

    @staticmethod
    def _detect_answer_language(question: str) -> str:
        try:
            language_code = detect(question)
        except LangDetectException:
            return "the same language as the question"
        if language_code == PORTUGUESE_LANGUAGE_CODE:
            return "Portuguese (pt-BR)"
        return "English"

    @staticmethod
    def _load_memory(history: list[Message]) -> ConversationBufferMemory:
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="question",
            output_key="answer",
        )
        pending_question: str | None = None
        for message in history:
            if message.role == "user":
                pending_question = message.content
            elif message.role == "assistant" and pending_question is not None:
                memory.save_context(
                    {"question": pending_question}, {"answer": message.content}
                )
                pending_question = None
        return memory

    @staticmethod
    def _build_prompt(answer_language: str) -> PromptTemplate:
        instructions = (
            "You are a helpful corporate knowledge assistant. Answer questions "
            "based strictly on the context provided below. If the answer is not "
            "found in the context, say so clearly — do not invent information.\n\n"
            f"Always respond in {answer_language}.\n\n"
        )
        template = instructions + (
            "Context:\n{context}\n\n"
            "Question:\n{question}\n\n"
            "Answer:"
        )
        return PromptTemplate(
            input_variables=["context", "question"], template=template
        )

    @staticmethod
    def _build_sources(documents: list[LangChainDocument]) -> list[Source]:
        sources: list[Source] = []
        seen: set[tuple[str, str]] = set()
        for document in documents:
            name = document.metadata.get("source", "unknown")
            snippet = " ".join(document.page_content.split())
            if len(snippet) > SNIPPET_MAX_LENGTH:
                snippet = snippet[:SNIPPET_MAX_LENGTH].rstrip() + "…"
            key = (name, snippet)
            if key in seen:
                continue
            seen.add(key)
            sources.append(Source(document_name=name, snippet=snippet))
        return sources
