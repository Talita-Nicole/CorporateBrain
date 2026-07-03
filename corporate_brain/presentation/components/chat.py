"""Chat area: conversation transcript, input box and per-answer sources."""

import logging

import streamlit as st

from application.use_cases.answer_question import (
    ENGLISH_LANGUAGE_LABEL,
    PORTUGUESE_LANGUAGE_LABEL,
    AnswerQuestion,
    RetrievalDebug,
    Source,
)
from domain.entities.message import Message, MessageSource
from domain.interfaces.session_repository import SessionRepository
from infrastructure.llm_errors import LLMCallError
from presentation.components.sessions import (
    CURRENT_SESSION_ID_KEY,
    CURRENT_SESSION_NAME_KEY,
    autosave_conversation,
)
from presentation.debug_mode import is_debug_mode_enabled
from presentation.i18n import ENGLISH, UI_LANGUAGE_KEY, t
from presentation.llm_error_messages import format_llm_call_error

logger = logging.getLogger(__name__)

HISTORY_KEY = "chat_history"
SELECTED_SOURCES_KEY = "selected_sources"
SUGGESTIONS_KEY = "follow_up_suggestions"
PENDING_QUESTION_KEY = "pending_question"
GENERATING_KEY = "generating_question"
STARTERS_DONE_KEY = "starters_generated"


def render_chat(
    answer_use_case: AnswerQuestion,
    company_name: str,
    session_repository: SessionRepository | None = None,
) -> None:
    _initialize_history()
    _render_header(company_name)
    _render_transcript()

    # Fixed-position slots, recreated every run right after the transcript. A
    # fresh ``st.empty()`` overwrites whatever filled the slot in the previous
    # frame, so the suggestion chips are cleared *before* the blocking
    # generation spinner runs — they can never linger or stay clickable while
    # the model is thinking. ``turn_slot`` holds the in-flight Q&A (above),
    # ``suggestions_slot`` holds the chips (below).
    turn_slot = st.empty()
    suggestions_slot = st.empty()

    _accept_new_question()
    _process_generation(answer_use_case, turn_slot, session_repository)
    _ensure_starters(answer_use_case)
    _render_suggestions(suggestions_slot)


def _initialize_history() -> None:
    if HISTORY_KEY not in st.session_state:
        st.session_state[HISTORY_KEY] = []


def _render_header(company_name: str) -> None:
    # Keyed so styles.py can pin this block to the top of the scrolling main
    # column via CSS (position: sticky) — "Clear Chat" stays reachable
    # without scrolling back up through a long conversation.
    with st.container(key="cb_chat_header"):
        col_title, col_btn = st.columns([6, 1])
        with col_title:
            st.markdown(
                f'<div class="cb-page-title">{t("chat.title", company_name=company_name)}</div>'
                f'<div class="cb-page-subtitle">{t("chat.subtitle")}</div>',
                unsafe_allow_html=True,
            )
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(
                t("chat.clear_button"),
                use_container_width=True,
                help=t("chat.clear_help"),
            ):
                st.session_state[HISTORY_KEY] = []
                st.session_state.pop(SUGGESTIONS_KEY, None)
                st.session_state.pop(GENERATING_KEY, None)
                # Allow starter suggestions to be regenerated for the fresh session.
                st.session_state.pop(STARTERS_DONE_KEY, None)
                # Detach from any saved conversation so a later save creates a new
                # one instead of silently overwriting the one just cleared.
                st.session_state.pop(CURRENT_SESSION_ID_KEY, None)
                st.session_state.pop(CURRENT_SESSION_NAME_KEY, None)
                st.rerun()


def _render_transcript() -> None:
    for message in st.session_state[HISTORY_KEY]:
        with st.chat_message(message.role):
            st.markdown(message.content)
            if message.sources:
                _render_sources(message.sources)


