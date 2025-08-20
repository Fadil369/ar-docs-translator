# Docs AI Translator — Local + Cloudflare Deploy

This repo contains:

- FastAPI backend (`webapp/`) with universal ingestion (PDF/DOCX/MD/TXT/HTML/CSV), enhanced Arabic translation, optional Arabic-only cleanup, and a quick audit.
- Web UI (`webapp/templates/`, `webapp/static/`), plus a lightweight Cloudflare Pages UI (`pages/`).
- Cloudflare Worker (`cloudflare/worker/`) to proxy `/api/*` to your backend origin.
- GitHub Actions workflow for deploying Worker + Pages (`.github/workflows/deploy-cloudflare.yml`).

## Local run

```bash
# from repo root
source .venv/bin/activate
uvicorn webapp.app:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
# open http://127.0.0.1:8000
```

## Cloudflare deployment

### 1) Cloudflare Worker (API proxy)

- Edit `cloudflare/worker/wrangler.toml` and set `API_ORIGIN` to your backend URL (public origin).
- Or set it at deploy time (CI does this via `CF_API_ORIGIN`).

Manual deploy:

```bash
cd cloudflare/worker
npm i
npx wrangler deploy --var API_ORIGIN="https://your-backend.example.com"
```

### 2) Cloudflare Pages (UI)

- Pages serves `pages/` with a single-page uploader UI.
- The workflow injects `window.API_BASE` to your Worker URL via `CF_WORKER_URL` secret.

## GitHub Actions (CI)

Workflow: `.github/workflows/deploy-cloudflare.yml`

Required GitHub repo secrets:

- `CF_API_TOKEN`: Cloudflare API token (Workers + Pages write perms)
- `CF_ACCOUNT_ID`: Cloudflare account ID
- `CF_API_ORIGIN`: Public backend origin URL (for the Worker proxy)
- `CF_WORKER_URL`: Worker URL (e.g., `https://docs-ai-translator-api.YOUR.workers.dev`)

On push to `main`, the workflow:

- Deploys Pages (`pages/`) and injects `window.API_BASE` with `CF_WORKER_URL`.
- Deploys the Worker with Wrangler and passes `API_ORIGIN`.

### Quick secrets setup via GitHub CLI

```bash
# Replace with your repo
REPO="Fadil369/ar-docs-translator"

# Set required secrets
gh secret set CF_API_TOKEN -R "$REPO"
gh secret set CF_ACCOUNT_ID -R "$REPO"
gh secret set CF_API_ORIGIN -R "$REPO"   # e.g. https://api.example.com
gh secret set CF_WORKER_URL -R "$REPO"    # e.g. https://your-worker.workers.dev
```

## Notes

- For best PDF results, try PDF modes: `auto`, `fitz`, `plumber`, `layout`, `pdfminer`.
- Enable "Arabic-only (remove English)" for a polished Arabic output. This removes code/links/English and normalizes digits/punctuation.
