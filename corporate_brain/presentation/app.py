"""Composition root and Streamlit page layout."""

import logging
import os
from typing import Optional

import streamlit as st
from pydantic import ValidationError

from application.use_cases.answer_question import AnswerQuestion
from application.use_cases.ingest_document import IngestDocument
from domain.interfaces.session_repository import SessionRepository
from infrastructure.chroma_document_repository import ChromaDocumentRepository
from infrastructure.config.app_settings import load_app_settings
from infrastructure.config.azure_settings import AzureSettings
from infrastructure.config.github_models_settings import GitHubModelsSettings
from infrastructure.config.groq_settings import GroqSettings
from infrastructure.config.postgres_settings import PostgresSettings
from infrastructure.config.providers import (
    AZURE_PROVIDER,
    GITHUB_PROVIDER,
    GROQ_PROVIDER,
    build_embedder,
    build_language_model,
)
from infrastructure.guardrails import PatternGuardrail
from infrastructure.llm_errors import LLMServiceError
from infrastructure.loaders.loader_factory import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    LangChainDocumentLoader,
)
from infrastructure.postgres_session_repository import PostgresSessionRepository
from presentation.components.branding import load_brand_config
from presentation.components.chat import render_chat
from presentation.components.sidebar import render_sidebar
from presentation.components.styles import inject_styles
from presentation.i18n import UI_LANGUAGE_KEY, DEFAULT_UI_LANGUAGE

logger = logging.getLogger(__name__)

DEFAULT_PERSIST_DIR = "./chroma_db"


def run() -> None:
    brand = load_brand_config()

    if UI_LANGUAGE_KEY not in st.session_state:
        # Persisted choice (Settings > Interface language) takes priority
        # over the DEFAULT_UI_LANGUAGE env var, mirroring how company_name/
        # company_logo_path already override their own env var defaults —
        # same single, global, app-wide settings file, no per-session state.
        saved_language = load_app_settings().ui_language.strip()
        st.session_state[UI_LANGUAGE_KEY] = saved_language or os.getenv(
            "DEFAULT_UI_LANGUAGE", DEFAULT_UI_LANGUAGE
        ).strip() or DEFAULT_UI_LANGUAGE

    st.set_page_config(
        page_title=brand.company_name,
        page_icon=brand.logo_path or "🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_styles(brand.primary_color)

    chat_provider = os.getenv("LLM_PROVIDER", AZURE_PROVIDER).strip().lower()
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", AZURE_PROVIDER).strip().lower()
    providers = (chat_provider, embedding_provider)

    try:
        azure_settings = AzureSettings() if AZURE_PROVIDER in providers else None
        github_settings = (
            GitHubModelsSettings() if GITHUB_PROVIDER in providers else None
        )
        groq_settings = GroqSettings() if chat_provider == GROQ_PROVIDER else None
    except ValidationError as error:
        logger.error("Invalid settings: %s", error)
        st.error(_format_validation_error(error))
        return

    try:
        ingest_use_case, answer_use_case, repository = _build_dependencies(
            chat_provider,
            embedding_provider,
            azure_settings,
            github_settings,
            groq_settings,
        )
    except LLMServiceError as error:
        logger.error("Cannot build providers: %s", error)
        st.error(str(error))
        return

    session_repository = _build_session_repository()

    render_sidebar(ingest_use_case, repository, brand, session_repository)
    render_chat(answer_use_case, brand.company_name, session_repository)


@st.cache_resource(show_spinner=False)
def _build_dependencies(
    chat_provider: str,
    embedding_provider: str,
    _azure_settings: Optional[AzureSettings],
    _github_settings: Optional[GitHubModelsSettings],
    _groq_settings: Optional[GroqSettings] = None,
) -> tuple[IngestDocument, AnswerQuestion, ChromaDocumentRepository]:
    """Build and cache the LLM/embedding clients and use cases.

    Cached by ``(chat_provider, embedding_provider)`` only — the settings
    objects are excluded from the cache key (Streamlit convention: leading
    underscore). This means rotating an API key in ``.env`` without changing
    the provider name does **not** invalidate this cache; the old client
    keeps running until the process restarts. If that happens, calls will
    fail with ``LLMAuthError`` and the UI shows a message telling the user to
    restart the app — see ``render_chat``/``render_sidebar`` error handling.
    """
    embedder = build_embedder(embedding_provider, _azure_settings, _github_settings)
    language_model = build_language_model(
        chat_provider, _azure_settings, _github_settings, _groq_settings
    )
    repository = ChromaDocumentRepository(
        embedder=embedder,
        persist_directory=os.getenv("CHROMA_PERSIST_DIR", DEFAULT_PERSIST_DIR),
    )
    loader = LangChainDocumentLoader()
    ingest_use_case = IngestDocument(loader=loader, repository=repository)
    embedding_model_name = _embedding_model_name(embedder)
    answer_use_case = AnswerQuestion(
        repository=repository,
        language_model=language_model,
        guardrail=PatternGuardrail(),
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        embedding_model_name=embedding_model_name,
    )
    return ingest_use_case, answer_use_case, repository


def _embedding_model_name(embedder) -> str:
    """Best-effort embedding model name for the CB-009 debug panel."""
    embeddings = embedder.as_langchain_embeddings()
    return getattr(embeddings, "model", None) or getattr(embeddings, "model_name", "unknown")


@st.cache_resource(show_spinner=False)
def _build_session_repository() -> Optional[SessionRepository]:
    """Build the Postgres-backed session repository, or ``None`` if unavailable.

    Session persistence (CB-013) is an optional feature: if ``POSTGRES_*``
    variables are missing or the database is unreachable, the chat still
    works — it just doesn't offer save/load of past conversations. Failures
    are logged, not raised, so a missing/down Postgres never blocks the app.
    """
    try:
        settings = PostgresSettings()
    except ValidationError:
        logger.info("Postgres not configured — session persistence disabled.")
        return None
    try:
        return PostgresSessionRepository(settings.connection_string())
    except Exception:  # noqa: BLE001
        logger.exception("Could not connect to Postgres — session persistence disabled.")
        return None


def _format_validation_error(error: ValidationError) -> str:
    """Render a Pydantic ``ValidationError`` as one line per failing env var.

    Field names are uppercased to match the ``.env`` variable names rather
    than the internal Python attribute names.
    """
    lines = [
        f"{'.'.join(str(part) for part in item['loc']).upper()}: {item['msg']}"
        for item in error.errors()
    ]
    details = "\n".join(f"- {line}" for line in lines)
    return (
        f"Missing or invalid configuration:\n{details}\n\n"
        "Copy .env.example to .env, fill in the required variables and restart the app."
    )
