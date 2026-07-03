"""Azure OpenAI implementation of the language model contract."""

from typing import Iterator, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessageChunk
from langchain_openai import AzureChatOpenAI

from domain.interfaces.language_model import LanguageModel
from infrastructure.config.azure_settings import AzureSettings
from infrastructure.llm_errors import with_llm_error_translation

DEFAULT_TEMPERATURE = 0.0
_CREDENTIAL_HINT = "AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT"


class AzureLanguageModel(LanguageModel):
    """Wraps ``AzureChatOpenAI`` behind the ``LanguageModel`` contract."""

    def __init__(
        self,
        settings: AzureSettings,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
    ) -> None:
        self._chat_model = AzureChatOpenAI(
            api_key=settings.azure_openai_api_key,
            azure_endpoint=settings.azure_openai_endpoint,
            azure_deployment=settings.azure_openai_deployment_name,
            api_version=settings.azure_openai_api_version,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def as_langchain_chat_model(self) -> BaseChatModel:
        return self._chat_model

    def invoke(self, prompt: str) -> str:
        with with_llm_error_translation("Azure OpenAI", _CREDENTIAL_HINT):
            response = self._chat_model.invoke(prompt)
        return str(response.content)

    def stream(self, messages: list) -> Iterator[AIMessageChunk]:
        # stream_usage=True is required for the merged chunk to carry
        # usage_metadata (token counts) once the stream completes.
        with with_llm_error_translation("Azure OpenAI", _CREDENTIAL_HINT):
            yield from self._chat_model.bind(stream_usage=True).stream(messages)
