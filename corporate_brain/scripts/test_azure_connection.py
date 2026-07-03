"""Standalone LLM/embeddings connectivity check.

Run from the project root:

    python scripts/test_azure_connection.py

Chat uses the provider in LLM_PROVIDER; embeddings use EMBEDDING_PROVIDER
("azure" or "github" for each). Prints a checklist with per-call timings.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from domain.interfaces.embedder import Embedder  # noqa: E402
from domain.interfaces.language_model import LanguageModel  # noqa: E402
from infrastructure.config.azure_settings import AzureSettings  # noqa: E402
from infrastructure.config.github_models_settings import (  # noqa: E402
    GitHubModelsSettings,
)
from infrastructure.config.groq_settings import GroqSettings  # noqa: E402
from infrastructure.config.providers import (  # noqa: E402
    AZURE_PROVIDER,
    GITHUB_PROVIDER,
    GROQ_PROVIDER,
    build_embedder,
    build_language_model,
)
from infrastructure.llm_errors import LLMCallError, LLMServiceError  # noqa: E402
from presentation.llm_error_messages import format_llm_call_error  # noqa: E402

OK = "✅"
FAIL = "❌"
LLM_PROMPT = "Reply only: connection OK"
EMBEDDING_SAMPLE = "Short test sentence to generate embeddings."


def _provider_display_name(provider: str) -> str:
    if provider == GITHUB_PROVIDER:
        return "GitHub Models"
    if provider == GROQ_PROVIDER:
        return "Groq"
    return "Azure OpenAI"


def _build_chat_client(
    provider: str,
    azure_settings: AzureSettings | None,
    github_settings: GitHubModelsSettings | None,
    groq_settings: GroqSettings | None,
) -> tuple[LanguageModel, str]:
    client = build_language_model(provider, azure_settings, github_settings, groq_settings)
    return client, _provider_display_name(provider)


def _build_embedder(
    provider: str,
    azure_settings: AzureSettings | None,
    github_settings: GitHubModelsSettings | None,
) -> tuple[Embedder, str]:
    client = build_embedder(provider, azure_settings, github_settings)
    return client, _provider_display_name(provider)


def _test_chat(client: LanguageModel, provider_name: str) -> bool:
    start = time.perf_counter()
    try:
        answer = client.invoke(LLM_PROMPT)
    except LLMCallError as error:
        print(f"{FAIL} Chat ({provider_name}): {format_llm_call_error(error)}")
        return False
    elapsed = time.perf_counter() - start
    print(f"{OK} Chat responding via {provider_name} ({elapsed:.2f}s): {answer.strip()}")
    return True


def _test_embeddings(client: Embedder, provider_name: str) -> bool:
    start = time.perf_counter()
    try:
        vector = client.embed_query(EMBEDDING_SAMPLE)
    except LLMCallError as error:
        print(f"{FAIL} Embeddings ({provider_name}): {format_llm_call_error(error)}")
        return False
    elapsed = time.perf_counter() - start
    print(
        f"{OK} Embeddings via {provider_name} ({elapsed:.2f}s): "
        f"vector of {len(vector)} dimensions"
    )
    return True


def _load_settings(
    providers: tuple[str, str],
) -> tuple[AzureSettings | None, GitHubModelsSettings | None, GroqSettings | None] | None:
    try:
        azure_settings = AzureSettings() if AZURE_PROVIDER in providers else None
        github_settings = (
            GitHubModelsSettings() if GITHUB_PROVIDER in providers else None
        )
        groq_settings = GroqSettings() if GROQ_PROVIDER in providers else None
    except ValidationError as error:
        print(f"{FAIL} Missing or invalid configuration")
        for item in error.errors():
            field = ".".join(str(part) for part in item["loc"])
            print(f"   - {field}: {item['msg']}")
        return None
    print(f"{OK} Configuration loaded")
    return azure_settings, github_settings, groq_settings


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    load_dotenv()
    chat_provider = os.getenv("LLM_PROVIDER", AZURE_PROVIDER).strip().lower()
    embedding_provider = os.getenv("EMBEDDING_PROVIDER", AZURE_PROVIDER).strip().lower()
    print("=== LLM / Embeddings Connection Test ===")
    print(f"Chat provider .......... {chat_provider}")
    print(f"Embeddings provider .... {embedding_provider}")

    loaded = _load_settings((chat_provider, embedding_provider))
    if loaded is None:
        return 1
    azure_settings, github_settings, groq_settings = loaded

    try:
        chat_client, chat_name = _build_chat_client(
            chat_provider, azure_settings, github_settings, groq_settings
        )
        embedder, embedder_name = _build_embedder(
            embedding_provider, azure_settings, github_settings
        )
    except LLMServiceError as error:
        print(f"{FAIL} {error}")
        return 1

    chat_ok = _test_chat(chat_client, chat_name)
    embeddings_ok = _test_embeddings(embedder, embedder_name)
    if chat_ok and embeddings_ok:
        print(f"\n{OK} All good! The integration is working.")
        return 0
    print(f"\n{FAIL} Integration has failures. Review the messages above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
