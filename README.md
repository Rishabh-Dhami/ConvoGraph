# ConvoGraph — Conversational Workflow with LLMs

## Overview

ConvoGraph is an experimental conversational workflow demo that combines a StateGraph-based chat flow with LLM-powered responses and optional SQLite checkpointing. The project is intended as a small platform to prototype conversation flows, thread management and LLM integrations using a Streamlit UI.

Key goals:
- Demonstrate multi-threaded chat sessions (thread ids) and a sidebar history UI.
- Provide optional local checkpointing (SQLite) for persisted conversation state.
- Auto-generate short titles for conversations using an LLM prompt.

## Features

- Multi-thread chat sessions with generated thread titles
- Streamlit-based UI for quick local interaction (`src/core.py`)
- Pluggable checkpointing: `SqliteSaver` (if available) or in-memory fallback
- Title generation using a configurable system prompt (`src/prompts.py`)
- Minimal helper utilities for loading/saving threads (`src/utils.py`)

## Architecture

The codebase is intentionally small and contains three main pieces:

1. LLM & Graph logic (`src/app.py`)
	- Initializes LLM client, StateGraph, and optional checkpointing.
	- Exposes `chat = graph.compile(checkpointer=...)` which other modules use to invoke the chain.

2. Streamlit UI (`src/core.py`)
	- Sidebar: thread list, new thread button, and thread switching.
	- Main area: chat messages and chat input; automatically triggers title generation for first messages.

3. Utilities & Prompts (`src/utils.py`, `src/prompts.py`)
	- Helpers for thread id generation, loading chats from a checkpoint, and generating titles.
	- Prompt templates used to direct LLM behavior.

Support files:
- `src/init_db.py` — small helper to create a local SQLite DB and example data.
- `src/database/` — directory for local DB (ignored by Git by default; `.gitkeep` is included to preserve the folder).

## Prerequisites

- Python 3.10+ (3.11 recommended)
- Virtual environment for isolated dependencies
- LLM provider API key (e.g., Google/Oracle/OpenAI) configured in `.env`

Optional services depending on your connector:
- LangChain / langgraph packages
- Provider-specific client libraries (e.g., `langchain-google-genai`)

## Installation

1. Clone the repository

```bash
git clone <repo-url>
cd ConvoGraph
```

