Docs AI Translator Web App

Quick start

- Create and activate a virtual environment
- Install requirements
- Run the server

Commands

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn webapp.app:app --reload --port 8000
```

Usage

- Open http://localhost:8000
- Drag-and-drop a single Markdown file to get immediate enhanced Arabic output (with a progress bar)
- Or drag-and-drop a ZIP containing a docs `content/` tree; you’ll see an audit preview (flagged files list), then click Download to get a ZIP with Arabic files and `translation_audit_report.md`

Notes

- The web app imports `local_ai_translator.py` from the repo root and uses its intelligent enhancement pipeline (aggressive mode optional)
- The audit preview and the report inside the ZIP use the stricter heuristic implemented in the app
