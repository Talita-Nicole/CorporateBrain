"""Chat area: conversation transcript, input box and per-answer sources."""

import logging

import streamlit as st

from application.use_cases.answer_question import AnswerQuestion, Source
from domain.entities.message import Message

logger = logging.getLogger(__name__)

HISTORY_KEY = "chat_history"
SELECTED_SOURCES_KEY = "selected_sources"
SUGGESTIONS_KEY = "follow_up_suggestions"
PENDING_QUESTION_KEY = "pending_question"
GENERATING_KEY = "generating_question"
STARTERS_DONE_KEY = "starters_generated"


def render_chat(answer_use_case: AnswerQuestion, company_name: str) -> None:
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
    _process_generation(answer_use_case, turn_slot)
    _ensure_starters(answer_use_case)
    _render_suggestions(suggestions_slot)


def _initialize_history() -> None:
    if HISTORY_KEY not in st.session_state:
        st.session_state[HISTORY_KEY] = []


def _render_header(company_name: str) -> None:
    col_title, col_btn = st.columns([6, 1])
    with col_title:
        st.markdown(
            f'<div class="cb-page-title">Ask {company_name}</div>'
            '<div class="cb-page-subtitle">Ask questions about your indexed documents.</div>',
            unsafe_allow_html=True,
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Clear", use_container_width=True):
            st.session_state[HISTORY_KEY] = []
            st.session_state.pop(SUGGESTIONS_KEY, None)
            st.session_state.pop(GENERATING_KEY, None)
            # Allow starter suggestions to be regenerated for the fresh session.
            st.session_state.pop(STARTERS_DONE_KEY, None)
            st.rerun()


def _render_transcript() -> None:
    for message in st.session_state[HISTORY_KEY]:
        with st.chat_message(message.role):
            st.markdown(message.content)


def _accept_new_question() -> None:
    """Read a typed question or a queued suggestion and schedule generation.

    ``st.chat_input`` is rendered on every run or the input box vanishes. A new
    question is not answered here: it is queued in ``GENERATING_KEY`` (dropping
    the stale chips) and the run reruns, so generation happens in a later run
    whose ``suggestions_slot`` starts empty.
    """
    typed_question = st.chat_input("Ask a question about your documents…")
    question = st.session_state.pop(PENDING_QUESTION_KEY, None) or typed_question
    if not question:
        return

    st.session_state.pop(SUGGESTIONS_KEY, None)
    st.session_state[GENERATING_KEY] = question
    st.rerun()


def _process_generation(answer_use_case: AnswerQuestion, slot) -> None:
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
            with st.spinner("Thinking…"):
                try:
                    result = answer_use_case.execute(
                        question=question,
                        history=history,
                        selected_sources=selected_sources,
                    )
                except Exception as error:  # noqa: BLE001
                    logger.exception("Failed to answer question")
                    st.error(f"Failed to generate an answer: {error}")
                    st.session_state.pop(GENERATING_KEY, None)
                    return
            st.markdown(result.answer)
            _render_sources(result.sources)

    st.session_state[HISTORY_KEY].append(Message(role="user", content=question))
    st.session_state[HISTORY_KEY].append(
        Message(role="assistant", content=result.answer)
    )
    st.session_state[SUGGESTIONS_KEY] = result.suggested_questions
    st.session_state.pop(GENERATING_KEY, None)


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
    try:
        with st.spinner("Preparing suggestions…"):
            starters = answer_use_case.suggest_starters(
                selected_sources=selected_sources
            )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to generate starter suggestions")
        starters = []

    if starters:
        st.session_state[SUGGESTIONS_KEY] = starters


def _render_sources(sources: list[Source]) -> None:
    if not sources:
        return
    with st.expander(f"📎 {len(sources)} source(s)"):
        for source in sources:
            st.markdown(f"**[{source.citation_number}] {source.document_name}**")
            st.caption(source.snippet)
            st.divider()


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
            '<div class="cb-section-label">Suggested questions</div>',
            unsafe_allow_html=True,
        )
        for index, question in enumerate(suggestions):
            if st.button(
                question, key=f"suggestion_{index}", use_container_width=True
            ):
                st.session_state[PENDING_QUESTION_KEY] = question
                st.session_state.pop(SUGGESTIONS_KEY, None)
                st.rerun()