2. Create a virtual environment and activate it

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
```

3. Install dependencies

```powershell
pip install -r requirements.txt
```

4. Create a `.env` file in the repo root and set provider keys

Example `.env` entries (adapt names for your provider):

```
GOOGLE_API_KEY=your_google_api_key
# or OPENAI_API_KEY=your_openai_api_key
# LANGGRAPH_API_KEY=...
```

## Setup (local DB)

Initialize the local SQLite database (creates `src/database/convo_graph.db` and sample data):

```powershell
python src/init_db.py
```

This script will create a `threads` and `messages` schema and add an example conversation.

## Running the app

Run the Streamlit UI for interactive testing:

```powershell
streamlit run src/core.py
```

Or run core modules directly for debugging:

```powershell
python src/app.py   # checks LLM and graph wiring (non-UI)
```

## Usage examples

- Start a new chat in the sidebar (`New Chat`). The first user + assistant exchange will automatically generate a short conversation title and appear in the sidebar.
- To test title generation directly (without Streamlit):

```powershell
python - <<'PY'
from src.utils import generate_title
print(generate_title('I need a short Python snippet to reverse a list'))
PY
```

## API / Integration points

ConvoGraph does not ship a separate HTTP API by default — the primary interaction is via the Streamlit frontend which calls into the compiled `chat` object from `src/app.py`.

If you want to expose REST endpoints, consider adding a small FastAPI wrapper that calls `chat.invoke(...)` and persists the state using the same checkpointer.

## Technical details

- Checkpointing: `src/app.py` will attempt to use `SqliteSaver(conn=conn)` if `langgraph` provides it; otherwise it falls back to `InMemorySaver()`.
- Thread storage: The `checkpointer` stores conversation messages and exposes `list()` and `get_state()` as used in `src/utils.py`.
- Title generator: `src/utils.generate_title` uses `ChatPromptTemplate` to assemble a system + user prompt and invoke the LLM. The function normalizes different return types and falls back to `"New Conversation"` on error.

## Troubleshooting

- ModuleNotFoundError for langgraph checkpoint modules: install `langgraph-checkpoint-sqlite` (package name may vary), or rely on the in-memory fallback.
- `sqlite3.OperationalError`: ensure `src/database/` exists and is writable; `src/init_db.py` will create it for you.
- LLM API errors: check your `.env` and provider quota/permissions.

## Development

- To reproduce the exact environment from the developer machine, use the provided `requirements.txt`.
- If you prefer a minimal runtime-only set (recommended for contributors), I can generate a `requirements-runtime.txt` containing only the packages required to run the app (Streamlit, python-dotenv, provider connectors, etc.).

## Contributing

- Fork the repo and open a PR against `main`.
- Keep secrets and local DB files out of Git; use `.env` and ensure `src/database/*.db` is ignored.

## Authors

- Rishabh Dhami — project lead

---

If you want, next steps I can implement for you:

- A — Add a simple FastAPI wrapper exposing basic conversation endpoints
- B — Produce a slim `requirements-runtime.txt` containing only runtime packages
- C — Add sample screenshots and a short GitHub repo description

Reply with one or more options (A/B/C) and I'll implement them.

Live (local): Run the Streamlit app at `src/core.py`.

## Features

- Conversation threads managed by `langgraph` StateGraph
- Streamlit UI (`src/core.py`) with sidebar thread list and chat UI
- Optional SQLite checkpointing (local DB at `src/database/convo_graph.db`)
- Auto-generated titles for new threads using an LLM prompt

## Quick Start (Windows / PowerShell)

Prerequisites: Python 3.10+, a virtual environment, and any provider API keys your LLM connector requires.

1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\\.venv\\Scripts\\Activate
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Configure environment variables

Create a `.env` in the repo root with keys your LLM provider requires (example names — adapt for your provider):

```
GOOGLE_API_KEY=your_google_key
# or OPENAI_API_KEY=your_openai_key
# LANGGRAPH_API_KEY=...
```

4. Run the Streamlit UI

```powershell
streamlit run src/core.py
```

Or run `src/app.py` directly for quick checks:

```powershell
python src/app.py
```

## Project Layout

- `src/app.py` — LLM/graph setup and checkpoint configuration
- `src/core.py` — Streamlit frontend (sidebar, chat UI, thread switching)
- `src/utils.py` — helper utilities (thread id generation, load chats, title generation)
- `src/prompts.py` — prompts used for chat and title generation
- `src/database/` — local SQLite DB (ignored by Git)

## Database / Checkpointing

- The app stores checkpoints in `src/database/convo_graph.db` when `SqliteSaver` is available. The folder is created automatically.
- DB files are ignored by Git. To keep the directory tracked, add `src/database/.gitkeep`.
- Quick DB creation/verify:

```powershell
python - <<'PY'
from pathlib import Path
import sqlite3
p = Path('src') / 'database' / 'convo_graph.db'
p.parent.mkdir(parents=True, exist_ok=True)
conn = sqlite3.connect(str(p))
conn.execute('PRAGMA user_version')
conn.close()
print('DB created/verified at', p.resolve())
PY
```

## Auto-title Generation

- When the first user+assistant messages are saved in a thread, the app calls `generate_title` (in `src/utils.py`) to create a short descriptive thread title using the system prompt in `src/prompts.py`.
- If the LLM call fails or returns an unexpected type, the app falls back to `"New Conversation"` and logs the error.

## Troubleshooting & Common Issues

- `ModuleNotFoundError: No module named 'langgraph.checkpoint.sqlite'`: some `langgraph` releases split checkpoint modules; `src/app.py` uses a safe fallback to `InMemorySaver` if `SqliteSaver` is unavailable.
- `sqlite3.OperationalError: unable to open database file`: ensure `src/database/` exists and the process has write permission.
- API / credential errors for LLM: verify `.env` is present and loaded (`python-dotenv`), and confirm provider quotas and network access.

## Development Tips

- Recreate environment with `requirements.txt`:

```powershell
pip install -r requirements.txt
```

- Test the title generator without the UI:

```powershell
python - <<'PY'
from src.utils import generate_title
print(generate_title('I need a short Python script to reverse a list'))
PY
```

## Contributing

- Fork the repo, create a branch, and open a pull request against `main`.
- Keep secrets and local DB files out of the repo — use `.env` and the ignored `src/database/*.db` files.

## License

- Add a `LICENSE` file if you want to make usage terms explicit.

## Authors

- Rishabh Dhami — ConvoGraph project lead

---

If you'd like, I can next:

- add an `init_db.py` to create tables and example data,
- add `src/database/.gitkeep` so the directory appears in the repo,
- slim `requirements.txt` to runtime-only packages,
- or produce a short GitHub-friendly README summary for the repo description.

