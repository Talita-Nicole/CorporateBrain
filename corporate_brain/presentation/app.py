"""Composition root and Streamlit page layout."""

import logging
import os
from typing import Optional

import streamlit as st
from pydantic import ValidationError

from application.use_cases.answer_question import AnswerQuestion
from application.use_cases.ingest_document import IngestDocument
from domain.interfaces.embedder import Embedder
from domain.interfaces.language_model import LanguageModel
from infrastructure.chroma_document_repository import ChromaDocumentRepository
from infrastructure.config.azure_settings import AzureSettings
from infrastructure.config.github_models_settings import GitHubModelsSettings
from infrastructure.llm_errors import LLMServiceError
from infrastructure.loaders.loader_factory import LangChainDocumentLoader
from presentation.components.chat import render_chat
from presentation.components.sidebar import render_sidebar

logger = logging.getLogger(__name__)

PAGE_TITLE = "Knowledge Base"
DEFAULT_PERSIST_DIR = "./chroma_db"
GITHUB_PROVIDER = "github"
AZURE_PROVIDER = "azure"


def run() -> None:
    """Render the application; the entrypoint configures env and logging first."""
    st.set_page_config(page_title=PAGE_TITLE, page_icon="📚", layout="wide")
    st.title(PAGE_TITLE)

    chat_provider = os.getenv("LLM_PROVIDER", AZURE_PROVIDER).strip().lower()
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", AZURE_PROVIDER).strip().lower()
    providers = (chat_provider, embedding_provider)

    try:
        azure_settings = AzureSettings() if AZURE_PROVIDER in providers else None
        github_settings = (
            GitHubModelsSettings() if GITHUB_PROVIDER in providers else None
        )
    except ValidationError as error:
        logger.error("Invalid settings: %s", error)
        st.error(
            "Missing or invalid configuration. Copy .env.example to .env, "
            "fill in the required variables and restart the app."
        )
        return

    try:
        ingest_use_case, answer_use_case, repository = _build_dependencies(
            chat_provider, embedding_provider, azure_settings, github_settings
        )
    except LLMServiceError as error:
        logger.error("Cannot build providers: %s", error)
        st.error(str(error))
        return

    render_sidebar(ingest_use_case, repository)
    render_chat(answer_use_case)


@st.cache_resource(show_spinner=False)
def _build_dependencies(
    chat_provider: str,
    embedding_provider: str,
    _azure_settings: Optional[AzureSettings],
    _github_settings: Optional[GitHubModelsSettings],
) -> tuple[IngestDocument, AnswerQuestion, ChromaDocumentRepository]:
    embedder = _build_embedder(embedding_provider, _azure_settings, _github_settings)
    language_model = _build_language_model(
        chat_provider, _azure_settings, _github_settings
    )
    repository = ChromaDocumentRepository(
        embedder=embedder,
        persist_directory=os.getenv("CHROMA_PERSIST_DIR", DEFAULT_PERSIST_DIR),
    )
    loader = LangChainDocumentLoader()
    ingest_use_case = IngestDocument(loader=loader, repository=repository)
    answer_use_case = AnswerQuestion(
        repository=repository, language_model=language_model
    )
    return ingest_use_case, answer_use_case, repository


def _build_embedder(
    provider: str,
    azure_settings: Optional[AzureSettings],
    github_settings: Optional[GitHubModelsSettings],
) -> Embedder:
    if provider == GITHUB_PROVIDER and github_settings is not None:
        return github_settings.get_embedding_client()
    if azure_settings is not None:
        return azure_settings.get_embedding_client()
    raise LLMServiceError("Embeddings configuration is missing.")


def _build_language_model(
    provider: str,
    azure_settings: Optional[AzureSettings],
    github_settings: Optional[GitHubModelsSettings],
) -> LanguageModel:
    if provider == GITHUB_PROVIDER and github_settings is not None:
        return github_settings.get_llm_client()
    if azure_settings is not None:
        return azure_settings.get_llm_client()
    raise LLMServiceError("Chat model configuration is missing.")
