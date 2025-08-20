#!/usr/bin/env python3
import io
import os
import re
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.templating import Jinja2Templates
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from uuid import uuid4
import asyncio

# Ensure we can import the local translator from repo root
ROOT = Path(__file__).resolve().parents[1]
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from local_ai_translator import LocalAITranslator


app = FastAPI(title="Docs AI Translator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

# Simple in-memory session store for produced ZIPs (dev/demo use)
SESSION_STORE = {}

# Background job state for universal file translation
JOBS = {}


def _strip_non_prose(text: str) -> str:
    text = re.sub(r"```[\s\S]*?```", "", text, flags=re.MULTILINE)
    text = re.sub(r"`[^`]+`", "", text)
    text = re.sub(r"({%[^%]*%}|{{[^}]*}})", "", text)
    text = re.sub(r"https?://[^\s)]+", "", text)
    return text


def _arabic_ratio(text: str) -> float:
    letters = re.findall(r"[A-Za-z\u0600-\u06FF]", text)
    if not letters:
        return 1.0
    arabic = re.findall(r"[\u0600-\u06FF]", text)
    return len(arabic) / len(letters)


def _likely_english(text: str) -> bool:
    cleaned = _strip_non_prose(text)
    ratio = _arabic_ratio(cleaned)
    ascii_letters = len(re.findall(r"[A-Za-z]", cleaned))
    if re.search(r"\b(Prerequisites|Overview|Summary|Steps|Note:|Tip:|Caution:|Warning:)\b", cleaned) and ratio < 0.5:
        return True
    return ascii_letters > 150 and ratio < 0.15


def _strip_html(html: str) -> str:
    html = re.sub(r"<script[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<style[\s\S]*?</style>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"\s+", " ", html)
    return html.strip()


def _extract_text_generic(path: Path) -> str:
    ext = path.suffix.lower()
    try:
        if ext in {".md", ".txt", ".csv", ".log", ".rtf"}:
            raw = path.read_bytes()
            try:
                return raw.decode("utf-8")
            except Exception:
                return raw.decode("latin-1", errors="ignore")
        if ext in {".html", ".htm"}:
            raw = path.read_text(encoding="utf-8", errors="ignore")
            return _strip_html(raw)
        if ext == ".docx":
            try:
                import docx  # python-docx
                doc = docx.Document(str(path))
                return "\n".join(p.text for p in doc.paragraphs)
            except Exception:
                return ""
        if ext == ".pdf":
            try:
                from pdfminer.high_level import extract_text
                return extract_text(str(path)) or ""
            except Exception:
                return ""
    except Exception:
        return ""
    # Fallback best-effort decode
    raw = path.read_bytes()
    try:
        return raw.decode("utf-8")
    except Exception:
        return raw.decode("latin-1", errors="ignore")


async def _process_file_job(session_id: str, src_path: Path, aggressive: bool, desired_format: str):
    JOBS[session_id] = {
        "status": "processing",
        "progress": 0,
        "preview": "",
        "download_path": None,
        "audit_flagged": False,
        "error": None,
    }
    try:
        text = _extract_text_generic(src_path)
        translator = LocalAITranslator(docs_root=str(ROOT / "docs"), aggressive=aggressive)
        total = max(1, (len(text) // 10000) + 1)
        out_parts: List[str] = []
        for idx in range(total):
            start = idx * 10000
            chunk = text[start:start + 10000]
            if not chunk:
                break
            enhanced = translator.translate_text_intelligent(chunk)
            out_parts.append(enhanced)
            JOBS[session_id]["progress"] = int(((idx + 1) / total) * 100)
            await asyncio.sleep(0)  # yield

        output_text = "\n\n".join(out_parts)

        # Wrap as Markdown frontmatter if requested
        sess_dir = src_path.parent
        if desired_format == "md":
            title = src_path.stem
            frontmatter = f"---\nlang: ar\ntitle: \"{title}\"\n---\n\n"
            output_text = frontmatter + output_text
            out_path = sess_dir / f"{src_path.stem}-ar.md"
        else:
            out_path = sess_dir / f"{src_path.stem}-ar.txt"

        out_path.write_text(output_text, encoding="utf-8")
        JOBS[session_id]["download_path"] = str(out_path)
        JOBS[session_id]["preview"] = output_text[:5000]
        JOBS[session_id]["audit_flagged"] = _likely_english(output_text)
        JOBS[session_id]["status"] = "completed"
        JOBS[session_id]["progress"] = 100
    except Exception as e:
        JOBS[session_id]["status"] = "error"
        JOBS[session_id]["error"] = str(e)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/translate-file")
async def translate_file(file: UploadFile = File(...), aggressive: bool = Form(False)):
    raw = await file.read()
    try:
        content = raw.decode("utf-8")
    except Exception:
        return JSONResponse({"error": "Unable to decode file as UTF-8"}, status_code=400)

    translator = LocalAITranslator(docs_root=str(ROOT / "docs"), aggressive=aggressive)
    front, body = translator.extract_frontmatter(content)
    enhanced_front = translator.enhance_frontmatter(front)
    output_md = translator.generate_enhanced_content(body, enhanced_front)

    return JSONResponse({
        "filename": file.filename,
        "aggressive": aggressive,
        "output_markdown": output_md,
    })


@app.post("/api/translate-archive")
async def translate_archive(file: UploadFile = File(...), aggressive: bool = Form(False)):
    # Prepare session temp dirs
    sess_dir = Path(tempfile.mkdtemp(prefix="translate_session_"))
    docs_root = sess_dir / "docs"
    content_dir = docs_root / "content"
    content_dir.mkdir(parents=True, exist_ok=True)

    # Extract ZIP into content_dir
    raw = await file.read()
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            zf.extractall(str(content_dir))
    except Exception as e:
        shutil.rmtree(sess_dir, ignore_errors=True)
        return JSONResponse({"error": f"Invalid ZIP: {e}"}, status_code=400)

    # Translate all .md (skip existing -ar.md)
    translator = LocalAITranslator(docs_root=str(docs_root), aggressive=aggressive)
    produced: List[Path] = []

    for p in content_dir.rglob("*.md"):
        if p.name.endswith("-ar.md"):
            continue
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
            front, body = translator.extract_frontmatter(txt)
            enhanced_front = translator.enhance_frontmatter(front)
            output_md = translator.generate_enhanced_content(body, enhanced_front)
            out_path = p.with_name(p.stem + "-ar.md")
            out_path.write_text(output_md, encoding="utf-8")
            produced.append(out_path)
        except Exception:
            continue

    # Build a lightweight audit report over produced Arabic files
    flagged: List[str] = []
    for ar in produced:
        try:
            txt = ar.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if _likely_english(txt):
            rel = str(ar.relative_to(content_dir))
            flagged.append(rel)

    report = sess_dir / "translation_audit_report.md"
    with report.open("w", encoding="utf-8") as f:
        f.write("# Arabic Translation Coverage Audit (Upload Session)\n\n")
        f.write(f"- Total produced Arabic md files: {len(produced)}\n\n")
        f.write(f"- Arabic files with likely English content: {len(flagged)}\n")
        for pth in sorted(flagged):
            f.write(f"  - {pth}\n")

    # Zip up the content directory and report
    out_zip = sess_dir / "translated_output.zip"
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in content_dir.rglob("*"):
            if path.is_file():
                z.write(path, arcname=str(Path("content") / path.relative_to(content_dir)))
        z.write(report, arcname="translation_audit_report.md")
    # Create a session id and store path for later download
    session_id = uuid4().hex
    SESSION_STORE[session_id] = str(out_zip)

    return JSONResponse({
        "session_id": session_id,
        "produced_count": len(produced),
        "flagged": sorted(flagged),
        "aggressive": aggressive
    })


@app.get("/api/download/{session_id}")
def download_result(session_id: str):
    path = SESSION_STORE.get(session_id)
    if not path or not Path(path).exists():
        return JSONResponse({"error": "Invalid or expired session."}, status_code=404)
    return FileResponse(path=path, filename="translated_output.zip")


@app.post("/api/ingest-file")
async def ingest_file(file: UploadFile = File(...), aggressive: bool = Form(False), desired_format: str = Form("md")):
    sess_dir = Path(tempfile.mkdtemp(prefix="universal_session_"))
    src_path = sess_dir / (file.filename or "uploaded")
    # stream copy to disk
    with src_path.open("wb") as f:
        await asyncio.to_thread(shutil.copyfileobj, file.file, f)

    session_id = uuid4().hex
    asyncio.create_task(_process_file_job(session_id, src_path, aggressive, desired_format))
    return JSONResponse({"session_id": session_id, "status": "processing"})


@app.get("/api/progress/{session_id}")
def get_progress(session_id: str):
    job = JOBS.get(session_id)
    if not job:
        return JSONResponse({"error": "Unknown session"}, status_code=404)
    resp = {k: v for k, v in job.items() if k != "download_path"}
    resp["can_download"] = bool(job.get("download_path"))
    return JSONResponse(resp)


@app.get("/api/download-file/{session_id}")
def download_file(session_id: str, format: Optional[str] = None):
    job = JOBS.get(session_id)
    if not job or not job.get("download_path"):
        return JSONResponse({"error": "Not ready"}, status_code=404)
    path = Path(job["download_path"])
    if format == "txt" and path.suffix != ".txt":
        # convert on the fly to .txt
        txt_path = path.with_suffix(".txt")
        try:
            content = Path(job["download_path"]).read_text(encoding="utf-8", errors="ignore")
            txt_path.write_text(content, encoding="utf-8")
            path = txt_path
        except Exception:
            pass
    return FileResponse(path=str(path), filename=path.name)

def create_app():
    return app
