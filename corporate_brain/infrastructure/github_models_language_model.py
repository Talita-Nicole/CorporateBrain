"""GitHub Models implementation of the language model contract (OpenAI-compatible)."""

from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from domain.interfaces.language_model import LanguageModel
from infrastructure.config.github_models_settings import GitHubModelsSettings
from infrastructure.llm_errors import LLM_SDK_ERRORS, translate_llm_error

DEFAULT_TEMPERATURE = 0.0
_CREDENTIAL_HINT = "GITHUB_TOKEN (with models:read permission)"


class GitHubModelsLanguageModel(LanguageModel):
    """Wraps ``ChatOpenAI`` pointed at the GitHub Models OpenAI-compatible endpoint."""

    def __init__(
        self,
        settings: GitHubModelsSettings,
        temperature: float = DEFAULT_TEMPERATURE,
        max_tokens: Optional[int] = None,
    ) -> None:
        self._chat_model = ChatOpenAI(
            base_url=settings.github_models_endpoint,
            api_key=settings.github_token,
            model=settings.github_models_chat_model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def as_langchain_chat_model(self) -> BaseChatModel:
        return self._chat_model

    def invoke(self, prompt: str) -> str:
        try:
            response = self._chat_model.invoke(prompt)
        except LLM_SDK_ERRORS as error:
            raise translate_llm_error(
                error, provider="GitHub Models", credential_hint=_CREDENTIAL_HINT
            ) from error
        return str(response.content)
