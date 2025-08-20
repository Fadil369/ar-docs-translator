#!/usr/bin/env python3
"""
GitHub Docs Advanced Translation Manager

A comprehensive tool for managing Arabic translations of GitHub documentation.
Combines analysis, basic translations, and AI-powered enhancements.

Features:
- Complete translation status analysis
- Creates basic placeholder translations
- Optional AI-powered translation improvements
- Progress tracking and reporting
- Batch processing capabilities

Usage:
    python3 advanced_translator.py                     # Full analysis and basic translation
    python3 advanced_translator.py --ai-enhance        # Use AI for quality translations
    python3 advanced_translator.py --priority-only     # Focus on high-priority files only
    python3 advanced_translator.py --report-only       # Generate reports without translation
"""

import os
import sys
import json
import argparse
import logging
import re
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Set, Optional

# Optional AI dependencies
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import frontmatter
    HAS_FRONTMATTER = True
except ImportError:
    HAS_FRONTMATTER = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_translation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AdvancedTranslationManager:
    """Advanced translation manager with analysis and AI capabilities"""
    
    def __init__(self, 
                 docs_root: str = "docs",
                 target_lang: str = "ar", 
                 ai_enhance: bool = False,
                 priority_only: bool = False,
                 report_only: bool = False):
        
        self.docs_root = Path(docs_root)
        self.content_root = self.docs_root / "content"
        self.target_lang = target_lang
        self.lang_suffix = f"-{target_lang}"
        self.ai_enhance = ai_enhance
        self.priority_only = priority_only
        self.report_only = report_only
        
        # Translation data
        self.english_files = []
        self.arabic_files = []
        self.missing_translations = []
        self.existing_translations = []
        self.priority_files = []
        
        # Statistics
        self.stats = {
            "analysis_start_time": None,
            "analysis_end_time": None,
            "translation_start_time": None,
            "translation_end_time": None,
            "total_english_files": 0,
            "total_arabic_files": 0,
            "missing_count": 0,
            "created_count": 0,
            "enhanced_count": 0,
            "error_count": 0,
            "coverage_percent": 0.0
        }
        
        # Configuration
        self.priority_patterns = [
            r"index\.md$",
            r"README\.md$",
            r"^get-started/.*",
            r"^authentication/.*",
            r"^account-and-profile/.*",
            r"^actions/.*quickstart.*",
            r"^actions/.*get-started.*",
            r"^issues/.*",
            r"^pull-requests/.*",
            r"^repositories/.*",
            r"^copilot/.*",
            r"^support/.*"
        ]
        
        self.skip_patterns = [
            r"\.git.*",
            r"\.DS_Store",
            r".*\.tmp",
            r".*\.log",
            r"node_modules",
            r"\.next",
            r"__pycache__",
            r".*test.*\.md$",
            r".*spec.*\.md$"
        ]
        
        # AI setup
        self.openai_client = None
        if ai_enhance and HAS_OPENAI:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized for AI enhancements")
            else:
                logger.warning("OPENAI_API_KEY not found - AI enhancements disabled")
                self.ai_enhance = False
        elif ai_enhance:
            logger.warning("OpenAI not available - AI enhancements disabled")
            self.ai_enhance = False
        
        # Arabic translations dictionary
        self.arabic_translations = {
            # Common GitHub terms
            "Repository": "المستودع",
            "Pull Request": "طلب السحب", 
            "Issue": "القضية",
            "Commit": "الالتزام",
            "Branch": "الفرع",
            "Merge": "الدمج",
            "Fork": "النسخة المتفرعة",
            "Clone": "النسخ",
            "Push": "الدفع",
            "Pull": "السحب",
            
            # Navigation and UI
            "Getting started": "البدء",
            "Quick start": "البدء السريع",
            "Authentication": "المصادقة",
            "Account and profile": "الحساب والملف الشخصي",
            "Actions": "الإجراءات",
            "Issues": "القضايا",
            "Pull requests": "طلبات السحب",
            "Repositories": "المستودعات",
            "Support": "الدعم",
            "About": "حول",
            "Overview": "نظرة عامة",
            "Guide": "دليل",
            "Tutorial": "البرنامج التعليمي",
            "Reference": "المرجع",
            "Documentation": "المستندات",
            
            # Actions and processes
            "Learn": "تعلم",
            "Understand": "افهم",
            "Get started": "ابدأ",
            "Configure": "اضبط",
            "Manage": "أدر",
            "Create": "أنشئ",
            "how to": "كيفية",
            "with": "مع",
            "for": "لـ",
            "and": "و",
            "or": "أو",
            "in": "في",
            "on": "على",
            "to": "إلى"
        }
    
    def should_skip_file(self, file_path: Path) -> bool:
        """Check if file should be skipped"""
        file_str = str(file_path)
        return any(re.search(pattern, file_str, re.IGNORECASE) for pattern in self.skip_patterns)
    
    def is_priority_file(self, file_path: Path) -> bool:
        """Check if file is high priority"""
        rel_path = str(file_path.relative_to(self.content_root))
        return any(re.search(pattern, rel_path, re.IGNORECASE) for pattern in self.priority_patterns)
    
    def get_arabic_file_path(self, english_file: Path) -> Path:
        """Get corresponding Arabic file path"""
        arabic_name = f"{english_file.stem}{self.lang_suffix}.md"
        return english_file.parent / arabic_name
    
    def analyze_translations(self) -> Dict:
        """Complete translation analysis"""
        logger.info("Starting comprehensive translation analysis...")
        self.stats["analysis_start_time"] = datetime.now()
        
        if not self.content_root.exists():
            raise FileNotFoundError(f"Content directory not found: {self.content_root}")
        
        # Find all files
        logger.info("Scanning content directory...")
        for file_path in self.content_root.rglob("*.md"):
            if self.should_skip_file(file_path):
                continue
            
            if self.lang_suffix in file_path.name:
                self.arabic_files.append(file_path)
            else:
                self.english_files.append(file_path)
                if self.is_priority_file(file_path):
                    self.priority_files.append(file_path)
        
        # Analyze translation status
        arabic_names = {f.name for f in self.arabic_files}
        
        for english_file in self.english_files:
            expected_arabic_name = f"{english_file.stem}{self.lang_suffix}.md"
            
            if expected_arabic_name in arabic_names:
                self.existing_translations.append(english_file)
            else:
                self.missing_translations.append(english_file)
        
        # Calculate statistics
        self.stats["total_english_files"] = len(self.english_files)
        self.stats["total_arabic_files"] = len(self.arabic_files)
        self.stats["missing_count"] = len(self.missing_translations)
        
        if self.stats["total_english_files"] > 0:
            coverage = len(self.existing_translations) / self.stats["total_english_files"] * 100
            self.stats["coverage_percent"] = coverage
        
        self.stats["analysis_end_time"] = datetime.now()
        analysis_time = (self.stats["analysis_end_time"] - self.stats["analysis_start_time"]).total_seconds()
        
        logger.info(f"Analysis completed in {analysis_time:.1f} seconds")
        logger.info(f"Found {len(self.english_files)} English files")
        logger.info(f"Found {len(self.arabic_files)} existing Arabic files")
        logger.info(f"Missing translations: {len(self.missing_translations)}")
        logger.info(f"Priority files needing translation: {len([f for f in self.missing_translations if self.is_priority_file(f)])}")
        
        return {
            "english_files": len(self.english_files),
            "arabic_files": len(self.arabic_files),
            "missing_translations": len(self.missing_translations),
            "priority_missing": len([f for f in self.missing_translations if self.is_priority_file(f)]),
            "coverage_percent": self.stats["coverage_percent"]
        }
    
    def extract_frontmatter(self, content: str) -> tuple:
        """Extract frontmatter from markdown content"""
        if HAS_FRONTMATTER:
            try:
                post = frontmatter.loads(content)
                return post.metadata, post.content
            except Exception as e:
                logger.warning(f"Frontmatter parsing error: {e}")
        
        # Fallback parsing
        lines = content.split('\n')
        if not lines or lines[0].strip() != '---':
            return {}, content
        
        fm_end = None
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                fm_end = i
                break
        
        if fm_end is None:
            return {}, content
        
        # Basic YAML parsing
        frontmatter_dict = {}
        for line in lines[1:fm_end]:
            if ':' in line and not line.strip().startswith('#'):
                try:
                    key, value = line.split(':', 1)
                    frontmatter_dict[key.strip()] = value.strip().strip('"\'')
                except ValueError:
                    continue
        
        content_body = '\n'.join(lines[fm_end + 1:])
        return frontmatter_dict, content_body
    
    def translate_text_basic(self, text: str) -> str:
        """Basic translation using dictionary"""
        translated = text
        for english, arabic in self.arabic_translations.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(english) + r'\b'
            translated = re.sub(pattern, arabic, translated, flags=re.IGNORECASE)
        return translated
    
    def translate_text_ai(self, text: str, context: str = "") -> str:
        """AI-powered translation using OpenAI"""
        if not self.openai_client:
            return self.translate_text_basic(text)
        
        try:
            prompt = f"""Translate the following GitHub documentation text from English to Arabic.

IMPORTANT GUIDELINES:
1. Preserve ALL markdown formatting (headers, links, lists, tables, code blocks)
2. Do NOT translate content inside liquid tags like {{% data variables.* %}}, {{% ifversion %}}, etc.
3. Do NOT translate code blocks, file paths, URLs, or technical identifiers
4. Keep all HTML tags and special formatting exactly as they are
5. Use Modern Standard Arabic that is clear and professional
6. Maintain the same paragraph structure and spacing
7. For GitHub-specific terms, use these translations:
   - Repository: المستودع
   - Pull Request: طلب السحب
   - Issue: القضية
   - Commit: الالتزام
   - Branch: الفرع
   - Merge: الدمج

Context: {context}

Text to translate:
{text}

Arabic translation:"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Arabic translator specializing in technical documentation for software development. Translate accurately while preserving all formatting."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=4000
            )
            
            translation = response.choices[0].message.content.strip()
            return translation
            
        except Exception as e:
            logger.error(f"AI translation error: {e}")
            return self.translate_text_basic(text)
    
    def create_arabic_content(self, english_file: Path) -> str:
        """Create Arabic content from English file"""
        try:
            with open(english_file, 'r', encoding='utf-8') as f:
                english_content = f.read()
            
            frontmatter, content = self.extract_frontmatter(english_content)
            
            # Translate frontmatter
            arabic_fm = frontmatter.copy()
            translatable_fields = ['title', 'shortTitle', 'intro', 'permissions']
            
            for field in translatable_fields:
                if field in arabic_fm and arabic_fm[field]:
                    if self.ai_enhance:
                        arabic_fm[field] = self.translate_text_ai(
                            arabic_fm[field], 
                            f"frontmatter {field} for {english_file.name}"
                        )
                    else:
                        arabic_fm[field] = self.translate_text_basic(arabic_fm[field])
            
            # Create Arabic content
            if self.ai_enhance and content.strip():
                # AI translation for full content
                arabic_content = self.translate_text_ai(
                    content,
                    f"GitHub documentation file: {english_file.relative_to(self.content_root)}"
                )
            else:
                # Basic placeholder with note
                arabic_content = f"""# {arabic_fm.get('title', 'صفحة غير مترجمة')}

