# Central de Conhecimento

A Retrieval-Augmented Generation (RAG) system that lets employees ask natural-language
questions about internal company documents and get contextual, source-cited answers.

Documents (PDF, DOCX, TXT, CSV) are uploaded, chunked and indexed into a local ChromaDB
vector store. Questions are answered by Azure OpenAI (`gpt-4o`) grounded strictly in the
retrieved context. The assistant replies in the same language as the question (pt-BR or
English) and shows the document name and excerpt that supported each answer.

## Stack

- **Python 3.11+**
- **LangChain** — the entire RAG pipeline (loaders, splitter, embeddings, vector store, chain, memory)
- **Azure OpenAI** — `gpt-4o` for generation and an embeddings deployment
- **ChromaDB** — local, persistent vector store
- **Streamlit** — chat interface

## Architecture

Clean Architecture with dependencies pointing inward. Use cases depend on interfaces
(ports), never on concrete implementations; the Streamlit layer wires everything together
and holds only UI state.

```
domain/          entities + interface contracts
application/     use cases (ingest document, answer question)
infrastructure/  adapters: LangChain loaders, Chroma repository, Azure OpenAI
presentation/    Streamlit UI + dependency composition
```

## Requirements

- Python 3.11 or 3.12 (recommended). Python 3.14 is not yet supported: the pinned
  LangChain 0.3.x stack relies on pydantic models that fail to build under 3.14.
- An Azure OpenAI resource with two deployments: a chat model (`gpt-4o`) and an embeddings model

## Installation

```bash
python -m venv .venv
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
```

## Configuration

Copy the example file and fill in your Azure OpenAI settings:

```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `LLM_PROVIDER` | Chat provider: `azure` (default) or `github` |
| `EMBEDDING_PROVIDER` | Embeddings provider: `azure` (default) or `github` |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI resource key |
| `AZURE_OPENAI_ENDPOINT` | Resource endpoint, e.g. `https://my-resource.openai.azure.com/` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Chat deployment name — required only when `LLM_PROVIDER=azure` |
| `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Embeddings deployment name (always required) |
| `AZURE_OPENAI_API_VERSION` | API version (default `2024-02-01`) |
| `GITHUB_TOKEN` | GitHub token with `models:read` — required only when `LLM_PROVIDER=github` |
| `GITHUB_MODELS_ENDPOINT` | GitHub Models endpoint (default `https://models.github.ai/inference`) |
| `GITHUB_MODELS_CHAT_MODEL` | Chat model id (default `openai/gpt-4o-mini`) |
| `GITHUB_MODELS_EMBEDDING_MODEL` | Embedding model id (default `openai/text-embedding-3-small`) |
| `CHROMA_PERSIST_DIR` | Local Chroma directory (default `./chroma_db`) |

`.env` must never be committed.

### Providers — Azure or GitHub Models

Chat and embeddings each have a selectable provider, so the app can run even when an
Azure subscription has no quota to deploy or call a model:

- Chat: `LLM_PROVIDER=azure` (`AzureChatOpenAI`, needs `AZURE_OPENAI_DEPLOYMENT_NAME`) or
  `LLM_PROVIDER=github` (GitHub Models, needs `GITHUB_TOKEN`).
- Embeddings: `EMBEDDING_PROVIDER=azure` (`AzureOpenAIEmbeddings`) or
  `EMBEDDING_PROVIDER=github` (GitHub Models, separate rate limit from Azure).

[GitHub Models](https://github.com/marketplace/models) is OpenAI-compatible, free and
needs no Azure quota — useful for student/free subscriptions that are rate-limited on
Azure. When a provider is set to `github`, the corresponding Azure variables are not
required.

Validate the configured providers before running the app:

```bash
python scripts/test_azure_connection.py
```

## Running

```bash
streamlit run main.py
```

The app opens at `http://localhost:8501`:

- **Sidebar** — upload documents (PDF, DOCX, TXT, CSV) and see the list of indexed files.
- **Chat** — ask questions; each answer shows its supporting sources and there is a button
  to clear the conversation.

Indexed documents persist in `./chroma_db`, so they remain available after a restart.

## How it works

| Step | LangChain component |
|---|---|
| Read documents | `PyPDFLoader`, `Docx2txtLoader`, `TextLoader`, `CSVLoader` |
| Chunking | `RecursiveCharacterTextSplitter` (`chunk_size=1000`, `chunk_overlap=200`) |
| Embeddings | `AzureOpenAIEmbeddings` or `OpenAIEmbeddings` (GitHub Models), per `EMBEDDING_PROVIDER` |
| Vector store | `Chroma` (collection `corporate_knowledge`) |
| QA chain | `ConversationalRetrievalChain` |
| Memory | `ConversationBufferMemory` (`return_messages=True`) |
| LLM | `AzureChatOpenAI` or `ChatOpenAI` (GitHub Models), per `LLM_PROVIDER` |

Each chunk stores `source` (file name), `page` (when available) and `chunk_index` in its
metadata, which is what powers the source citations.
