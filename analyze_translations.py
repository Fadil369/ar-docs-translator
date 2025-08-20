#!/usr/bin/env python3
"""
GitHub Docs Translation Analyzer

A standalone script to analyze the current state of Arabic translations
in the GitHub docs repository. This script provides comprehensive reporting
without requiring external dependencies.

Features:
- Analyzes all English markdown files
- Identifies missing Arabic translations  
- Generates detailed reports
- No external dependencies required
- Creates translation mapping files

Usage:
    python analyze_translations.py
    python analyze_translations.py --output-format json
    python analyze_translations.py --verbose
"""

import os
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TranslationAnalyzer:
    """Analyze translation status of GitHub documentation"""
    
    def __init__(self, docs_root: str = "docs", target_lang: str = "ar"):
        self.docs_root = Path(docs_root)
        self.content_root = self.docs_root / "content"
        self.target_lang = target_lang
        self.lang_suffix = f"-{target_lang}"
        
        # Analysis results
        self.analysis = {
            "english_files": [],
            "arabic_files": [],
            "missing_translations": [],
            "existing_translations": [],
            "directory_coverage": {},
            "file_size_analysis": {},
            "priority_files": []
        }
        
        # Statistics
        self.stats = {
            "total_english_files": 0,
            "total_arabic_files": 0,
            "translation_coverage_percent": 0,
            "missing_count": 0,
            "directories_analyzed": 0,
            "total_content_size": 0,
            "translated_content_size": 0
        }
        
        # Skip patterns for files that shouldn't be translated
        self.skip_patterns = [
            r"\.git.*",
            r"\.DS_Store", 
            r".*\.tmp",
            r".*\.log",
            r"node_modules",
            r"\.next",
            r"__pycache__",
            r".*test.*\.md$",  # Test files
            r".*spec.*\.md$",  # Specification files
        ]
        
        # Priority file patterns (important files that should be translated first)
        self.priority_patterns = [
            r"index\.md$",
            r"README\.md$", 
            r"get-started/.*\.md$",
            r"authentication/.*\.md$",
            r"account-and-profile/.*\.md$",
            r"actions/.*\.md$",
            r"copilot/.*\.md$",
            r"issues/.*\.md$",
            r"pull-requests/.*\.md$",
            r"repositories/.*\.md$"
        ]
    
    def should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped"""
        for pattern in self.skip_patterns:
            if re.search(pattern, file_path, re.IGNORECASE):
                return True
        return False
    
    def is_priority_file(self, file_path: str) -> bool:
        """Check if file is high priority for translation"""
        for pattern in self.priority_patterns:
            if re.search(pattern, file_path, re.IGNORECASE):
                return True
        return False
    
    def get_arabic_file_path(self, english_file: Path) -> Path:
        """Generate corresponding Arabic file path"""
        name_without_ext = english_file.stem
        arabic_name = f"{name_without_ext}{self.lang_suffix}.md"
        return english_file.parent / arabic_name
    
    def extract_frontmatter_simple(self, content: str) -> Dict:
        """Extract frontmatter without external dependencies"""
        lines = content.split('\n')
        if not lines or lines[0].strip() != '---':
            return {}
        
        # Find end of frontmatter
        fm_end = None
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                fm_end = i
                break
        
        if fm_end is None:
            return {}
        
        # Parse frontmatter (basic YAML parsing)
        frontmatter = {}
        for line in lines[1:fm_end]:
            if ':' in line and not line.strip().startswith('#'):
                try:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    frontmatter[key] = value
                except ValueError:
                    continue
        
        return frontmatter
    
    def get_file_info(self, file_path: Path) -> Dict:
        """Get detailed information about a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            frontmatter = self.extract_frontmatter_simple(content)
            
            # Count content metrics
            word_count = len(content.split())
            line_count = len(content.split('\n'))
            char_count = len(content)
            
            # Check for special content
            has_liquid_tags = bool(re.search(r'\{\%.*?\%\}', content))
            has_code_blocks = bool(re.search(r'```', content))
            has_tables = bool(re.search(r'\|.*\|', content))
            
            return {
                "path": str(file_path),
                "relative_path": str(file_path.relative_to(self.content_root)),
                "size_bytes": file_path.stat().st_size,
                "word_count": word_count,
                "line_count": line_count,
                "char_count": char_count,
                "title": frontmatter.get('title', ''),
                "has_liquid_tags": has_liquid_tags,
                "has_code_blocks": has_code_blocks,
                "has_tables": has_tables,
                "is_priority": self.is_priority_file(str(file_path.relative_to(self.content_root))),
                "frontmatter": frontmatter
            }
            
        except Exception as e:
            logger.error(f"Error analyzing file {file_path}: {e}")
            return {
                "path": str(file_path),
                "relative_path": str(file_path.relative_to(self.content_root)),
                "error": str(e)
            }
    
    def analyze_directory_coverage(self) -> Dict:
        """Analyze translation coverage by directory"""
        directory_stats = {}
        
        for english_file_info in self.analysis["english_files"]:
            rel_path = english_file_info["relative_path"]
            directory = str(Path(rel_path).parent)
            
            if directory not in directory_stats:
                directory_stats[directory] = {
                    "total_files": 0,
                    "translated_files": 0,
                    "missing_files": 0,
                    "total_size": 0,
                    "translated_size": 0,
                    "files": []
                }
            
            directory_stats[directory]["total_files"] += 1
            directory_stats[directory]["total_size"] += english_file_info.get("size_bytes", 0)
            
            # Check if translation exists
            english_path = Path(english_file_info["path"])
            arabic_path = self.get_arabic_file_path(english_path)
            
            file_status = {
                "english_file": rel_path,
                "arabic_file": str(arabic_path.relative_to(self.content_root)),
                "translated": arabic_path.exists(),
                "is_priority": english_file_info.get("is_priority", False),
                "word_count": english_file_info.get("word_count", 0)
            }
            
            if arabic_path.exists():
                directory_stats[directory]["translated_files"] += 1
                directory_stats[directory]["translated_size"] += english_file_info.get("size_bytes", 0)
            else:
                directory_stats[directory]["missing_files"] += 1
            
            directory_stats[directory]["files"].append(file_status)
        
        # Calculate coverage percentages
        for directory, stats in directory_stats.items():
            if stats["total_files"] > 0:
                stats["coverage_percent"] = (stats["translated_files"] / stats["total_files"]) * 100
            else:
                stats["coverage_percent"] = 0
        
        return directory_stats
    
    def find_all_files(self) -> Tuple[List[Path], List[Path]]:
        """Find all English and Arabic markdown files"""
        if not self.content_root.exists():
            logger.error(f"Content directory not found: {self.content_root}")
            return [], []
        
        english_files = []
        arabic_files = []
        
        # Walk through all markdown files
        for file_path in self.content_root.rglob("*.md"):
            rel_path = str(file_path.relative_to(self.content_root))
            
            # Skip files based on patterns
            if self.should_skip_file(rel_path):
                continue
            
            if self.lang_suffix in file_path.name:
                arabic_files.append(file_path)
            else:
                english_files.append(file_path)
        
        logger.info(f"Found {len(english_files)} English files")
        logger.info(f"Found {len(arabic_files)} Arabic files")
        
        return english_files, arabic_files
    
    def run_analysis(self) -> Dict:
        """Run complete translation analysis"""
        logger.info("Starting GitHub Docs translation analysis")
        logger.info(f"Docs root: {self.docs_root}")
        logger.info(f"Content root: {self.content_root}")
        logger.info(f"Target language: {self.target_lang}")
        
        # Find all files
        english_files, arabic_files = self.find_all_files()
        
        # Analyze English files
        logger.info("Analyzing English files...")
        for file_path in english_files:
            file_info = self.get_file_info(file_path)
            self.analysis["english_files"].append(file_info)
            
            if file_info.get("is_priority"):
                self.analysis["priority_files"].append(file_info)
        
        # Analyze Arabic files
        logger.info("Analyzing Arabic files...")
        for file_path in arabic_files:
            file_info = self.get_file_info(file_path)
            self.analysis["arabic_files"].append(file_info)
        
        # Find missing translations
        logger.info("Identifying missing translations...")
        arabic_file_paths = {Path(f["path"]).name for f in self.analysis["arabic_files"]}
        
        for english_file_info in self.analysis["english_files"]:
            english_path = Path(english_file_info["path"])
            expected_arabic_name = f"{english_path.stem}{self.lang_suffix}.md"
            
            if expected_arabic_name not in arabic_file_paths:
                self.analysis["missing_translations"].append(english_file_info)
            else:
                self.analysis["existing_translations"].append(english_file_info)
        
        # Analyze directory coverage
        logger.info("Analyzing directory coverage...")
        self.analysis["directory_coverage"] = self.analyze_directory_coverage()
        
        # Calculate statistics
        self.calculate_statistics()
        
        logger.info("Analysis completed!")
        return self.analysis
    
    def calculate_statistics(self):
        """Calculate comprehensive statistics"""
        self.stats["total_english_files"] = len(self.analysis["english_files"])
        self.stats["total_arabic_files"] = len(self.analysis["arabic_files"])
        self.stats["missing_count"] = len(self.analysis["missing_translations"])
        self.stats["directories_analyzed"] = len(self.analysis["directory_coverage"])
        
        # Calculate coverage percentage
        if self.stats["total_english_files"] > 0:
            translated_count = self.stats["total_english_files"] - self.stats["missing_count"]
            self.stats["translation_coverage_percent"] = (translated_count / self.stats["total_english_files"]) * 100
        
        # Calculate content size statistics
        self.stats["total_content_size"] = sum(
            f.get("size_bytes", 0) for f in self.analysis["english_files"]
        )
        
        translated_files = set(f["relative_path"] for f in self.analysis["existing_translations"])
        self.stats["translated_content_size"] = sum(
            f.get("size_bytes", 0) for f in self.analysis["english_files"]
            if f["relative_path"] in translated_files
        )
    
    def generate_report(self, output_format: str = "text") -> str:
        """Generate comprehensive analysis report"""
        if output_format == "json":
            return self.generate_json_report()
        else:
            return self.generate_text_report()
    
    def generate_text_report(self) -> str:
        """Generate human-readable text report"""
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("GITHUB DOCS ARABIC TRANSLATION ANALYSIS")
        report_lines.append("=" * 60)
        report_lines.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"Docs Root: {self.docs_root}")
        report_lines.append(f"Target Language: {self.target_lang}")
        report_lines.append("")
        
        # Summary Statistics
        report_lines.append("SUMMARY STATISTICS")
        report_lines.append("-" * 30)
        report_lines.append(f"Total English Files: {self.stats['total_english_files']}")
        report_lines.append(f"Total Arabic Files: {self.stats['total_arabic_files']}")
        report_lines.append(f"Missing Translations: {self.stats['missing_count']}")
        report_lines.append(f"Translation Coverage: {self.stats['translation_coverage_percent']:.1f}%")
        report_lines.append(f"Directories Analyzed: {self.stats['directories_analyzed']}")
        report_lines.append(f"Total Content Size: {self.stats['total_content_size']:,} bytes")
        report_lines.append(f"Translated Content Size: {self.stats['translated_content_size']:,} bytes")
        report_lines.append("")
        
        # Priority Files
        priority_missing = [f for f in self.analysis["missing_translations"] if f.get("is_priority")]
        if priority_missing:
            report_lines.append("HIGH PRIORITY MISSING TRANSLATIONS")
            report_lines.append("-" * 40)
            for file_info in priority_missing[:10]:  # Show top 10
                report_lines.append(f"  • {file_info['relative_path']}")
                if file_info.get("title"):
                    report_lines.append(f"    Title: {file_info['title']}")
                report_lines.append(f"    Size: {file_info.get('word_count', 0)} words")
            if len(priority_missing) > 10:
                report_lines.append(f"  ... and {len(priority_missing) - 10} more priority files")
            report_lines.append("")
        
        # Directory Coverage
        report_lines.append("DIRECTORY COVERAGE")
        report_lines.append("-" * 30)
        dir_coverage = sorted(
            self.analysis["directory_coverage"].items(),
            key=lambda x: x[1]["coverage_percent"]
        )
        
        for directory, stats in dir_coverage:
            if stats["total_files"] > 0:
                report_lines.append(f"{directory}")
                report_lines.append(f"  Coverage: {stats['coverage_percent']:.1f}% "
                                  f"({stats['translated_files']}/{stats['total_files']} files)")
                if stats["missing_files"] > 0:
                    report_lines.append(f"  Missing: {stats['missing_files']} files")
        report_lines.append("")
        
        # Top Missing Files by Size
        missing_by_size = sorted(
            self.analysis["missing_translations"],
            key=lambda x: x.get("word_count", 0),
            reverse=True
        )
        
        if missing_by_size:
            report_lines.append("LARGEST MISSING TRANSLATIONS")
            report_lines.append("-" * 35)
            for file_info in missing_by_size[:15]:  # Show top 15
                words = file_info.get("word_count", 0)
                report_lines.append(f"  • {file_info['relative_path']} ({words} words)")
                if file_info.get("title"):
                    report_lines.append(f"    \"{file_info['title']}\"")
            report_lines.append("")
        
        # Translation Recommendations
        report_lines.append("RECOMMENDATIONS")
        report_lines.append("-" * 20)
        
        if self.stats["translation_coverage_percent"] < 50:
            report_lines.append("• Focus on translating high-priority files first (index.md, README.md)")
            report_lines.append("• Start with get-started/ and authentication/ directories")
        
        if priority_missing:
            report_lines.append(f"• {len(priority_missing)} high-priority files need translation")
        
        worst_coverage = min(
            (stats for stats in self.analysis["directory_coverage"].values() if stats["total_files"] > 0),
            key=lambda x: x["coverage_percent"],
            default=None
        )
        if worst_coverage and worst_coverage["coverage_percent"] < 25:
            report_lines.append("• Some directories have very low coverage - consider batch translation")
        
        report_lines.append("")
        report_lines.append("For detailed file listings, use --output-format json")
        
        return "\n".join(report_lines)
    
    def generate_json_report(self) -> str:
        """Generate machine-readable JSON report"""
        report_data = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "docs_root": str(self.docs_root),
                "target_language": self.target_lang,
                "analyzer_version": "1.0.0"
            },
            "statistics": self.stats,
            "analysis": self.analysis
        }
        
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def save_translation_map(self, filename: str = None):
        """Save a mapping file for translation tools"""
        if filename is None:
            filename = f"translation_map_{self.target_lang}_{datetime.now().strftime('%Y%m%d')}.json"
        
        translation_map = {
            "metadata": {
                "created": datetime.now().isoformat(),
                "target_language": self.target_lang,
                "total_files": len(self.analysis["missing_translations"])
            },
            "missing_translations": []
        }
        
        for file_info in self.analysis["missing_translations"]:
            english_path = Path(file_info["path"])
            arabic_path = self.get_arabic_file_path(english_path)
            
            translation_map["missing_translations"].append({
                "english_file": file_info["relative_path"],
                "arabic_file": str(arabic_path.relative_to(self.content_root)),
                "priority": file_info.get("is_priority", False),
                "word_count": file_info.get("word_count", 0),
                "title": file_info.get("title", ""),
                "size_bytes": file_info.get("size_bytes", 0)
            })
        
        # Sort by priority and size
        translation_map["missing_translations"].sort(
            key=lambda x: (not x["priority"], -x["word_count"])
        )
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(translation_map, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Translation map saved to: {filename}")
        return filename

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Analyze GitHub Docs translation status",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_translations.py                   # Basic analysis
  python analyze_translations.py --verbose         # Detailed logging
  python analyze_translations.py --output-format json > report.json
  python analyze_translations.py --save-map        # Create translation mapping file
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
        '--output-format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    
    parser.add_argument(
        '--save-map',
        action='store_true',
        help='Save translation mapping file'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize analyzer
    analyzer = TranslationAnalyzer(
        docs_root=args.docs_root,
        target_lang=args.target_lang
    )
    
    try:
        # Run analysis
        analysis_results = analyzer.run_analysis()
        
        # Generate and display report
        report = analyzer.generate_report(args.output_format)
        print(report)
        
        # Save translation map if requested
        if args.save_map:
            analyzer.save_translation_map()
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())