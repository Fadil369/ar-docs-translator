#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).parent
AUDIT_FILE = ROOT / "translation_audit_report.md"
TRANSLATOR = ROOT / "local_ai_translator.py"

def parse_flagged_paths(text: str) -> List[str]:
    paths: List[str] = []
    in_section = False
    for line in text.splitlines():
        header = line.strip().lstrip("- ")
        if header.startswith("Arabic files with likely English content:"):
            in_section = True
            continue
        if in_section:
            term = line.strip().lstrip("- ")
            if term.startswith("Arabic files that are too short/placeholder:") or term.startswith("Saved detailed report to:"):
                break
            if line.strip().startswith("- "):
                # Lines may wrap; collapse visual wraps by removing trailing hyphenated breaks
                item = line.strip()[2:]
                item = item.replace("\u200b", "").replace("  ", " ")
                paths.append(item)
    # Clean up wrapped list artifacts
    cleaned: List[str] = []
    for p in paths:
        # remove possible trailing spaces and wrap artifacts
        p = p.strip()
        # ensure it ends with -ar.md
        if not p.endswith("-ar.md"):
            # try to stitch if a wrapped hyphenated line cut; skip if invalid
            pass
        cleaned.append(p)
    # Deduplicate and filter obvious non-paths
    uniq: List[str] = []
    for p in cleaned:
        if p and (".md" in p) and ("-ar.md" in p) and p not in uniq:
            uniq.append(p)
    return uniq


def main():
    if not AUDIT_FILE.exists():
        print(f"Audit file not found: {AUDIT_FILE}")
        sys.exit(1)
    report = AUDIT_FILE.read_text(encoding="utf-8")
    flagged = parse_flagged_paths(report)
    if not flagged:
        print("No flagged files found in audit.")
        return

    print(f"Re-enhancing {len(flagged)} flagged files...")

    import subprocess
    errors = 0
    ok = 0
    for rel in flagged:
        # Some lines may be just the filename without the leading docs/content/; normalize
        if not rel.startswith("docs/content/"):
            # try treat as relative under docs/content
            candidate = ROOT / "docs" / "content" / rel
            if candidate.exists():
                path = candidate
            else:
                path = ROOT / rel
        else:
            path = ROOT / rel
        if not path.exists():
            print(f"Skip missing: {rel}")
            continue

        cmd = [sys.executable, str(TRANSLATOR), "--file", str(path), "--root", str(ROOT / "docs"), "--aggressive"]
        try:
            res = subprocess.run(cmd, cwd=str(ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            if res.returncode == 0:
                ok += 1
                print(f"OK: {rel}")
            else:
                errors += 1
                print(f"ERROR {rel}:\n{res.stdout}")
        except Exception as e:
            errors += 1
            print(f"ERROR running translator on {rel}: {e}")

    print(f"Done. Success: {ok}, Errors: {errors}")

if __name__ == "__main__":
    main()
