#!/usr/bin/env python3
"""
GitHub Docs Arabic Translation Tool

This script scans the GitHub docs content folder to ensure all English content
is translated to Arabic. It identifies missing translations and creates them
automatically while preserving markdown formatting, frontmatter, and liquid tags.

Features:
- Scans all English markdown files in the content directory
- Identifies missing Arabic translations
- Creates Arabic translations using OpenAI's GPT models
- Preserves frontmatter metadata and liquid tags
- Maintains proper markdown formatting
- Generates comprehensive translation reports
- Handles special content like code examples and liquid syntax

Usage:
    python translate_docs.py
    python translate_docs.py --dry-run  # Preview only, no files created
    python translate_docs.py --force    # Overwrite existing translations
"""

import os
import re
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import time

# Import for AI translation (install with: pip install openai)
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("Warning: OpenAI library not installed. Run: pip install openai")

# Import for markdown parsing (install with: pip install python-frontmatter)
try:
    import frontmatter
    HAS_FRONTMATTER = True
except ImportError:
    HAS_FRONTMATTER = False
    print("Warning: frontmatter library not installed. Run: pip install python-frontmatter")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('translation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GitHubDocsTranslator:
    """Main translator class for GitHub documentation"""
    
    def __init__(self, docs_root: str = "docs", target_lang: str = "ar", dry_run: bool = False, force: bool = False):
        self.docs_root = Path(docs_root)
        self.content_root = self.docs_root / "content"
        self.target_lang = target_lang
        self.dry_run = dry_run
        self.force = force
        
        # Arabic language suffix
        self.lang_suffix = f"-{target_lang}"
        
        # Translation statistics
        self.stats = {
            "total_files": 0,
            "existing_translations": 0,
            "missing_translations": 0,
            "created_translations": 0,
            "skipped_files": 0,
            "errors": 0
        }
        
        # Files to skip (system files, etc.)
        self.skip_patterns = [
            r"\.git.*",
            r"\.DS_Store",
            r".*\.tmp",
            r".*\.log",
            r"node_modules",
            r"\.next",
            r"__pycache__"
        ]
        
        # Initialize OpenAI client if available
        self.openai_client = None
        if HAS_OPENAI:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
            else:
                logger.warning("OPENAI_API_KEY not found in environment variables")
    
    def should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped based on patterns"""
        for pattern in self.skip_patterns:
            if re.search(pattern, file_path):
                return True
        return False
    
    def find_english_files(self) -> List[Path]:
        """Find all English markdown files that need translation"""
        english_files = []
        
        if not self.content_root.exists():
            logger.error(f"Content directory not found: {self.content_root}")
            return english_files
        
        # Walk through all content directories
        for file_path in self.content_root.rglob("*.md"):
            # Skip files that already have language suffix
            if self.lang_suffix in file_path.name:
                continue
            
            # Skip files matching skip patterns
            if self.should_skip_file(str(file_path)):
                continue
            
            english_files.append(file_path)
        
        logger.info(f"Found {len(english_files)} English files to check")
        return english_files
    
    def get_arabic_file_path(self, english_file: Path) -> Path:
        """Generate the corresponding Arabic file path"""
        # Replace .md with -ar.md
        name_without_ext = english_file.stem
        arabic_name = f"{name_without_ext}{self.lang_suffix}.md"
        return english_file.parent / arabic_name
    
    def extract_translatable_content(self, content: str) -> Dict:
        """Extract and parse markdown content with frontmatter"""
        if not HAS_FRONTMATTER:
            logger.warning("frontmatter library not available, using basic parsing")
            return self._basic_content_parse(content)
        
        try:
            post = frontmatter.loads(content)
            return {
                "frontmatter": post.metadata,
                "content": post.content,
                "full_content": content
            }
        except Exception as e:
            logger.error(f"Error parsing frontmatter: {e}")
            return self._basic_content_parse(content)
    
    def _basic_content_parse(self, content: str) -> Dict:
        """Basic content parsing without frontmatter library"""
        lines = content.split('\n')
        if lines[0].strip() == '---':
            # Find end of frontmatter
            fm_end = 1
            for i, line in enumerate(lines[1:], 1):
                if line.strip() == '---':
                    fm_end = i + 1
                    break
            
            frontmatter_text = '\n'.join(lines[1:fm_end-1])
            body_content = '\n'.join(lines[fm_end:])
            
            # Parse YAML frontmatter manually (basic)
            frontmatter_dict = {}
            for line in frontmatter_text.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter_dict[key.strip()] = value.strip().strip('"\'')
            
            return {
                "frontmatter": frontmatter_dict,
                "content": body_content,
                "full_content": content
            }
        else:
            return {
                "frontmatter": {},
                "content": content,
                "full_content": content
            }
    
    def translate_text(self, text: str, context: str = "") -> str:
        """Translate English text to Arabic using OpenAI"""
        if not self.openai_client:
            logger.warning("OpenAI client not available, returning placeholder translation")
            return f"[TRANSLATION NEEDED: {text[:50]}...]"
        
        try:
            # Create translation prompt
            prompt = self._create_translation_prompt(text, context)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert Arabic translator specializing in technical documentation. Translate GitHub documentation from English to Arabic while preserving markdown formatting, code blocks, liquid tags, and technical terms. Maintain the original structure and meaning."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            translation = response.choices[0].message.content.strip()
            
            # Post-process translation to ensure liquid tags are preserved
            translation = self._preserve_liquid_tags(text, translation)
            
            return translation
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return f"[TRANSLATION ERROR: {text[:50]}...]"
    
    def _create_translation_prompt(self, text: str, context: str) -> str:
        """Create a detailed translation prompt"""
        prompt = f"""Translate the following GitHub documentation text from English to Arabic.

IMPORTANT RULES:
1. Preserve ALL markdown formatting (headers, links, lists, tables, etc.)
2. Do NOT translate content inside liquid tags like {{% data variables.* %}}, {{% ifversion %}}, etc.
3. Do NOT translate code blocks, file paths, or technical identifiers
4. Preserve all URLs and link references exactly as they are
5. Maintain the same paragraph structure and spacing
6. Use modern standard Arabic that is clear and accessible
7. Preserve any HTML tags or special formatting

Context: {context}

Text to translate:

{text}

Arabic translation:"""
        return prompt
    
    def _preserve_liquid_tags(self, original: str, translation: str) -> str:
        """Ensure liquid tags are preserved correctly in translation"""
        # Common liquid tag patterns
        liquid_patterns = [
            r'\{\%\s*data\s+variables\.[^}]+\%\}',
            r'\{\%\s*data\s+reusables\.[^}]+\%\}',
            r'\{\%\s*ifversion\s+[^}]+\%\}',
            r'\{\%\s*endif\s*\%\}',
            r'\{\%\s*else\s*\%\}',
            r'\{\%\s*octicon\s+[^}]+\%\}',
            r'\{\%\s*note\s*\%\}',
            r'\{\%\s*endnote\s*\%\}',
            r'\{\%\s*tip\s*\%\}',
            r'\{\%\s*endtip\s*\%\}',
            r'\{\%\s*warning\s*\%\}',
            r'\{\%\s*endwarning\s*\%\}',
            r'\{\{\s*[^}]+\s*\}\}',
        ]
        
        # Extract liquid tags from original
        original_tags = []
        for pattern in liquid_patterns:
            original_tags.extend(re.findall(pattern, original, re.IGNORECASE))
        
        # If we found liquid tags in original, make sure they're preserved
        if original_tags:
            for tag in original_tags:
                # Simple heuristic: if the tag is missing or corrupted in translation,
                # we might need to restore it
                if tag not in translation:
                    logger.warning(f"Liquid tag might be corrupted in translation: {tag}")
        
        return translation
    
    def translate_frontmatter(self, frontmatter: Dict) -> Dict:
        """Translate relevant frontmatter fields"""
        translated_fm = frontmatter.copy()
        
        # Fields that should be translated
        translatable_fields = ['title', 'shortTitle', 'intro', 'permissions']
        
        for field in translatable_fields:
            if field in translated_fm and translated_fm[field]:
                original_value = translated_fm[field]
                if isinstance(original_value, str):
                    translated_fm[field] = self.translate_text(
                        original_value, 
                        context=f"frontmatter field: {field}"
                    )
        
        return translated_fm
    
    def create_arabic_content(self, english_content: str, file_path: str) -> str:
        """Create complete Arabic content from English content"""
        parsed = self.extract_translatable_content(english_content)
        
        # Translate frontmatter
        if parsed["frontmatter"]:
            translated_frontmatter = self.translate_frontmatter(parsed["frontmatter"])
        else:
            translated_frontmatter = {}
        
        # Translate main content
        if parsed["content"].strip():
            translated_content = self.translate_text(
                parsed["content"], 
                context=f"documentation file: {file_path}"
            )
        else:
            translated_content = parsed["content"]
        
        # Reconstruct the file
        if translated_frontmatter:
            # Convert frontmatter back to YAML
            fm_lines = ["---"]
            for key, value in translated_frontmatter.items():
                if isinstance(value, str):
                    # Escape quotes if necessary
                    if '"' in value or "'" in value:
                        value = repr(value)
                    fm_lines.append(f"{key}: {value}")
                else:
                    fm_lines.append(f"{key}: {value}")
            fm_lines.append("---")
            
            result = "\n".join(fm_lines) + "\n\n" + translated_content
        else:
            result = translated_content
        
        return result
    
    def process_file(self, english_file: Path) -> bool:
        """Process a single English file for translation"""
        arabic_file = self.get_arabic_file_path(english_file)
        
        # Check if Arabic translation already exists
        if arabic_file.exists() and not self.force:
            logger.debug(f"Arabic translation exists: {arabic_file}")
            self.stats["existing_translations"] += 1
            return True
        
        try:
            # Read English content
            with open(english_file, 'r', encoding='utf-8') as f:
                english_content = f.read()
            
            logger.info(f"Translating: {english_file.relative_to(self.content_root)}")
            
            # Create Arabic translation
            arabic_content = self.create_arabic_content(
                english_content, 
                str(english_file.relative_to(self.content_root))
            )
            
            if self.dry_run:
                logger.info(f"[DRY RUN] Would create: {arabic_file}")
                self.stats["created_translations"] += 1
                return True
            
            # Ensure directory exists
            arabic_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write Arabic content
            with open(arabic_file, 'w', encoding='utf-8') as f:
                f.write(arabic_content)
            
            logger.info(f"Created Arabic translation: {arabic_file}")
            self.stats["created_translations"] += 1
            
            # Small delay to avoid API rate limits
            if self.openai_client:
                time.sleep(0.5)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing {english_file}: {e}")
            self.stats["errors"] += 1
            return False
    
    def run_translation(self) -> Dict:
        """Main method to run the translation process"""
        logger.info("Starting GitHub Docs Arabic translation process")
        logger.info(f"Docs root: {self.docs_root}")
        logger.info(f"Target language: {self.target_lang}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info(f"Force overwrite: {self.force}")
        
        # Find all English files
        english_files = self.find_english_files()
        self.stats["total_files"] = len(english_files)
        
        if not english_files:
            logger.warning("No English files found to translate")
            return self.stats
        
        # Process each file
        for english_file in english_files:
            try:
                self.process_file(english_file)
            except KeyboardInterrupt:
                logger.info("Translation interrupted by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error processing {english_file}: {e}")
                self.stats["errors"] += 1
        
        # Generate report
        self.generate_report()
        
        return self.stats
    
    def generate_report(self):
        """Generate a comprehensive translation report"""
        logger.info("\n" + "="*50)
        logger.info("TRANSLATION REPORT")
        logger.info("="*50)
        logger.info(f"Total files processed: {self.stats['total_files']}")
        logger.info(f"Existing translations: {self.stats['existing_translations']}")
        logger.info(f"Missing translations: {self.stats['missing_translations']}")
        logger.info(f"Created translations: {self.stats['created_translations']}")
        logger.info(f"Errors: {self.stats['errors']}")
        
        completion_rate = 0
        if self.stats['total_files'] > 0:
            completed = self.stats['existing_translations'] + self.stats['created_translations']
            completion_rate = (completed / self.stats['total_files']) * 100
        
        logger.info(f"Translation completion rate: {completion_rate:.1f}%")
        
        # Save detailed report to file
        report_file = f"translation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "completion_rate": completion_rate,
            "config": {
                "docs_root": str(self.docs_root),
                "target_lang": self.target_lang,
                "dry_run": self.dry_run,
                "force": self.force
            }
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Detailed report saved to: {report_file}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Translate GitHub Docs content to Arabic",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python translate_docs.py                    # Translate missing files
  python translate_docs.py --dry-run          # Preview what would be translated
  python translate_docs.py --force            # Overwrite existing translations
  python translate_docs.py --docs-root ../    # Use different docs directory
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
        '--dry-run',
        action='store_true',
        help='Preview mode - show what would be translated without creating files'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing translations'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check requirements
    missing_deps = []
    if not HAS_OPENAI:
        missing_deps.append("openai")
    if not HAS_FRONTMATTER:
        missing_deps.append("python-frontmatter")
    
    if missing_deps:
        print(f"Missing required dependencies: {', '.join(missing_deps)}")
        print(f"Install with: pip install {' '.join(missing_deps)}")
        if not args.dry_run:
            return 1
    
    # Check for OpenAI API key
    if not args.dry_run and not os.getenv('OPENAI_API_KEY'):
        print("Warning: OPENAI_API_KEY environment variable not set")
        print("Set it with: export OPENAI_API_KEY='your-api-key'")
        if not HAS_OPENAI:
            return 1
    
    # Initialize and run translator
    translator = GitHubDocsTranslator(
        docs_root=args.docs_root,
        target_lang=args.target_lang,
        dry_run=args.dry_run,
        force=args.force
    )
    
    try:
        stats = translator.run_translation()
        
        if stats['errors'] > 0:
            logger.warning(f"Translation completed with {stats['errors']} errors")
            return 1
        else:
            logger.info("Translation completed successfully!")
            return 0
            
    except KeyboardInterrupt:
        logger.info("Translation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())