> **ملاحظة**: هذه الصفحة تحتاج إلى ترجمة كاملة. المحتوى أدناه باللغة الإنجليزية.

---

{content}"""
            
            # Reconstruct file
            result_lines = ["---"]
            for key, value in arabic_fm.items():
                if isinstance(value, str) and any(char in value for char in '"\''):
                    value = json.dumps(value)
                result_lines.append(f"{key}: {value}")
            result_lines.append("---")
            result_lines.append("")
            result_lines.append(arabic_content)
            
            return '\n'.join(result_lines)
            
        except Exception as e:
            logger.error(f"Error creating Arabic content for {english_file}: {e}")
            self.stats["error_count"] += 1
            return None
    
    def create_translations(self) -> None:
        """Create missing Arabic translations"""
        if self.report_only:
            logger.info("Report-only mode: skipping translation creation")
            return
        
        # Determine which files to translate
        files_to_translate = []
        if self.priority_only:
            files_to_translate = [f for f in self.missing_translations if self.is_priority_file(f)]
            logger.info(f"Priority-only mode: translating {len(files_to_translate)} priority files")
        else:
            files_to_translate = self.missing_translations
            logger.info(f"Translating all {len(files_to_translate)} missing files")
        
        if not files_to_translate:
            logger.info("No files to translate")
            return
        
        self.stats["translation_start_time"] = datetime.now()
        
        # Sort by priority and size
        files_to_translate.sort(key=lambda f: (not self.is_priority_file(f), f.stat().st_size))
        
        created_count = 0
        enhanced_count = 0
        
        logger.info(f"Starting translation of {len(files_to_translate)} files...")
        
        for i, english_file in enumerate(files_to_translate, 1):
            try:
                arabic_file = self.get_arabic_file_path(english_file)
                
                # Skip if already exists
                if arabic_file.exists():
                    continue
                
                # Create Arabic content
                arabic_content = self.create_arabic_content(english_file)
                if arabic_content is None:
                    continue
                
                # Ensure directory exists
                arabic_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Write file
                with open(arabic_file, 'w', encoding='utf-8') as f:
                    f.write(arabic_content)
                
                created_count += 1
                if self.ai_enhance:
                    enhanced_count += 1
                
                rel_path = english_file.relative_to(self.content_root)
                priority_mark = " [PRIORITY]" if self.is_priority_file(english_file) else ""
                ai_mark = " [AI]" if self.ai_enhance else ""
                
                if i % 100 == 0 or self.is_priority_file(english_file):
                    logger.info(f"[{i}/{len(files_to_translate)}] Created: {rel_path}{priority_mark}{ai_mark}")
                
                # Rate limiting for AI
                if self.ai_enhance and self.openai_client:
                    time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error translating {english_file}: {e}")
                self.stats["error_count"] += 1
        
        self.stats["created_count"] = created_count
        self.stats["enhanced_count"] = enhanced_count
        self.stats["translation_end_time"] = datetime.now()
        
        translation_time = (self.stats["translation_end_time"] - self.stats["translation_start_time"]).total_seconds()
        
        logger.info(f"Translation completed in {translation_time:.1f} seconds")
        logger.info(f"Successfully created {created_count} translation files")
        if self.ai_enhance:
            logger.info(f"AI-enhanced translations: {enhanced_count}")
    
    def generate_comprehensive_report(self) -> str:
        """Generate detailed analysis report"""
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("GITHUB DOCS ARABIC TRANSLATION COMPREHENSIVE REPORT")
        report_lines.append("=" * 70)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Docs Root: {self.docs_root}")
        report_lines.append(f"Target Language: {self.target_lang}")
        report_lines.append(f"AI Enhancement: {'Enabled' if self.ai_enhance else 'Disabled'}")
        report_lines.append(f"Priority Only: {'Yes' if self.priority_only else 'No'}")
        report_lines.append("")
        
        # Summary Statistics
        report_lines.append("SUMMARY STATISTICS")
        report_lines.append("-" * 40)
        report_lines.append(f"Total English Files: {self.stats['total_english_files']:,}")
        report_lines.append(f"Total Arabic Files: {self.stats['total_arabic_files']:,}")
        report_lines.append(f"Existing Translations: {len(self.existing_translations):,}")
        report_lines.append(f"Missing Translations: {self.stats['missing_count']:,}")
        report_lines.append(f"Translation Coverage: {self.stats['coverage_percent']:.1f}%")
        report_lines.append(f"Files Created This Run: {self.stats['created_count']:,}")
        if self.ai_enhance:
            report_lines.append(f"AI-Enhanced Files: {self.stats['enhanced_count']:,}")
        report_lines.append(f"Errors Encountered: {self.stats['error_count']:,}")
        report_lines.append("")
        
        # Priority Analysis
        priority_missing = [f for f in self.missing_translations if self.is_priority_file(f)]
        priority_existing = [f for f in self.existing_translations if self.is_priority_file(f)]
        
        report_lines.append("PRIORITY FILES ANALYSIS")
        report_lines.append("-" * 35)
        report_lines.append(f"Total Priority Files: {len(self.priority_files):,}")
        report_lines.append(f"Priority Files Translated: {len(priority_existing):,}")
        report_lines.append(f"Priority Files Missing: {len(priority_missing):,}")
        if len(self.priority_files) > 0:
            priority_coverage = (len(priority_existing) / len(self.priority_files)) * 100
            report_lines.append(f"Priority Coverage: {priority_coverage:.1f}%")
        report_lines.append("")
        
        # Directory Breakdown
        report_lines.append("DIRECTORY COVERAGE BREAKDOWN")
        report_lines.append("-" * 45)
        
        dir_stats = {}
        for english_file in self.english_files:
            rel_path = english_file.relative_to(self.content_root)
            directory = str(rel_path.parent) if rel_path.parent != Path('.') else "root"
            
            if directory not in dir_stats:
                dir_stats[directory] = {"total": 0, "translated": 0, "missing": 0}
            
            dir_stats[directory]["total"] += 1
            if english_file in self.existing_translations:
                dir_stats[directory]["translated"] += 1
            else:
                dir_stats[directory]["missing"] += 1
        
        # Sort by coverage (worst first)
        sorted_dirs = sorted(
            [(dir_name, stats) for dir_name, stats in dir_stats.items() if stats["total"] >= 5],
            key=lambda x: x[1]["missing"] / x[1]["total"] if x[1]["total"] > 0 else 0,
            reverse=True
        )
        
        for directory, stats in sorted_dirs[:20]:
            missing_pct = (stats["missing"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            report_lines.append(f"  {directory[:50]:<50} {stats['missing']:>3}/{stats['total']:<3} missing ({missing_pct:5.1f}%)")
        
        if len(sorted_dirs) > 20:
            report_lines.append(f"  ... and {len(sorted_dirs) - 20} more directories")
        report_lines.append("")
        
        # Performance Metrics
        if self.stats["analysis_end_time"] and self.stats["analysis_start_time"]:
            analysis_time = (self.stats["analysis_end_time"] - self.stats["analysis_start_time"]).total_seconds()
            report_lines.append("PERFORMANCE METRICS")
            report_lines.append("-" * 30)
            report_lines.append(f"Analysis Time: {analysis_time:.1f} seconds")
            
            if self.stats["translation_end_time"] and self.stats["translation_start_time"]:
                translation_time = (self.stats["translation_end_time"] - self.stats["translation_start_time"]).total_seconds()
                report_lines.append(f"Translation Time: {translation_time:.1f} seconds")
                if self.stats["created_count"] > 0:
                    avg_time = translation_time / self.stats["created_count"]
                    report_lines.append(f"Average Time per File: {avg_time:.2f} seconds")
            report_lines.append("")
        
        # Recommendations
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 25)
        
        if self.stats["coverage_percent"] < 50:
            report_lines.append("• Translation coverage is low - prioritize high-impact files")
        
        if len(priority_missing) > 50:
            report_lines.append(f"• Focus on {len(priority_missing)} high-priority files first")
        
        if self.stats["error_count"] > 0:
            report_lines.append(f"• Review {self.stats['error_count']} files that had errors")
        
        if not self.ai_enhance:
            report_lines.append("• Consider using --ai-enhance for higher quality translations")
        
        if self.stats["created_count"] > 0:
            report_lines.append("• Review and improve newly created translations")
            report_lines.append("• Test translated pages for formatting and functionality")
        
        report_lines.append("• Set up regular translation maintenance workflow")
        report_lines.append("• Monitor for new English content that needs translation")
        report_lines.append("")
        
        return '\n'.join(report_lines)
    
    def save_detailed_status(self) -> str:
        """Save comprehensive status to JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"comprehensive_translation_status_{timestamp}.json"
        
        status_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "docs_root": str(self.docs_root),
                "target_language": self.target_lang,
                "ai_enhance": self.ai_enhance,
                "priority_only": self.priority_only,
                "report_only": self.report_only
            },
            "statistics": self.stats,
            "summary": {
                "total_files": len(self.english_files),
                "missing_translations": len(self.missing_translations),
                "priority_missing": len([f for f in self.missing_translations if self.is_priority_file(f)]),
                "coverage_percent": self.stats["coverage_percent"]
            },
            "file_details": {
                "missing_translations": [
                    {
                        "file": str(f.relative_to(self.content_root)),
                        "size_bytes": f.stat().st_size,
                        "is_priority": self.is_priority_file(f)
                    }
                    for f in self.missing_translations
                ],
                "existing_translations": [
                    str(f.relative_to(self.content_root)) for f in self.existing_translations
                ]
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Detailed status saved to: {filename}")
        return filename
    
    def run(self) -> bool:
        """Run the complete translation management process"""
        try:
            logger.info("Starting GitHub Docs Advanced Translation Manager")
            
            # Step 1: Analyze current state
            analysis_results = self.analyze_translations()
            
            # Step 2: Create translations (unless report-only)
            if not self.report_only:
                self.create_translations()
            
            # Step 3: Generate comprehensive report
            report = self.generate_comprehensive_report()
            print(report)
            
            # Step 4: Save detailed status
            self.save_detailed_status()
            
            logger.info("Translation management completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Translation management failed: {e}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Advanced GitHub Docs Translation Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 advanced_translator.py                      # Basic analysis and translation
  python3 advanced_translator.py --ai-enhance         # Use AI for quality translations
  python3 advanced_translator.py --priority-only      # Focus on high-priority files
  python3 advanced_translator.py --report-only        # Generate reports only
  python3 advanced_translator.py --ai-enhance --priority-only  # AI for priority files only
        """
    )
    
    parser.add_argument('--docs-root', default='docs', help='Path to docs directory')
    parser.add_argument('--target-lang', default='ar', help='Target language code')
    parser.add_argument('--ai-enhance', action='store_true', help='Use AI for translation (requires OpenAI API key)')
    parser.add_argument('--priority-only', action='store_true', help='Only translate high-priority files')
    parser.add_argument('--report-only', action='store_true', help='Generate reports without creating translations')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check dependencies
    if args.ai_enhance:
        if not HAS_OPENAI:
            print("Error: OpenAI library not installed. Run: pip install openai")
            return 1
        if not os.getenv('OPENAI_API_KEY'):
            print("Error: OPENAI_API_KEY environment variable not set")
            return 1
    
    # Initialize and run
    manager = AdvancedTranslationManager(
        docs_root=args.docs_root,
        target_lang=args.target_lang,
        ai_enhance=args.ai_enhance,
        priority_only=args.priority_only,
        report_only=args.report_only
    )
    
    try:
        success = manager.run()
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Process failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())