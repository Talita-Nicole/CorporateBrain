"""Groq implementation of the language model contract (OpenAI-compatible)."""

from typing import Iterator, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessageChunk
from langchain_openai import ChatOpenAI

from domain.interfaces.language_model import LanguageModel
from infrastructure.config.groq_settings import GroqSettings
from infrastructure.llm_errors import with_llm_error_translation

DEFAULT_TEMPERATURE = 0.0
_CREDENTIAL_HINT = "GROQ_API_KEY"


class GroqLanguageModel(LanguageModel):
    """Wraps ``ChatOpenAI`` pointed at the Groq OpenAI-compatible endpoint."""

    def __init__(
        self,
        settings: GroqSettings,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
    ) -> None:
        self._chat_model = ChatOpenAI(
            base_url=settings.groq_endpoint,
            api_key=settings.groq_api_key,
            model=settings.groq_chat_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def as_langchain_chat_model(self) -> BaseChatModel:
        return self._chat_model

    def invoke(self, prompt: str) -> str:
        with with_llm_error_translation("Groq", _CREDENTIAL_HINT):
            response = self._chat_model.invoke(prompt)
        return str(response.content)

    def stream(self, messages: list) -> Iterator[AIMessageChunk]:
        with with_llm_error_translation("Groq", _CREDENTIAL_HINT):
            yield from self._chat_model.bind(stream_usage=True).stream(messages)
