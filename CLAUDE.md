# Deep Financial Research Assistant

## What This Is
A POC agentic AI app for querying SEC 10-K filings for S&P 500 companies.
LangGraph handles agent orchestration (multi-node supervisor pattern).
Streamlit is the UI. Deployed on GCP Cloud Run.

## Stack
- **Agent**: LangGraph
- **UI**: Streamlit
- **Vector DB**: ChromaDB (OpenAI `text-embedding-3-small` embeddings)
- **LLM**: OpenAI GPT-4.1 family
- **Config**: Pydantic settings with `SecretStr` for all secrets
- **Linting**: Pylint (VS Code)
- **Deployment**: Docker on GCP Cloud Run via Cloud Build

## Key Commands
```bash
streamlit run src/app.py        # run the app
python src/main.py              # CLI interface for testing without UI
pylint src/                     # lint
pip install -r requirements.txt # install deps
gcloud builds submit --config cloudbuild.yaml  # deploy to GCP
```

## Where Things Live
- `src/graph/state.py` — GraphState schema (source of truth for state fields)
- `src/graph/blueprint.py` — graph definition and routing logic
- `src/nodes/` — one file per node
- `src/components/` — Streamlit UI components
- `src/utils/config.py` — all secrets and settings (Pydantic)
- `scripts/` — data pipeline (ingest from EDGAR, index into ChromaDB)
- `data/raw/` — downloaded SEC filings (never commit)
- `data/index/` — ChromaDB vector store, ~2.1 GB (never commit)

## Architecture Principles
- `app.py` is UI only — no business logic, no graph construction
- Nodes are pure functions: take `GraphState` in, return a partial `dict` out — never mutate state in place
- Graph is compiled once at module level, not inside request handlers or Streamlit callbacks
- All secrets go through `src/utils/config.py` — never `os.environ` directly in nodes or components
- Use `logging` (from `src/utils/logging.py`) — never `print()` in production code

## Code Style
- PEP 8, enforced by Pylint
- Type hints on all functions — especially node signatures: `def node_name(state: GraphState) -> dict:`
- `TypedDict` for all state schemas
- Google-style docstrings on all public functions and classes
- Max line length: 100 characters

## Environment Variables
See `.env.example` for the full list. In GCP, secrets are injected via Secret Manager.
- `OPENAI_API_KEY`
- `EDGAR_IDENTITY`
- `DEEP_FINANCIAL_RESEARCH_PASSWORD`

## Git Conventions
- **Branches**: `feat/<desc>`, `fix/<desc>`, `refactor/<desc>`, `chore/<desc>`, `docs/<desc>`
- **Commits**: Conventional Commits — `<type>(<scope>): <description>`
  - Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `style`
  - Scopes: `graph`, `node`, `search`, `ui`, `auth`, `data`, `deploy`, `config`, `deps`
- **Never commit**: `.env`, `data/raw/`, `data/index/`, `__pycache__/`
- **Never push directly to `main`**