"""Chat area: conversation transcript, input box and per-answer sources."""

import logging

import streamlit as st

from application.use_cases.answer_question import AnswerQuestion, Source
from domain.entities.message import Message

logger = logging.getLogger(__name__)

HISTORY_KEY = "chat_history"


def render_chat(answer_use_case: AnswerQuestion) -> None:
    """Render the chat transcript, the clear button and handle new input."""
    _initialize_history()
    _render_clear_button()
    _render_transcript()
    _handle_user_input(answer_use_case)


def _initialize_history() -> None:
    if HISTORY_KEY not in st.session_state:
        st.session_state[HISTORY_KEY] = []


def _render_clear_button() -> None:
    if st.button("Clear conversation"):
        st.session_state[HISTORY_KEY] = []
        st.rerun()


def _render_transcript() -> None:
    for message in st.session_state[HISTORY_KEY]:
        with st.chat_message(message.role):
            st.markdown(message.content)


def _handle_user_input(answer_use_case: AnswerQuestion) -> None:
    question = st.chat_input("Ask a question about your documents")
    if not question:
        return

    history = list(st.session_state[HISTORY_KEY])
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = answer_use_case.execute(question=question, history=history)
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
    with st.expander("Sources"):
        for source in sources:
            st.markdown(f"**{source.document_name}**")
            st.caption(source.snippet)
