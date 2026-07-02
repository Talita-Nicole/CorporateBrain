"""Chat area: conversation transcript, input box and per-answer sources."""

import logging

import streamlit as st

from application.use_cases.answer_question import AnswerQuestion, Source
from domain.entities.message import Message

logger = logging.getLogger(__name__)

HISTORY_KEY = "chat_history"
SELECTED_SOURCES_KEY = "selected_sources"


def render_chat(answer_use_case: AnswerQuestion, company_name: str) -> None:
    _initialize_history()
    _render_header(company_name)
    _render_transcript()
    _handle_user_input(answer_use_case)


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
            st.rerun()


def _render_transcript() -> None:
    for message in st.session_state[HISTORY_KEY]:
        with st.chat_message(message.role):
            st.markdown(message.content)


def _handle_user_input(answer_use_case: AnswerQuestion) -> None:
    question = st.chat_input("Ask a question about your documents…")
    if not question:
        return

    history = list(st.session_state[HISTORY_KEY])
    selected_sources = sorted(st.session_state.get(SELECTED_SOURCES_KEY, set()))
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
                return
        st.markdown(result.answer)
        _render_sources(result.sources)

    st.session_state[HISTORY_KEY].append(Message(role="user", content=question))
    st.session_state[HISTORY_KEY].append(
        Message(role="assistant", content=result.answer)
    )


def _render_sources(sources: list[Source]) -> None:
    if not sources:
        return
    with st.expander(f"📎 {len(sources)} source(s)"):
        for source in sources:
            st.markdown(f"**[{source.citation_number}] {source.document_name}**")
            st.caption(source.snippet)
            st.divider()
