#!/usr/bin/env python3
"""
GitHub Docs Translation Analyzer

A standalone script to analyze the current state of Arabic translations
in the GitHub docs repository and create missing translations.

Features:
- Analyzes all English markdown files
- Identifies missing Arabic translations  
- Generates detailed reports
- Creates missing translation files
- No external dependencies required

Usage:
    python simple_translator.py                    # Analyze and create missing translations
    python simple_translator.py --analyze-only     # Only analyze, don't create files
    python simple_translator.py --verbose          # Enable verbose output
"""

import os
import json
import argparse
import logging
import re
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleTranslator:
    """Simple translation analyzer and creator for GitHub documentation"""
    
    def __init__(self, docs_root="docs", target_lang="ar", analyze_only=False):
        self.docs_root = Path(docs_root)
        self.content_root = self.docs_root / "content"
        self.target_lang = target_lang
        self.lang_suffix = f"-{target_lang}"
        self.analyze_only = analyze_only
        
        # Results storage
        self.english_files = []
        self.arabic_files = []
        self.missing_translations = []
        self.existing_translations = []
        
        # Statistics
        self.stats = {
            "total_english_files": 0,
            "total_arabic_files": 0,
            "missing_count": 0,
            "created_count": 0,
            "coverage_percent": 0
        }
        
        # Skip patterns
        self.skip_patterns = [
            r"\.git.*",
            r"\.DS_Store", 
            r".*\.tmp",
            r".*\.log",
            r"node_modules",
            r"\.next",
            r"__pycache__"
        ]
        
        # Priority directories (translate these first)
        self.priority_dirs = [
            "get-started",
            "authentication", 
            "account-and-profile",
            "actions",
            "issues",
            "pull-requests",
            "repositories",
            "copilot",
            "support"
        ]
    
    def should_skip_file(self, file_path):
        """Check if file should be skipped"""
        file_str = str(file_path)
        for pattern in self.skip_patterns:
            if re.search(pattern, file_str, re.IGNORECASE):
                return True
        return False
    
    def get_arabic_file_path(self, english_file):
        """Generate corresponding Arabic file path"""
        name_without_ext = english_file.stem
        arabic_name = f"{name_without_ext}{self.lang_suffix}.md"
        return english_file.parent / arabic_name
    
    def is_priority_file(self, file_path):
        """Check if file is in a priority directory"""
        rel_path = str(file_path.relative_to(self.content_root))
        for priority_dir in self.priority_dirs:
            if rel_path.startswith(priority_dir):
                return True
        return "index.md" in rel_path or "README.md" in rel_path
    
    def extract_frontmatter(self, content):
        """Extract frontmatter from markdown content"""
        lines = content.split('\n')
        if not lines or lines[0].strip() != '---':
            return {}, content
        
        # Find end of frontmatter
        fm_end = None
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                fm_end = i
                break
        
        if fm_end is None:
            return {}, content
        
        # Extract frontmatter and content
        frontmatter_lines = lines[1:fm_end]
        content_lines = lines[fm_end + 1:]
        
        # Parse frontmatter
        frontmatter = {}
        for line in frontmatter_lines:
            if ':' in line and not line.strip().startswith('#'):
                try:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    frontmatter[key] = value
                except ValueError:
                    continue
        
        return frontmatter, '\n'.join(content_lines)
    
    def create_arabic_frontmatter(self, english_fm):
        """Create Arabic frontmatter from English"""
        arabic_fm = english_fm.copy()
        
        # Simple translation dictionary for common terms
        translations = {
            "Getting started": "البدء",
            "Quick start": "البدء السريع", 
            "Authentication": "المصادقة",
            "Account and profile": "الحساب والملف الشخصي",
            "About": "حول",
            "Issues": "المشاكل",
            "Pull requests": "طلبات السحب",
            "Repositories": "المستودعات",
            "Actions": "الإجراءات",
            "Support": "الدعم",
            "GitHub": "GitHub",
            "Welcome": "مرحباً",
            "Documentation": "المستندات",
            "Guide": "دليل",
            "Tutorial": "برنامج تعليمي",
            "Reference": "مرجع",
            "Overview": "نظرة عامة"
        }
        
        # Translate common frontmatter fields
        if 'title' in arabic_fm:
            title = arabic_fm['title']
            for en_term, ar_term in translations.items():
                title = title.replace(en_term, ar_term)
            arabic_fm['title'] = title
        
        if 'shortTitle' in arabic_fm:
            short_title = arabic_fm['shortTitle']
            for en_term, ar_term in translations.items():
                short_title = short_title.replace(en_term, ar_term)
            arabic_fm['shortTitle'] = short_title
        
        if 'intro' in arabic_fm:
            intro = arabic_fm['intro']
            # Basic intro translations
            intro = intro.replace("Learn", "تعلم")
            intro = intro.replace("Understand", "افهم")
            intro = intro.replace("Get started", "ابدأ")
            intro = intro.replace("how to", "كيفية")
            arabic_fm['intro'] = intro
        
        return arabic_fm
    
    def create_arabic_content(self, english_content):
        """Create basic Arabic content structure"""
        frontmatter, content = self.extract_frontmatter(english_content)
        
        # Create Arabic frontmatter
        arabic_fm = self.create_arabic_frontmatter(frontmatter)
        
        # Create placeholder Arabic content
        arabic_content_lines = [
            "# " + arabic_fm.get('title', 'صفحة غير مترجمة'),
            "",
            "> **ملاحظة**: هذه الصفحة تحتاج إلى ترجمة. المحتوى أدناه باللغة الإنجليزية.",
            "",
            "---",
            "",
            content
        ]
        
        # Reconstruct file with Arabic frontmatter
        result_lines = ["---"]
        for key, value in arabic_fm.items():
            if isinstance(value, str) and ('"' in value or "'" in value):
                value = f'"{value}"'
            result_lines.append(f"{key}: {value}")
        result_lines.append("---")
        result_lines.append("")
        result_lines.extend(arabic_content_lines)
        
        return '\n'.join(result_lines)
    
    def find_all_files(self):
        """Find all English and Arabic files"""
        if not self.content_root.exists():
            logger.error(f"Content directory not found: {self.content_root}")
            return
        
        logger.info(f"Scanning content directory: {self.content_root}")
        
        # Find all markdown files
        for file_path in self.content_root.rglob("*.md"):
            if self.should_skip_file(file_path):
                continue
            
            if self.lang_suffix in file_path.name:
                self.arabic_files.append(file_path)
            else:
                self.english_files.append(file_path)
        
        logger.info(f"Found {len(self.english_files)} English files")
        logger.info(f"Found {len(self.arabic_files)} Arabic files")
    
    def analyze_translations(self):
        """Analyze current translation status"""
        logger.info("Analyzing translation status...")
        
        # Create set of existing Arabic file names for quick lookup
        arabic_names = {f.name for f in self.arabic_files}
        
        # Check each English file for corresponding Arabic translation
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
        
        logger.info(f"Translation coverage: {self.stats['coverage_percent']:.1f}%")
        logger.info(f"Missing translations: {self.stats['missing_count']}")
    
    def create_missing_translations(self):
        """Create missing Arabic translation files"""
        if self.analyze_only:
            logger.info("Analysis-only mode: skipping file creation")
            return
        
        logger.info(f"Creating {len(self.missing_translations)} missing translations...")
        
        # Sort by priority (priority files first, then by file size)
        missing_sorted = sorted(
            self.missing_translations,
            key=lambda f: (not self.is_priority_file(f), f.stat().st_size),
            reverse=False
        )
        
        created_count = 0
        for english_file in missing_sorted:
            try:
                arabic_file = self.get_arabic_file_path(english_file)
                
                # Read English content
                with open(english_file, 'r', encoding='utf-8') as f:
                    english_content = f.read()
                
                # Create Arabic content
                arabic_content = self.create_arabic_content(english_content)
                
                # Ensure directory exists
                arabic_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Write Arabic file
                with open(arabic_file, 'w', encoding='utf-8') as f:
                    f.write(arabic_content)
                
                created_count += 1
                rel_path = english_file.relative_to(self.content_root)
                priority_mark = " [PRIORITY]" if self.is_priority_file(english_file) else ""
                logger.info(f"Created: {rel_path} -> {arabic_file.name}{priority_mark}")
                
            except Exception as e:
                logger.error(f"Error creating translation for {english_file}: {e}")
        
        self.stats["created_count"] = created_count
        logger.info(f"Successfully created {created_count} translation files")
    
    def generate_report(self):
        """Generate analysis report"""
        print("\n" + "=" * 60)
        print("GITHUB DOCS ARABIC TRANSLATION ANALYSIS")
        print("=" * 60)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Docs Root: {self.docs_root}")
        print(f"Content Root: {self.content_root}")
        print()
        
        # Summary statistics
        print("SUMMARY STATISTICS")
        print("-" * 30)
        print(f"Total English Files: {self.stats['total_english_files']}")
        print(f"Total Arabic Files: {self.stats['total_arabic_files']}")
        print(f"Existing Translations: {len(self.existing_translations)}")
        print(f"Missing Translations: {self.stats['missing_count']}")
        print(f"Translation Coverage: {self.stats['coverage_percent']:.1f}%")
        if not self.analyze_only:
            print(f"Files Created: {self.stats['created_count']}")
        print()
        
        # Priority files analysis
        priority_missing = [f for f in self.missing_translations if self.is_priority_file(f)]
        if priority_missing:
            print("HIGH PRIORITY MISSING TRANSLATIONS")
            print("-" * 40)
            for file_path in priority_missing[:10]:
                rel_path = file_path.relative_to(self.content_root)
                print(f"  • {rel_path}")
            if len(priority_missing) > 10:
                print(f"  ... and {len(priority_missing) - 10} more priority files")
            print()
        
        # Directory analysis
        print("DIRECTORY ANALYSIS")
        print("-" * 25)
        dir_stats = {}
        
        for english_file in self.english_files:
            rel_path = english_file.relative_to(self.content_root)
            directory = str(rel_path.parent) if rel_path.parent != Path('.') else "root"
            
            if directory not in dir_stats:
                dir_stats[directory] = {"total": 0, "missing": 0}
            
            dir_stats[directory]["total"] += 1
            if english_file in self.missing_translations:
                dir_stats[directory]["missing"] += 1
        
        # Sort directories by coverage (worst first)
        sorted_dirs = sorted(
            dir_stats.items(),
            key=lambda x: x[1]["missing"] / x[1]["total"] if x[1]["total"] > 0 else 0,
            reverse=True
        )
        
        for directory, stats in sorted_dirs[:15]:  # Show top 15 directories
            if stats["total"] > 0:
                missing_pct = (stats["missing"] / stats["total"]) * 100
                print(f"  {directory}: {stats['missing']}/{stats['total']} missing ({missing_pct:.1f}%)")
        print()
        
        # Recommendations
        print("RECOMMENDATIONS")
        print("-" * 20)
        if self.stats["coverage_percent"] < 50:
            print("• Translation coverage is low - focus on high-priority directories first")
        
        if priority_missing:
            print(f"• Translate {len(priority_missing)} high-priority files first")
        
        if self.stats["missing_count"] > 100:
            print("• Consider using automated translation tools for initial drafts")
            print("• Focus on index.md and README.md files in each directory")
        
        print("• Review and improve translations after initial creation")
        print("• Set up regular translation maintenance workflow")
        print()
    
    def save_translation_status(self):
        """Save detailed translation status to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"translation_status_{timestamp}.json"
        
        # Prepare data for JSON serialization
        status_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "docs_root": str(self.docs_root),
                "target_language": self.target_lang
            },
            "statistics": self.stats,
            "missing_translations": [
                {
                    "english_file": str(f.relative_to(self.content_root)),
                    "arabic_file": str(self.get_arabic_file_path(f).relative_to(self.content_root)),
                    "is_priority": self.is_priority_file(f),
                    "size_bytes": f.stat().st_size
                }
                for f in self.missing_translations
            ],
            "existing_translations": [
                str(f.relative_to(self.content_root)) for f in self.existing_translations
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Translation status saved to: {filename}")
        return filename
    
    def run(self):
        """Run the complete translation analysis and creation process"""
        logger.info("Starting GitHub Docs translation analysis")
        
        try:
            # Step 1: Find all files
            self.find_all_files()
            
            # Step 2: Analyze translation status
            self.analyze_translations()
            
            # Step 3: Create missing translations (if not analyze-only mode)
            if not self.analyze_only:
                self.create_missing_translations()
            
            # Step 4: Generate report
            self.generate_report()
            
            # Step 5: Save detailed status
            self.save_translation_status()
            
            logger.info("Translation process completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Translation process failed: {e}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze and create GitHub Docs Arabic translations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python simple_translator.py                    # Analyze and create missing translations
  python simple_translator.py --analyze-only     # Only analyze, don't create files
  python simple_translator.py --verbose          # Enable verbose output
  python simple_translator.py --docs-root ../docs  # Use different docs directory
        """
    )
    
    parser.add_argument(
        '--docs-root',
        default='docs',
        help='Path to docs directory (default: docs)'
    )
    
    parser.add_argument(
        '--target-lang',
        default='ar',
        help='Target language code (default: ar)'
    )
    
    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='Only analyze current translations, do not create new files'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize and run translator
    translator = SimpleTranslator(
        docs_root=args.docs_root,
        target_lang=args.target_lang,
        analyze_only=args.analyze_only
    )
    
    try:
        success = translator.run()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Process failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())