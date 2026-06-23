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
from infrastructure.llm_errors import LLMServiceError  # noqa: E402

OK = "✅"
FAIL = "❌"
AZURE_PROVIDER = "azure"
GITHUB_PROVIDER = "github"
LLM_PROMPT = "Reply only: connection OK"
EMBEDDING_SAMPLE = "Short test sentence to generate embeddings."


def _build_chat_client(
    provider: str,
    azure_settings: AzureSettings | None,
    github_settings: GitHubModelsSettings | None,
) -> tuple[LanguageModel, str]:
    if provider == GITHUB_PROVIDER and github_settings is not None:
        return github_settings.get_llm_client(), "GitHub Models"
    if azure_settings is not None:
        return azure_settings.get_llm_client(), "Azure OpenAI"
    raise LLMServiceError("Chat model configuration is missing.")


def _build_embedder(
    provider: str,
    azure_settings: AzureSettings | None,
    github_settings: GitHubModelsSettings | None,
) -> tuple[Embedder, str]:
    if provider == GITHUB_PROVIDER and github_settings is not None:
        return github_settings.get_embedding_client(), "GitHub Models"
    if azure_settings is not None:
        return azure_settings.get_embedding_client(), "Azure OpenAI"
    raise LLMServiceError("Embeddings configuration is missing.")


def _test_chat(client: LanguageModel, provider_name: str) -> bool:
    start = time.perf_counter()
    try:
        answer = client.invoke(LLM_PROMPT)
    except LLMServiceError as error:
        print(f"{FAIL} Chat ({provider_name}): {error}")
        return False
    elapsed = time.perf_counter() - start
    print(f"{OK} Chat responding via {provider_name} ({elapsed:.2f}s): {answer.strip()}")
    return True


def _test_embeddings(client: Embedder, provider_name: str) -> bool:
    start = time.perf_counter()
    try:
        vector = client.embed_query(EMBEDDING_SAMPLE)
    except LLMServiceError as error:
        print(f"{FAIL} Embeddings ({provider_name}): {error}")
        return False
    elapsed = time.perf_counter() - start
    print(
        f"{OK} Embeddings via {provider_name} ({elapsed:.2f}s): "
        f"vector of {len(vector)} dimensions"
    )
    return True


def _load_settings(
    providers: tuple[str, str],
) -> tuple[AzureSettings | None, GitHubModelsSettings | None] | None:
    try:
        azure_settings = AzureSettings() if AZURE_PROVIDER in providers else None
        github_settings = (
            GitHubModelsSettings() if GITHUB_PROVIDER in providers else None
        )
    except ValidationError as error:
        print(f"{FAIL} Missing or invalid configuration")
        for item in error.errors():
            field = ".".join(str(part) for part in item["loc"])
            print(f"   - {field}: {item['msg']}")
        return None
    print(f"{OK} Configuration loaded")
    return azure_settings, github_settings


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
    azure_settings, github_settings = loaded

    try:
        chat_client, chat_name = _build_chat_client(
            chat_provider, azure_settings, github_settings
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
