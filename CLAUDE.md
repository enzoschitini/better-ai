# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

BetterAI is a platform unifying multiple AI models/agents behind one backend. It ships as **two separate front doors over the same `src/` codebase**:

- `web_services.py` — a FastAPI REST/streaming API (deployed as the main service, see `Procfile`).
- `web_app.py` — a Streamlit multi-page app (internal/demo UI over the same agents and services).

Both are thin entrypoints; almost all logic lives under `src/`.

## Commands

Dependency management is via `uv` (see `pyproject.toml` / `uv.lock`; `requirements.txt` also exists but `uv` is authoritative). Python `3.12` (see `.python-version`).

```bash
# install deps
uv sync

# run the FastAPI service (matches Procfile, but locally use web_services:app)
uvicorn web_services:app --reload

# run the Streamlit app
streamlit run web_app.py

# run a single agent module standalone (each agent package has a `run.py`/`__main__`-style entry)
python -m src.agents._base_agent.agent

# tests: no single pytest suite/conftest — tests are ad-hoc scripts colocated with the code
# (e.g. src/agents/agent_executor/test.py, src/chat/test/TestAgent.py). Run them individually:
python -m src.agents.agent_executor.test
```

There is no lint/format config in the repo — don't assume ruff/black/flake8 conventions beyond what's already in the file you're editing.

## Architecture

### Two front doors, one backend

- **`src/web_services_network/`** — FastAPI app.
  - `api.py` (`WebServiceAPI`) builds the app, wires CORS, health routes, and **auto-discovers routers**: `collect_routers("src.web_services_network.routes")` walks every module in `routes/` and picks up any module-level `router` variable. To add an endpoint group, drop a new file in `src/web_services_network/routes/` with an `APIRouter` named `router` — no manual registration needed.
  - `routes/*.py` — one file per feature area (`agents.py`, `davinci.py`, `deep_research.py`, `parse_content.py`, `vector_store.py`).
  - `utils/auth.py` (`Authorization.validate_api_key`) — API-key check via `X-API-Key` header against `BETTERAI_API_KEY`; **bypassed entirely when `LOCAL=true`**. Used as a FastAPI `Depends` on protected routes.
- **`src/web_applications/`** — Streamlit app.
  - `utils/pages.py` defines `APPS` (slug → label/description/path) and builds `st.Page` objects consumed by `web_app.py`'s `st.navigation`. Add a page by adding an entry here plus a module under `applications/`.
  - `applications/*.py` are the top-level pages; `pages/<feature>/` holds supporting sub-pages/config for a given app (e.g. `pages/acquarello/`, `pages/content_generator/`).

### Agents (`src/agents/`, plus feature-specific agent folders like `content_agent`, `datafram_agent`, `deep_research`, `trend_radar`, `knowlegbase_agent`)

Built on **Agno** (`agno.agent.Agent`), not raw LangChain, even though LangChain packages are also dependencies (used for document/text processing utilities, not the agent runtime itself).

- Each agent package follows the same shape: `agent.py` (class with `create_agent(metadata, tool_context)` building an `Agent`), `config.py` (prompt/model constants), `run.py` (standalone runner), `tools/toolkit.py` (an Agno `Toolkit` subclass exposing the agent's tools).
- `src/agents/utils/model_gateway.py` (`ModelGateway`) — the unified model factory. All new agent code should create models through this instead of importing provider SDKs directly; it normalizes provider aliases (`anthropic`/`claude`, `google`/`gemini`, etc.), validates kwargs against the target class's real constructor signature via `inspect`, and supports OpenAI's chat/responses/open_responses/like variants.
- `src/agents/utils/database.py` (`Database`) — factory returning either `SqliteDb` (local, `local=True`) or `PostgresDb` (Supabase). Both branches wire up the *same* long list of Agno table names (sessions, memories, metrics, knowledge, traces, schedules, etc.) — if you add a new Agno table, update both `_local_database` and `_supabase`.
- `src/agents/agent_executor/` — generic execution harness decoupled from any single agent:
  - `unified_executor.py` (`AgentExecutor`) — one class, four run modes: `run_json` (single response), `run_stream`/`run_stream_print` (incremental), `run_agent_os` (Agno's `AgentOS` server), `run_print_response`/`run_cli_loop` (interactive CLI). `AgentExecutor.from_agent_class(agent_class, params, session_id, user_id)` is the standard way to instantiate: it registers the class in a `LocalAgentFactory`, builds the agent + a fresh `ToolContext`/tool collector, and returns a ready `AgentExecutor`.
  - `tool_context.py` — per-run tool-call metadata collector, threaded through the toolkit so tool outputs can be surfaced alongside streamed text (see how `routes/agents.py` emits synthetic `ToolCallCompleted` SSE events when tool metadata appears mid-stream).
- Streaming API convention (see `routes/agents.py`): SSE via `StreamingResponse`, each event a `data: {...}\n\n` JSON line with an `event` field (`StreamStart`, `AgentChunk`, `ToolCallCompleted`, `error`, `MetadataResponse`, `StreamEnd`). Non-JSON-serializable objects (Agno/Pydantic models, enums) go through a fallback serializer — follow this pattern for any new streaming endpoint rather than inventing a new event shape.

### Data layer

- Relational/agent-state storage: Supabase Postgres in prod, local SQLite for dev — selected via the `Database` factory above, not per-call flags.
- Vector store: Pinecone (`src/vector_store/`), namespaced per `PINECONE_NAMESPACE`/`PINECONE_GLOBAL_NAMESPACE`.
- Document/NoSQL storage: MongoDB (`src/database/no_relational_db/`), gated by `NOSQL_BACKEND`/`SAVE_MONGO`.
- File storage: Supabase Storage (`src/storage/`).

### Config / environment

No secrets are committed; `doc/envs/{dev,homol,prod}.env` are key-only templates (values stripped) showing the expected variable groups: LLM keys (OpenAI, Google/Gemini, Groq, Anthropic, HuggingFace), Pinecone, MongoDB, Supabase, plus app flags (`LOCAL`, `SAVE_LOGS`, `SAVE_MONGO`, `SHOW_INFO_LOGS`, `SHOW_METADATA`, `FORMAT_METADATA`, `NOSQL_BACKEND`). `LOCAL=true` disables API-key auth (see above) and should only be set in dev.

Deployment target is Railway (see `origins` in `src/web_services_network/config.py` and the `Procfile`); three environments — prod, homol (staging), dev — each with their own Railway URL.

### Logging / tracing

`src/tracing/` is the structured tracing/logging engine (`tracing_core.py`, `logger_engine.py`, `payload_builder.py`); `src/internal_services/` and `src/utils/logging_utils.py` hold adjacent logging utilities. `src/tracing/backup/` and several `backup/` subfolders elsewhere (e.g. `src/content_parse/backup/`) hold superseded implementations kept for reference — don't build on code under a `backup/` folder without checking whether it's still wired up anywhere.