def _accept_new_question() -> None:
    """Read a typed question or a queued suggestion and schedule generation.

    ``st.chat_input`` is rendered on every run or the input box vanishes. A new
    question is not answered here: it is queued in ``GENERATING_KEY`` (dropping
    the stale chips) and the run reruns, so generation happens in a later run
    whose ``suggestions_slot`` starts empty.
    """
    typed_question = st.chat_input(t("chat.input_placeholder"))
    question = st.session_state.pop(PENDING_QUESTION_KEY, None) or typed_question
    if not question:
        return

    st.session_state.pop(SUGGESTIONS_KEY, None)
    st.session_state[GENERATING_KEY] = question
    st.rerun()


def _process_generation(
    answer_use_case: AnswerQuestion,
    slot,
    session_repository: SessionRepository | None = None,
) -> None:
    """Answer the question queued by ``_accept_new_question`` (if any)."""
    question = st.session_state.get(GENERATING_KEY)
    if not question:
        return

    history = list(st.session_state[HISTORY_KEY])
    selected_sources = sorted(st.session_state.get(SELECTED_SOURCES_KEY, set()))

    with slot.container():
        with st.chat_message("user"):
            st.markdown(question)
        with st.chat_message("assistant"):
            try:
                streaming = answer_use_case.execute_streaming(
                    question=question,
                    history=history,
                    selected_sources=selected_sources,
                    # Token usage is always computed — it's rendered as a
                    # plain, discreet line under every answer (Claude.ai
                    # style), not gated behind a user-facing toggle. No extra
                    # LLM/embedding call: the data is already produced by the
                    # same retrieval and the same streamed response.
                    debug=True,
                )
                if streaming.result is not None and streaming.result.refused:
                    # Guardrail refusals are resolved without calling the LLM
                    # (``.result`` is already populated) — render as a warning
                    # instead of streaming plain markdown text.
                    st.warning(streaming.result.answer, icon="🚫")
                else:
                    st.write_stream(streaming.tokens())
            except LLMCallError as error:
                logger.exception("Failed to answer question")
                st.error(format_llm_call_error(error))
                st.session_state.pop(GENERATING_KEY, None)
                return
            except Exception as error:  # noqa: BLE001
                logger.exception("Failed to answer question")
                st.error(t("chat.answer_failed", error=error))
                st.session_state.pop(GENERATING_KEY, None)
                return

            result = streaming.result
            if result is None:
                # The stream raised before yielding anything and was already
                # reported above; nothing further to render for this turn.
                st.session_state.pop(GENERATING_KEY, None)
                return

            if not result.refused:
                _render_sources(result.sources)
                _render_token_usage(result.retrieval_debug)
                if is_debug_mode_enabled():
                    _render_debug_panel(result.retrieval_debug)

    message_sources = [
        MessageSource(
            citation_number=source.citation_number,
            document_name=source.document_name,
            snippet=source.snippet,
        )
        for source in result.sources
    ]
    st.session_state[HISTORY_KEY].append(Message(role="user", content=question))
    st.session_state[HISTORY_KEY].append(
        Message(role="assistant", content=result.answer, sources=message_sources)
    )
    st.session_state[SUGGESTIONS_KEY] = result.suggested_questions
    st.session_state.pop(GENERATING_KEY, None)

    # Autosave: upsert the conversation now that it has at least one
    # completed turn. Uses the same session id across turns (seeded into
    # session_state on the first save), so this always updates the same row.
    autosave_conversation(session_repository, st.session_state[HISTORY_KEY])

    # render_sidebar runs before render_chat within the same script
    # execution (see app.py), so the sidebar's source-selection lock — which
    # reads GENERATING_KEY — rendered from the *stale* pre-turn value on this
    # very run. Popping the key above doesn't retroactively un-disable those
    # already-rendered checkboxes; only a fresh run, with GENERATING_KEY
    # gone, renders them enabled again.
    st.rerun()


