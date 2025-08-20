#!/usr/bin/env python3
import os
import re
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parent
CONTENT_DIR = ROOT / "docs" / "content"

ENGLISH_CUES = [
    r"\bPrerequisites\b", r"\bOverview\b", r"\bSummary\b", r"\bSteps\b",
    r"\bNote:\b", r"\bTip:\b", r"\bCaution:\b", r"\bWarning:\b",
    r"\bAbout GitHub\b", r"\bGitHub Actions\b", r"\bThis guide\b",
    r"\bYou can\b", r"\bTo [a-z]+:\b", r"\bExample\b", r"\bLearn more\b",
]
EN_PATTERN = re.compile("|".join(ENGLISH_CUES))
CODE_BLOCK = re.compile(r"```[\s\S]*?```", re.MULTILINE)
INLINE_CODE = re.compile(r"`[^`]+`")
LIQUID = re.compile(r"({%[^%]*%}|{{[^}]*}})")
URLS = re.compile(r"https?://[^\s)]+")
AR_CHARS = re.compile(r"[\u0600-\u06FF]")

SKIP_DIRS = {"assets", "images", "_snippets"}


def is_markdown(p: Path) -> bool:
    return p.suffix.lower() == ".md"


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(CONTENT_DIR))
    except Exception:
        return str(p)


def enumerate_md_files():
    for root, dirs, files in os.walk(CONTENT_DIR):
        # prune skip dirs
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".md"):
                yield Path(root) / f


def has_arabic(text: str) -> bool:
    return bool(AR_CHARS.search(text))


def _strip_non_prose(text: str) -> str:
    text = CODE_BLOCK.sub("", text)
    text = INLINE_CODE.sub("", text)
    text = LIQUID.sub("", text)
    text = URLS.sub("", text)
    return text

def _arabic_ratio(text: str) -> float:
    letters = re.findall(r"[A-Za-z\u0600-\u06FF]", text)
    if not letters:
        return 1.0
    arabic = re.findall(r"[\u0600-\u06FF]", text)
    return len(arabic) / len(letters)

def likely_english(text: str) -> bool:
    cleaned = _strip_non_prose(text)
    ratio = _arabic_ratio(cleaned)
    ascii_letters = len(re.findall(r"[A-Za-z]", cleaned))
    # Gate obvious English sections with cues but avoid counting mostly Arabic text
    if EN_PATTERN.search(cleaned) and ratio < 0.5:
        return True
    # Stricter heuristic
    return ascii_letters > 150 and ratio < 0.15


def main():
    en_files = []
    ar_files = []
    pairs = defaultdict(dict)  # stem -> { 'en': path, 'ar': path }

    for p in enumerate_md_files():
        name = p.name
        stem = name.replace("-ar.md", ".md")
        if name.endswith("-ar.md"):
            pairs[rel(p.with_name(stem))]["ar"] = p
            ar_files.append(p)
        else:
            pairs[rel(p)]["en"] = p
            en_files.append(p)

    missing_ar = []
    english_leakage = []
    ar_leakage = []

    for key, pair in pairs.items():
        en = pair.get("en")
        ar = pair.get("ar")
        if en and not ar:
            missing_ar.append(rel(en))
        if ar:
            try:
                txt = ar.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                txt = ""
            if likely_english(txt):
                english_leakage.append(rel(ar))
            # Check if trivially short or placeholder
            if len(txt.strip()) < 120 or "هذه الصفحة تحتاج" in txt or "> **ملاحظة**" in txt:
                ar_leakage.append(rel(ar))

    total_en = len(en_files)
    total_ar = len(ar_files)
    total_pairs = sum(1 for _ in pairs)

    print("=== Arabic Coverage Audit ===")
    print(f"Total English md files: {total_en}")
    print(f"Total Arabic md files:  {total_ar}")
    print(f"Total pairs discovered: {total_pairs}")
    print()

    print(f"Missing Arabic counterparts: {len(missing_ar)}")
    if missing_ar:
        for p in sorted(missing_ar)[:50]:
            print(f"  - {p}")
        if len(missing_ar) > 50:
            print(f"  ... and {len(missing_ar) - 50} more")
    print()

    print(f"Arabic files with likely English content: {len(english_leakage)}")
    if english_leakage:
        for p in sorted(english_leakage)[:50]:
            print(f"  - {p}")
        if len(english_leakage) > 50:
            print(f"  ... and {len(english_leakage) - 50} more")
    print()

    print(f"Arabic files that are too short/placeholder: {len(ar_leakage)}")
    if ar_leakage:
        for p in sorted(ar_leakage)[:50]:
            print(f"  - {p}")
        if len(ar_leakage) > 50:
            print(f"  ... and {len(ar_leakage) - 50} more")

    # Save report
    report = ROOT / "translation_audit_report.md"
    with report.open("w", encoding="utf-8") as f:
        f.write("# Arabic Translation Coverage Audit\n\n")
        f.write(f"- Total English md files: {total_en}\n")
        f.write(f"- Total Arabic md files: {total_ar}\n")
        f.write(f"- Total pairs discovered: {total_pairs}\n\n")
        f.write(f"- Missing Arabic counterparts: {len(missing_ar)}\n")
        for pth in sorted(missing_ar):
            f.write(f"  - {pth}\n")
        f.write("\n")
        f.write(f"- Arabic files with likely English content: {len(english_leakage)}\n")
        for pth in sorted(english_leakage):
            f.write(f"  - {pth}\n")
        f.write("\n")
        f.write(f"- Arabic files that are too short/placeholder: {len(ar_leakage)}\n")
        for pth in sorted(ar_leakage):
            f.write(f"  - {pth}\n")
    print(f"\nSaved detailed report to: {report}")

if __name__ == "__main__":
    main()
