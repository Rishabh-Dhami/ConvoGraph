# ConvoGraph — Conversational Workflow with LLMs

ConvoGraph is a compact demo that combines a StateGraph-driven chat workflow with LLM-powered responses and optional SQLite checkpointing. It provides a Streamlit-based UI for multi-threaded chat sessions and automatic short-title generation for new conversations.

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