def _ensure_starters(answer_use_case: AnswerQuestion) -> None:
    """On a fresh session, seed suggestion chips from the indexed documents.

    Runs once (guarded by ``STARTERS_DONE_KEY``) only when there is no history,
    no pending suggestions and no answer in flight, so the user gets a sense of
    what to ask before typing anything.
    """
    if st.session_state.get(GENERATING_KEY):
        return
    if st.session_state[HISTORY_KEY] or st.session_state.get(SUGGESTIONS_KEY):
        return
    if st.session_state.get(STARTERS_DONE_KEY):
        return

    st.session_state[STARTERS_DONE_KEY] = True
    selected_sources = sorted(st.session_state.get(SELECTED_SOURCES_KEY, set()))
    ui_language = st.session_state.get(UI_LANGUAGE_KEY, ENGLISH)
    starter_language = (
        ENGLISH_LANGUAGE_LABEL if ui_language == ENGLISH else PORTUGUESE_LANGUAGE_LABEL
    )
    try:
        with st.spinner(t("chat.preparing_suggestions")):
            starters = answer_use_case.suggest_starters(
                selected_sources=selected_sources,
                ui_language=starter_language,
            )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to generate starter suggestions")
        starters = []

    if starters:
        st.session_state[SUGGESTIONS_KEY] = starters


def _render_sources(sources: list[Source] | list[MessageSource]) -> None:
    """Render the sources expander.

    Accepts either ``Source`` (fresh from ``AnswerQuestion.execute``) or
    ``MessageSource`` (reloaded from a saved conversation) — both carry the
    same three fields, so a live answer and a reloaded one render identically.
    """
    if not sources:
        return
    with st.expander(t("chat.sources_expander", count=len(sources))):
        for source in sources:
            st.markdown(f"**[{source.citation_number}] {source.document_name}**")
            st.caption(source.snippet)
            st.divider()


def _render_token_usage(debug: RetrievalDebug | None) -> None:
    """Plain, discreet token count under the answer — always shown, no toggle.

    Matches the lightweight style of Claude.ai's token indicator: a single
    small caption line, not a dropdown. Detailed retrieval internals
    (chunks, distances, top-k) are intentionally excluded from this default
    view — see ``_render_debug_panel`` for those, gated behind
    ``DEBUG_MODE``.
    """
    if debug is None or debug.total_tokens is None:
        return
    st.caption(
        t(
            "chat.token_usage",
            input=debug.input_tokens,
            output=debug.output_tokens,
            total=debug.total_tokens,
        )
    )


def _render_debug_panel(debug: RetrievalDebug | None) -> None:
    """Full retrieval/pipeline debug panel — only rendered when ``DEBUG_MODE=true``.

    Not linked from any user-facing setting; this is a developer-only view.
    """
    if debug is None:
        return
    with st.expander(t("chat.debug_expander")):
        st.markdown(
            t(
                "chat.debug_config",
                top_k=debug.top_k,
                max_distance=debug.max_relevant_distance,
                chunk_size=debug.chunk_size,
                chunk_overlap=debug.chunk_overlap,
            )
        )
        st.markdown(
            t("chat.debug_models", embedding_model=debug.embedding_model, chat_model=debug.chat_model)
        )
        st.divider()
        for chunk in debug.retrieved_chunks:
            icon = "✅" if chunk.passed_threshold else "❌"
            st.markdown(f"{icon} **{chunk.document_name}** — distance: {chunk.distance:.3f}")
            st.caption(chunk.snippet)


def _render_suggestions(slot) -> None:
    """Render suggestion chips (starters or follow-ups) into the fixed slot.

    Rendered from session_state so ``st.button`` clicks are captured on the
    rerun that follows the click. A click queues the question and reruns; the
    input handler then consumes it as if typed.
    """
    suggestions = st.session_state.get(SUGGESTIONS_KEY) or []
    if not suggestions:
        return

    with slot.container():
        st.markdown(
            f'<div class="cb-section-label">{t("chat.suggested_questions")}</div>',
            unsafe_allow_html=True,
        )
        for index, question in enumerate(suggestions):
            if st.button(
                question, key=f"suggestion_{index}", use_container_width=True
            ):
                st.session_state[PENDING_QUESTION_KEY] = question
                st.session_state.pop(SUGGESTIONS_KEY, None)
                st.rerun()
