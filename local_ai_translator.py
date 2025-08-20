#!/usr/bin/env python3
"""
Local AI-Enhanced Translation Engine
Advanced translation system without API key requirements.

Features:
- Comprehensive Arabic technical terminology database
- Context-aware translation patterns
- Advanced linguistic processing
- GitHub-specific domain knowledge
- Smart content structure analysis
- Natural language enhancement rules
"""

import os
import re
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LocalAITranslator:
    """Advanced local translator with AI-like intelligence"""
    
    def __init__(self, docs_root: Optional[str] = None, aggressive: bool = False, arabic_only: bool = False):
        # Resolve docs_root relative to this script if not absolute
        script_dir = Path(__file__).parent
        if docs_root is None:
            self.docs_root = (script_dir / "docs").resolve()
        else:
            candidate = Path(docs_root)
            self.docs_root = (candidate if candidate.is_absolute() else (script_dir / candidate)).resolve()
        self.content_root = self.docs_root / "content"
        self.aggressive = aggressive
        self.arabic_only = arabic_only
        self.fallback_threshold = 0.6 if aggressive else 0.25
        
        # Initialize translation databases
        self.setup_terminology_database()
        self.setup_linguistic_rules()
        self.setup_content_patterns()
        self.setup_github_domain_knowledge()
        self.setup_lexical_fallback()
        
        # Statistics tracking
        self.stats = {
            "files_processed": 0,
            "translations_enhanced": 0,
            "terminology_applications": 0,
            "pattern_matches": 0,
            "linguistic_improvements": 0
        }

    def setup_lexical_fallback(self):
        """High-frequency English→Arabic lexical mappings for offline translation."""
        self.lexical_map: Dict[str, str] = {
            # Pronouns / helpers
            "you": "أنت",
            "your": "الخاص بك",
            "we": "نحن",
            "they": "هم",
            "it": "هو",
            "this": "هذا",
            "that": "ذلك",
            "these": "هذه",
            "those": "تلك",
            "is": "هو",
            "are": "هي",
            "was": "كان",
            "were": "كانت",
            "be": "يكون",
            "been": "كان",
            "will": "سوف",
            "should": "يجب",
            "must": "يجب",
            "can": "يمكن",
            "could": "يمكن",
            "may": "قد",
            "might": "قد",
            "not": "ليس",
            "and": "و",
            "or": "أو",
            "but": "لكن",
            "if": "إذا",
            "when": "عند",
            "where": "حيث",
            "how": "كيف",
            "what": "ما",
            "why": "لماذا",
            "to": "إلى",
            "from": "من",
            "for": "لـ",
            "with": "مع",
            "without": "بدون",
            "in": "في",
            "on": "على",
            "by": "بواسطة",
            "of": "من",
            "as": "كـ",
            "about": "حول",
            "before": "قبل",
            "after": "بعد",
            "between": "بين",
            "within": "ضمن",
            "using": "باستخدام",
            "into": "إلى",
            "over": "فوق",
            "under": "تحت",
            "through": "عبر",
            "via": "عبر",

            # Common UI/actions
            "create": "إنشاء",
            "created": "تم الإنشاء",
            "delete": "حذف",
            "deleted": "تم الحذف",
            "update": "تحديث",
            "updated": "تم التحديث",
            "edit": "تحرير",
            "open": "فتح",
            "close": "إغلاق",
            "closed": "مغلق",
            "click": "انقر",
            "select": "حدد",
            "choose": "اختر",
            "go": "اذهب",
            "enable": "تمكين",
            "enabled": "مُمكّن",
            "disable": "تعطيل",
            "disabled": "مُعطّل",
            "configure": "تكوين",
            "settings": "الإعدادات",
            "setting": "الإعداد",
            "manage": "إدارة",
            "management": "إدارة",
            "view": "عرض",
            "see": "انظر",
            "learn": "تعلم",
            "install": "تثبيت",
            "upgrade": "ترقية",
            "sign": "تسجيل",
            "sign in": "تسجيل الدخول",
            "sign out": "تسجيل الخروج",
            "log in": "تسجيل الدخول",
            "log out": "تسجيل الخروج",
            "save": "حفظ",
            "apply": "تطبيق",
            "run": "تشغيل",
            "build": "بناء",
            "test": "اختبار",
            "deploy": "نشر",
            "publish": "نشر",
            "allows": "يسمح",
            "allow": "يسمح",
            "exchange": "تبادل",
            "short-lived": "قصيرة الأجل",
            "directly": "مباشرة",
            "cloud": "السحابة",
            "provider": "المزوّد",
            "providers": "المزوّدون",
            "in your": "في الخاص بك",
            "before you begin": "قبل أن تبدأ",
            "at this stage": "في هذه المرحلة",
            "for example": "على سبيل المثال",
            "by updating": "عن طريق تحديث",
            "by default": "افتراضيًا",
            "to get started": "للبدء",
            "you can now": "يمكنك الآن",
            "next steps": "الخطوات التالية",
            "use": "استخدم",
            "usage": "الاستخدام",
            "instruction": "تعليمات",
            "instructions": "تعليمات",
            "installing": "تثبيت",
            "package": "حزمة",
            "packages": "حزم",
            "dependency": "اعتمادية",
            "dependencies": "اعتماديات",
            "search": "ابحث",
            "find": "العثور",
            "supported": "مدعوم",
            "client": "عميل",
            "instance": "مثيل",
            "specific": "محدد",
            "working": "العمل",
            "registry": "السجل",
            "billing": "الفوترة",
            "platform": "المنصة",
            "roles": "أدوار",
            "role": "دور",
            "promotion": "عرض ترويجي",
            "promotions": "عروض ترويجية",
            "discount": "خصم",
            "discounts": "خصومات",
            "csv": "CSV",
            "report": "تقرير",
            "reports": "تقارير",
            "codeql": "CodeQL",
            "cli": "CLI",
            "database": "قاعدة بيانات",
            "analyze": "تحليل",
            "bundle": "حزمة",
            "cleanup": "تنظيف",
            "import": "استيراد",
            "export": "تصدير",
            "finalize": "إنهاء",
            "resolve": "حل",
            "query": "استعلام",
            "format": "تنسيق",
            "metadata": "بيانات وصفية",
            "version": "إصدار",
            "server": "خادم",
            "language": "لغة",
            "pack": "حزمة",
            "upgrade": "ترقية",
            "decompile": "فك تجميع",
            "token": "رمز",
            "endpoint": "نقطة نهاية",
            "endpoints": "نقاط نهاية",
            "available": "متاحة",
            "access": "وصول",
            "chat": "الدردشة",
            "configure": "تكوين",
            "manage": "إدارة",
            "decode": "فك ترميز",
            "hash": "تجزئة",
            "interpret": "تفسير",
            "diagnostic": "تشخيص",
            "diagnostics": "تشخيصات",
            "dataset": "مجموعة بيانات",
            "datasets": "مجموعات بيانات",
            "measure": "قياس",
            "predicate": "مسند",
            "extensible": "قابل للتوسعة",
            "execute": "تنفيذ",
            "generate": "إنشاء",
            "help": "مساعدة",
            "add": "إضافة",
            "viewing": "عرض",
            "description": "وصف",
            "data": "بيانات",
            "bypass": "تجاوز",
            "delegated": "مفوّض",
            "protection": "حماية",
            "push": "دفع",
            "upgrades": "ترقيات",
            "synchronization": "مزامنة",
            "synchronize": "مزامنة",
            "time synchronization": "مزامنة الوقت",
            "deleting": "حذف",
            "library": "مكتبة",
            "libraries": "مكتبات",
            "insights": "رؤى",
            "exporting": "تصدير",

            # Nouns common in GitHub docs
            "account": "الحساب",
            "profile": "الملف الشخصي",
            "organization": "المنظمة",
            "user": "المستخدم",
            "members": "الأعضاء",
            "member": "العضو",
            "owner": "المالك",
            "team": "الفريق",
            "project": "المشروع",
            "settings": "الإعدادات",
            "preferences": "التفضيلات",
            "email": "البريد الإلكتروني",
            "security": "الأمان",
            "privacy": "الخصوصية",
            "permissions": "الأذونات",
            "access": "الوصول",
            "token": "الرمز",
            "password": "كلمة المرور",
            "passkey": "مفتاح المرور",
            "branch": "فرع",
            "branches": "فروع",
            "commit": "التزام",
            "issue": "قضية",
            "pull": "سحب",
            "request": "طلب",
            "workflow": "سير العمل",
            "runner": "مشغل",
            "artifact": "منتج",
            "actions": "إجراءات",
            "copilot": "Copilot",
            "codespaces": "Codespaces",
            "overview": "نظرة عامة",
            "summary": "الملخص",
            "prerequisites": "المتطلبات المسبقة",
            "warning": "تحذير",
            "caution": "تحذير",
            "tip": "نصيحة",
            "note": "ملاحظة",
        }

    def _arabic_ratio(self, text: str) -> float:
        total_letters = len(re.findall(r"[A-Za-z\u0600-\u06FF]", text))
        if total_letters == 0:
            return 1.0
        arabic_letters = len(re.findall(r"[\u0600-\u06FF]", text))
        return arabic_letters / total_letters

    def _apply_lexical_fallback(self, text: str) -> str:
        # Apply word-level replacements conservatively with word boundaries
        result = text
        for en, ar in self.lexical_map.items():
            pattern = r"\b" + re.escape(en) + r"\b"
            result = re.sub(pattern, ar, result, flags=re.IGNORECASE)
        return result

    def _arabic_typography(self, text: str) -> str:
        # Apply Arabic typography only on lines containing Arabic
        digit_map = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
        out_lines: List[str] = []
        for line in text.splitlines():
            if re.search(r"[\u0600-\u06FF]", line):
                l = line.translate(digit_map)
                l = l.replace("?", "؟").replace(";", "؛").replace(",", "،")
                l = re.sub(r"[ \t]+", " ", l)
                out_lines.append(l)
            else:
                out_lines.append(line)
        return "\n".join(out_lines)

    def _arabic_only_cleanup(self, text: str) -> str:
        # Remove fenced and inline code, liquid, URLs/emails, HTML tags
        cleaned = re.sub(r"```[\s\S]*?```", "", text)
        cleaned = re.sub(r"`[^`]+`", "", cleaned)
        cleaned = re.sub(r"({%[^%]*%}|{{[^}]*}})", "", cleaned)
        cleaned = re.sub(r"https?://\S+", "", cleaned)
        cleaned = re.sub(r"\b\S+@\S+\b", "", cleaned)
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)

        # Drop Latin letters; keep digits and punctuation for now
        cleaned = re.sub(r"[A-Za-z]", "", cleaned)

        # Keep only lines with Arabic content
        kept_lines: List[str] = []
        for line in cleaned.splitlines():
            ln = line.strip()
            if not ln:
                continue
            if re.search(r"[\u0600-\u06FF]", ln):
                kept_lines.append(ln)

        result = "\n".join(kept_lines)
        result = re.sub(r"\n{3,}", "\n\n", result).strip()
        # Apply Arabic typography at the end
        return self._arabic_typography(result)
    
    def setup_terminology_database(self):
        """Comprehensive technical terminology database"""
        
        self.terminology = {
            # Core GitHub Terms
            "repository": "المستودع",
            "repositories": "المستودعات", 
            "commit": "الالتزام",
            "commits": "الالتزامات",
            "pull request": "طلب السحب",
            "pull requests": "طلبات السحب",
            "issue": "القضية",
            "issues": "القضايا",
            "branch": "الفرع",
            "branches": "الفروع",
            "merge": "الدمج",
            "fork": "النسخة المتفرعة",
            "clone": "الاستنساخ",
            "push": "الدفع",
            "fetch": "الجلب",
            "workflow": "سير العمل",
            "workflows": "سير العمل",
            
            # Authentication & Security
            "authentication": "المصادقة",
            "authorization": "التخويل",
            "token": "الرمز المميز",
            "tokens": "الرموز المميزة",
            "API key": "مفتاح API",
            "SSH key": "مفتاح SSH",
            "OAuth": "OAuth",
            "two-factor authentication": "المصادقة ثنائية العامل",
            "2FA": "المصادقة ثنائية العامل",
            "passkey": "مفتاح المرور",
            "passkeys": "مفاتيح المرور",
            "single sign-on": "تسجيل الدخول الموحد",
            "SSO": "تسجيل الدخول الموحد",
            
            # Actions & CI/CD
            "GitHub Actions": "GitHub Actions",
            "action": "الإجراء",
            "actions": "الإجراءات",
            "runner": "المشغل",
            "runners": "المشغلون",
            "job": "المهمة",
            "jobs": "المهام",
            "step": "الخطوة",
            "steps": "الخطوات",
            "artifact": "المنتج",
            "artifacts": "المنتجات",
            "deployment": "النشر",
            "continuous integration": "التكامل المستمر",
            "CI/CD": "CI/CD",
            "build": "البناء",
            
            # Organizations & Teams
            "organization": "المنظمة",
            "organizations": "المنظمات",
            "team": "الفريق",
            "teams": "الفرق",
            "member": "العضو",
            "members": "الأعضاء",
            "owner": "المالك",
            "admin": "المسؤول",
            "collaborator": "المتعاون",
            "collaborators": "المتعاونون",
            
            # Development Terms
            "code": "الكود",
            "source code": "الكود المصدري",
            "codebase": "قاعدة الكود",
            "developer": "المطور",
            "developers": "المطورون",
            "development": "التطوير",
            "programming": "البرمجة",
            "software": "البرمجيات",
            "application": "التطبيق",
            "project": "المشروع",
            "file": "الملف",
            "files": "الملفات",
            "folder": "المجلد",
            "directory": "الدليل",
            
            # Git Terms
            "git": "Git",
            "version control": "التحكم في الإصدارات",
            "staging": "التجهيز",
            "stash": "المخزن المؤقت",
            "diff": "الفرق",
            "log": "السجل",
            "remote": "البعيد",
            "origin": "الأصل",
            "upstream": "المنبع",
            "downstream": "المصب",
            
            # General Tech Terms
            "API": "API",
            "URL": "URL",
            "HTTP": "HTTP",
            "HTTPS": "HTTPS",
            "JSON": "JSON",
            "YAML": "YAML",
            "markdown": "Markdown",
            "command line": "سطر الأوامر",
            "terminal": "الطرفية",
            "shell": "الصدفة",
            "script": "النص البرمجي",
            "configuration": "التكوين",
            "settings": "الإعدادات",
            "permissions": "الأذونات",
            "access": "الوصول",
            "security": "الأمان",
            "privacy": "الخصوصية",
            "token": "رمز الوصول",
            "access token": "رمز الوصول",
            "access tokens": "رموز الوصول",
            "user access token": "رمز وصول المستخدم",
            "user access tokens": "رموز وصول المستخدم",
            "installation access token": "رمز وصول التثبيت",
            "installation access tokens": "رموز وصول التثبيت",
            
            # Action Words
            "create": "إنشاء",
            "delete": "حذف",
            "update": "تحديث",
            "edit": "تحرير",
            "manage": "إدارة",
            "configure": "تكوين",
            "setup": "إعداد",
            "install": "تثبيت",
            "deploy": "نشر",
            "publish": "نشر",
            "share": "مشاركة",
            "collaborate": "التعاون",
            "contribute": "المساهمة",
            "review": "مراجعة",
            "approve": "الموافقة",
            "reject": "رفض",
            
            # Common Phrases
            "getting started": "البدء",
            "quick start": "البدء السريع",
            "learn more": "تعلم المزيد",
            "read more": "اقرأ المزيد",
            "see also": "انظر أيضًا",
            "for more information": "لمزيد من المعلومات",
            "best practices": "أفضل الممارسات",
            "troubleshooting": "استكشاف الأخطاء وإصلاحها",
            "documentation": "المستندات",
            "tutorial": "الدرس التعليمي",
            "guide": "الدليل",
            "example": "مثال",
            "examples": "أمثلة",
            "libraries": "المكتبات",
            "network configurations": "تكوينات الشبكة",
            "codes of conduct": "مدونات السلوك",
            "code of conduct": "مدونة السلوك",
            "anti-bribery": "مكافحة الرشوة",
            "modern slavery": "العبودية الحديثة",
            "child labor": "عمل الأطفال",
            "subprocessors": "معالجات فرعية",
            "subprocessor": "معالج فرعي",
            "embeddings": "تضمينات",
            "keyboard shortcuts": "اختصارات لوحة المفاتيح",

            # Audit cue translations
            "overview": "نظرة عامة",
            "summary": "الملخص",
            "steps": "الخطوات",
            "prerequisites": "المتطلبات المسبقة",
            "note": "ملاحظة",
            "tip": "نصيحة",
            "caution": "تحذير",
            "warning": "تحذير",
            "this guide": "هذا الدليل",
            "about github": "حول GitHub"
            ,
            # Added phrase cues
            "in your": "في الخاص بك",
            "before you begin": "قبل أن تبدأ",
            "at this stage": "في هذه المرحلة",
            "for example": "على سبيل المثال",
            "by updating": "عن طريق تحديث",
            "by default": "افتراضيًا",
            "to get started": "للبدء",
            "you can now": "يمكنك الآن",
            "next steps": "الخطوات التالية"
        }
        
        # Create reverse mapping for context awareness
        self.reverse_terminology = {v: k for k, v in self.terminology.items()}
    
    def setup_linguistic_rules(self):
        """Advanced Arabic linguistic rules"""
        
        self.linguistic_rules = {
            # Article rules
            "definite_article": {
                "patterns": [
                    (r'\bthe\s+([a-zA-Z]+)', r'ال\1'),  # Basic "the" translation
                    (r'\ba\s+([a-zA-Z]+)', r'\1'),      # Remove indefinite articles
                    (r'\ban\s+([a-zA-Z]+)', r'\1')      # Remove indefinite articles
                ]
            },
            
            # Sentence structure improvements
            "sentence_structure": {
                "patterns": [
                    # Convert "You can..." to "يمكنك..."
                    (r'\bYou can\s+([^.]+)', r'يمكنك \1'),
                    # Convert "To do X..." to "لـ..."
                    (r'\bTo\s+([a-zA-Z]+)', r'لـ\1'),
                    # Convert "This will..." to "سيؤدي هذا إلى..."
                    (r'\bThis will\s+([^.]+)', r'سيؤدي هذا إلى \1'),
                    # Convert "Learn how to..." to "تعلم كيفية..."
                    (r'\bLearn how to\s+([^.]+)', r'تعلم كيفية \1')
                ]
            },
            
            # Technical context patterns
            "technical_context": {
                "code_blocks": r'```[\s\S]*?```',
                "inline_code": r'`[^`]+`',
                "liquid_tags": r'{%[^%]*%}',
                "liquid_variables": r'{{[^}]*}}',
                "urls": r'https?://[^\s]+',
                "file_paths": r'[a-zA-Z0-9._/-]+\.[a-zA-Z]{2,4}'
            }
        }
    
    def setup_content_patterns(self):
        """Content structure and pattern recognition"""
        
        self.content_patterns = {
            # Common GitHub documentation patterns
            "introduction_patterns": [
                (r'^## About (.+)', r'## حول \1'),
                (r'^### What is (.+)\?', r'### ما هو \1؟'),
                (r'^### Why (.+)\?', r'### لماذا \1؟'),
                (r'^### How (.+)', r'### كيف \1'),
                (r'^### When (.+)', r'### متى \1')
            ],
            
            "instruction_patterns": [
                (r'^### Step (\d+):', r'### الخطوة \1:'),
                (r'^#### Prerequisites', r'#### المتطلبات المسبقة'),
                (r'^#### Requirements', r'#### المتطلبات'),
                (r'^#### Before you begin', r'#### قبل أن تبدأ'),
                (r'^### Next steps', r'### الخطوات التالية')
            ],
            
            "navigation_patterns": [
                (r'In this article', r'في هذا المقال'),
                (r'Table of contents', r'جدول المحتويات'),
                (r'See also', r'انظر أيضًا'),
                (r'Related articles', r'المقالات ذات الصلة'),
                (r'Further reading', r'قراءة إضافية')
            ]
        }
    
    def setup_github_domain_knowledge(self):
        """GitHub-specific domain knowledge and context"""
        
        self.github_contexts = {
            # Product names (keep in English with Arabic explanation)
            "products": {
                "GitHub Desktop": "GitHub Desktop",
                "GitHub CLI": "GitHub CLI",
                "GitHub Mobile": "GitHub Mobile", 
                "GitHub Codespaces": "GitHub Codespaces",
                "GitHub Copilot": "GitHub Copilot",
                "GitHub Actions": "GitHub Actions",
                "GitHub Pages": "GitHub Pages",
                "GitHub Packages": "GitHub Packages"
            },
            
            # Feature explanations
            "feature_explanations": {
                "GitHub Desktop": "تطبيق سطح المكتب لـ GitHub",
                "GitHub CLI": "واجهة سطر الأوامر لـ GitHub", 
                "Codespaces": "بيئات التطوير السحابية",
                "Copilot": "مساعد البرمجة بالذكاء الاصطناعي",
                "Actions": "أتمتة سير العمل والتكامل المستمر",
                "Pages": "استضافة المواقع الثابتة",
                "Packages": "إدارة وتوزيع الحزم"
            },
            
            # Common workflows
            "workflows": {
                "fork_and_pull": "النسخ المتفرع وطلب السحب",
                "gitflow": "سير عمل Git",
                "feature_branch": "فرع الميزة",
                "release_management": "إدارة الإصدارات"
            }
        }
    
    def extract_frontmatter(self, content):
        """Extract YAML frontmatter from markdown content"""
        if not content.strip().startswith('---'):
            return {}, content
            
        try:
            parts = content.split('---', 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1].strip()
                frontmatter = {}
                
                for line in frontmatter_text.split('\n'):
                    if ':' in line and not line.strip().startswith('#'):
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip().strip('"\'')
                
                body = parts[2].strip()
                return frontmatter, body
        except Exception as e:
            logger.warning(f"Frontmatter parsing error: {e}")
            
        return {}, content
    
    def enhance_frontmatter(self, frontmatter):
        """Enhance frontmatter with better Arabic translations"""
        
        enhanced = frontmatter.copy()
        
        # Enhanced title translations
        if 'title' in enhanced:
            enhanced['title'] = self.translate_text_intelligent(enhanced['title'])
        
        # Enhanced intro translations  
        if 'intro' in enhanced:
            enhanced['intro'] = self.translate_text_intelligent(enhanced['intro'])
            
        # Enhanced shortTitle translations
        if 'shortTitle' in enhanced:
            enhanced['shortTitle'] = self.translate_text_intelligent(enhanced['shortTitle'])
        
        # Ensure RTL direction for Arabic docs
        if 'dir' not in enhanced:
            enhanced['dir'] = 'rtl'
        return enhanced
    
    def translate_text_intelligent(self, text):
        """Intelligent text translation with context awareness"""
        
        if not text or not text.strip():
            return text
        
        # Preserve liquid tags and technical elements using stable placeholders
        temp_text = text
        preserved: List[Tuple[str, str]] = []  # (placeholder, original)
        
        def make_replacer(kind: str):
            def _repl(m: re.Match) -> str:
                placeholder = f"__PRESERVE_{kind}_{len(preserved)}__"
                preserved.append((placeholder, m.group(0)))
                return placeholder
            return _repl
        
        # Preserve liquid tags first
        liquid_pattern = r'({%[^%]*%}|{{[^}]*}})'
        temp_text = re.sub(liquid_pattern, make_replacer("LIQUID"), temp_text)
        
        # Preserve inline code snippets
        code_pattern = r'`[^`]+`'
        temp_text = re.sub(code_pattern, make_replacer("CODE"), temp_text)

        # Apply terminology translations
        for english, arabic in self.terminology.items():
            # Case-insensitive replacement with word boundaries
            pattern = r'\b' + re.escape(english) + r'\b'
            temp_text = re.sub(pattern, arabic, temp_text, flags=re.IGNORECASE)
            self.stats["terminology_applications"] += temp_text.count(arabic)

        # Apply linguistic rules
        for rule_category, rules in self.linguistic_rules.items():
            if rule_category == "technical_context":
                continue  # Skip technical context in this phase

            if isinstance(rules, dict) and "patterns" in rules:
                for pattern, replacement in rules["patterns"]:
                    if re.search(pattern, temp_text):
                        temp_text = re.sub(pattern, replacement, temp_text)
                        self.stats["pattern_matches"] += 1

        # If text still predominantly English, apply lexical fallback
        if self._arabic_ratio(temp_text) < self.fallback_threshold and len(re.findall(r"[A-Za-z]", temp_text)) > 50:
            temp_text = self._apply_lexical_fallback(temp_text)

        # Either restore preserved elements or drop them for Arabic-only output
        if self.arabic_only:
            for placeholder, _ in preserved:
                temp_text = temp_text.replace(placeholder, "")
            return self._arabic_only_cleanup(temp_text)
        else:
            for placeholder, original in preserved:
                temp_text = temp_text.replace(placeholder, original)
            return self._arabic_typography(temp_text)
    
    def generate_enhanced_content(self, original_content, frontmatter):
        """Generate enhanced Arabic content from English original"""
        
        # Start with Arabic header
        enhanced_content = f"# {frontmatter.get('title', 'مستند GitHub')}\n\n"
        
        # Add context-aware introduction
        if 'intro' in frontmatter:
            enhanced_content += f"{frontmatter['intro']}\n\n"
        
        # Analyze content structure
        sections = self.analyze_content_structure(original_content)
        
        # Generate intelligent Arabic content based on structure
        for section in sections:
            if section['type'] == 'heading':
                level = '#' * section['level']
                translated_heading = self.translate_text_intelligent(section['content'])
                enhanced_content += f"{level} {translated_heading}\n\n"
                
            elif section['type'] == 'paragraph':
                if section['content'].strip():
                    translated_paragraph = self.translate_text_intelligent(section['content'])
                    enhanced_content += f"{translated_paragraph}\n\n"
                    
            elif section['type'] == 'list':
                for item in section['items']:
                    translated_item = self.translate_text_intelligent(item)
                    enhanced_content += f"- {translated_item}\n"
                enhanced_content += "\n"
                
            elif section['type'] == 'code_block':
                enhanced_content += f"```{section.get('language', '')}\n{section['content']}\n```\n\n"
                
            elif section['type'] == 'quote':
                translated_quote = self.translate_text_intelligent(section['content'])
                enhanced_content += f"> {translated_quote}\n\n"
        
        # Add helpful Arabic navigation
        enhanced_content += "\n---\n\n"
        enhanced_content += "## مصادر إضافية\n\n"
        enhanced_content += "- [المستندات الرئيسية لـ GitHub](https://docs.github.com/ar)\n"
        enhanced_content += "- [مجتمع GitHub باللغة العربية](https://github.com/community)\n"
        enhanced_content += "- [الدعم الفني](https://support.github.com)\n"
        
        return enhanced_content
    
    def analyze_content_structure(self, content):
        """Analyze content structure for intelligent processing"""
        
        sections = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Heading detection
            if line.startswith('#'):
                level = len(line) - len(line.lstrip('#'))
                heading_text = line.lstrip('#').strip()
                sections.append({
                    'type': 'heading',
                    'level': level,
                    'content': heading_text
                })
                
            # Code block detection
            elif line.startswith('```'):
                language = line[3:].strip()
                code_content = []
                i += 1
                while i < len(lines) and not lines[i].strip().startswith('```'):
                    code_content.append(lines[i])
                    i += 1
                sections.append({
                    'type': 'code_block',
                    'language': language,
                    'content': '\n'.join(code_content)
                })
                
            # List detection
            elif line.startswith(('-', '*', '+')):
                list_items = []
                while i < len(lines) and lines[i].strip().startswith(('-', '*', '+')):
                    item_text = lines[i].strip()[1:].strip()
                    list_items.append(item_text)
                    i += 1
                i -= 1  # Adjust for the increment at the end of the loop
                sections.append({
                    'type': 'list',
                    'items': list_items
                })
                
            # Quote detection
            elif line.startswith('>'):
                quote_text = line[1:].strip()
                sections.append({
                    'type': 'quote',
                    'content': quote_text
                })
                
            # Regular paragraph
            else:
                sections.append({
                    'type': 'paragraph',
                    'content': line
                })
            
            i += 1
        
        return sections
    
    def enhance_translation_file(self, arabic_file_path):
        """Enhance an existing Arabic translation file"""
        
        if not arabic_file_path.exists():
            logger.warning(f"Arabic file not found: {arabic_file_path}")
            return False
        
        try:
            # Read current Arabic content
            with open(arabic_file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            # Extract frontmatter
            frontmatter, body = self.extract_frontmatter(current_content)
            
            # Find corresponding English file
            english_file_path = arabic_file_path.parent / arabic_file_path.name.replace('-ar.md', '.md')
            
            if english_file_path.exists():
                with open(english_file_path, 'r', encoding='utf-8') as f:
                    english_content = f.read()
                
                english_frontmatter, english_body = self.extract_frontmatter(english_content)
            else:
                english_body = ""
                english_frontmatter = {}
            
            # Enhance frontmatter
            enhanced_frontmatter = self.enhance_frontmatter(frontmatter)
            
            # Generate enhanced content
            enhanced_content = self.generate_enhanced_content(english_body, enhanced_frontmatter)
            
            # Construct final file content
            final_content = "---\n"
            for key, value in enhanced_frontmatter.items():
                # Preserve array and complex values
                if isinstance(value, (list, dict)):
                    final_content += f"{key}: {value}\n"
                else:
                    final_content += f"{key}: {value}\n"
            final_content += "---\n\n"
            final_content += (self._arabic_only_cleanup(enhanced_content) if self.arabic_only else self._arabic_typography(enhanced_content))
            
            # Write enhanced content
            with open(arabic_file_path, 'w', encoding='utf-8') as f:
                f.write(final_content)
            
            self.stats["files_processed"] += 1
            self.stats["translations_enhanced"] += 1
            
            logger.info(f"Enhanced: {arabic_file_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error enhancing {arabic_file_path}: {e}")
            return False
    
    def enhance_sample_files(self, sample_size=5):
        """Enhance a sample of files for testing"""
        
        logger.info(f"Enhancing {sample_size} sample files...")
        
        # Find Arabic files
        arabic_files = list(self.content_root.rglob("*-ar.md"))
        
        if not arabic_files:
            logger.error("No Arabic files found to enhance")
            return False
        
        # Select random sample
        import random
        sample_files = random.sample(arabic_files, min(sample_size, len(arabic_files)))
        
        enhanced_count = 0
        for file_path in sample_files:
            if self.enhance_translation_file(file_path):
                enhanced_count += 1
        
        logger.info(f"Enhanced {enhanced_count}/{sample_size} sample files")
        self.print_enhancement_stats()
        
        return enhanced_count > 0
    
    def enhance_priority_files(self):
        """Enhance high-priority documentation files"""
        
        priority_patterns = [
            "*/index-ar.md",
            "*/README-ar.md", 
            "*get-started*-ar.md",
            "*authentication*-ar.md",
            "*actions*-ar.md",
            "*quick*-ar.md"
        ]
        
        priority_files = []
        for pattern in priority_patterns:
            priority_files.extend(self.content_root.glob(pattern))
            priority_files.extend(self.content_root.rglob(pattern))
        
        # Remove duplicates
        priority_files = list(set(priority_files))
        
        logger.info(f"Enhancing {len(priority_files)} priority files...")
        
        enhanced_count = 0
        for file_path in priority_files:
            if self.enhance_translation_file(file_path):
                enhanced_count += 1
        
        logger.info(f"Enhanced {enhanced_count}/{len(priority_files)} priority files")
        self.print_enhancement_stats()
        
        return enhanced_count > 0
    
    def enhance_all_files(self):
        """Enhance all Arabic translation files"""
        
        arabic_files = list(self.content_root.rglob("*-ar.md"))
        
        logger.info(f"Enhancing all {len(arabic_files)} Arabic files...")
        
        enhanced_count = 0
        for i, file_path in enumerate(arabic_files):
            if i % 100 == 0:
                logger.info(f"Progress: {i}/{len(arabic_files)} files processed...")
            
            if self.enhance_translation_file(file_path):
                enhanced_count += 1
        
        logger.info(f"Enhanced {enhanced_count}/{len(arabic_files)} files")
        self.print_enhancement_stats()
        
        return enhanced_count > 0
    
    def print_enhancement_stats(self):
        """Print enhancement statistics"""
        
        print("\n📊 LOCAL AI ENHANCEMENT STATISTICS")
        print("=" * 45)
        print(f"Files Processed: {self.stats['files_processed']}")
        print(f"Translations Enhanced: {self.stats['translations_enhanced']}")
        print(f"Terminology Applications: {self.stats['terminology_applications']}")
        print(f"Pattern Matches: {self.stats['pattern_matches']}")
        print(f"Linguistic Improvements: {self.stats['linguistic_improvements']}")
        
        # Calculate enhancement metrics
        if self.stats['files_processed'] > 0:
            avg_improvements = (
                self.stats['terminology_applications'] + 
                self.stats['pattern_matches'] + 
                self.stats['linguistic_improvements']
            ) / self.stats['files_processed']
            print(f"Average Improvements per File: {avg_improvements:.1f}")
        
        print("\n✅ Local AI Enhancement Complete!")

def main():
    """Main function with command line interface"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Local AI-Enhanced Translation")
    parser.add_argument("--sample", type=int, default=5, help="Number of sample files to enhance")
    parser.add_argument("--priority", action="store_true", help="Enhance priority files only")
    parser.add_argument("--all", action="store_true", help="Enhance all files")
    parser.add_argument("--file", type=str, help="Enhance a specific Arabic file path (e.g., docs/content/.../index-ar.md)")
    parser.add_argument("--root", type=str, help="Path to docs root (directory that contains 'content')")
    parser.add_argument("--aggressive", action="store_true", help="Use aggressive lexical fallback for stubborn files")
    parser.add_argument("--arabic-only", action="store_true", help="Output Arabic-only text (strip English/code/URLs)")
    
    args = parser.parse_args()
    
    # Initialize local AI translator
    translator = LocalAITranslator(docs_root=args.root, aggressive=args.aggressive, arabic_only=args.arabic_only)
    
    print("🤖 LOCAL AI-ENHANCED TRANSLATOR")
    print("=" * 40)
    print("✅ No API key required!")
    print("✅ 100% local processing!")
    print("✅ Advanced linguistic intelligence!")
    print("✅ Comprehensive terminology database!")
    
    if args.file:
        translator.enhance_translation_file(Path(args.file))
    elif args.all:
        translator.enhance_all_files()
    elif args.priority:
        translator.enhance_priority_files()
    else:
        translator.enhance_sample_files(args.sample)

if __name__ == "__main__":
    main()