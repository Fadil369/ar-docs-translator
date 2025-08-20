#!/usr/bin/env python3
"""
Simple Translation Quality Checker for GitHub Docs Arabic Translations
Performs comprehensive quality analysis without complex type annotations.
"""

import os
import json
import re
import logging
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleQualityChecker:
    def __init__(self, docs_root="docs"):
        self.docs_root = Path(docs_root)
        self.content_root = self.docs_root / "content"
        self.stats = {
            'total_files_checked': 0,
            'files_with_issues': 0,
            'perfect_translations': 0,
            'placeholder_only': 0,
            'missing_frontmatter': 0,
            'empty_files': 0,
            'quality_scores': []
        }
        
    def extract_frontmatter(self, content):
        """Extract YAML frontmatter from markdown content."""
        if not content.strip().startswith('---'):
            return {}, content
            
        try:
            parts = content.split('---', 2)
            if len(parts) >= 3:
                # Simple frontmatter parsing - look for key: value patterns
                frontmatter_text = parts[1].strip()
                frontmatter = {}
                
                for line in frontmatter_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        frontmatter[key.strip()] = value.strip().strip('"\'')
                
                body = parts[2].strip()
                return frontmatter, body
        except Exception as e:
            logger.warning(f"Frontmatter parsing error: {e}")
            
        return {}, content
    
    def check_frontmatter_quality(self, frontmatter, file_path):
        """Check the quality of frontmatter translation."""
        issues = []
        
        # Check if critical fields are translated
        translatable_fields = ['title', 'shortTitle', 'intro']
        
        for field in translatable_fields:
            if field in frontmatter:
                value = frontmatter[field]
                if value:
                    # Check if it contains Arabic characters
                    arabic_chars = 'ابتثجحخدذرزسشصضطظعغفقكلمنهوي'
                    has_arabic = any(char in value for char in arabic_chars)
                    
                    # Check for English indicators (excluding GitHub)
                    english_words = ['the', 'and', 'or', 'for', 'with', 'to', 'in', 'on', 'Learn', 'Get', 'Start', 'How']
                    has_english = any(word in value for word in english_words)
                    
                    if has_english and not has_arabic:
                        issues.append(f"Field '{field}' may need translation: '{value}'")
        
        return issues
    
    def check_content_quality(self, content, file_path):
        """Check the quality of content translation."""
        issues = []
        
        # Check if content is just placeholder
        placeholder_indicators = [
            "# [Translation Required]",
            "يحتاج هذا المحتوى إلى ترجمة",
            "This content needs translation",
            "<!-- Translation placeholder -->",
            "هذا محتوى نائب للترجمة"
        ]
        
        is_placeholder = any(indicator in content for indicator in placeholder_indicators)
        
        # Check for liquid tag preservation
        liquid_tags = re.findall(r'{%[^%]*%}', content)
        
        # Check if content is too short
        content_lines = [line.strip() for line in content.split('\n') if line.strip()]
        actual_content_lines = [
            line for line in content_lines 
            if not line.startswith('#') and not line.startswith('<!--') and not line.startswith('---')
        ]
        
        if len(actual_content_lines) < 2:
            issues.append("Content appears to be very short")
        
        # Check for preserved liquid tags
        if liquid_tags:
            logger.debug(f"Found {len(liquid_tags)} liquid tags in {file_path}")
        
        return issues, is_placeholder
    
    def check_file_pair(self, english_file):
        """Check quality of an English-Arabic file pair."""
        # Determine Arabic file path
        arabic_file = english_file.parent / f"{english_file.stem}-ar{english_file.suffix}"
        
        result = {
            'english_file': str(english_file.relative_to(self.content_root)),
            'arabic_file': str(arabic_file.relative_to(self.content_root)),
            'exists': arabic_file.exists(),
            'issues': [],
            'quality_score': 0,
            'is_placeholder': False
        }
        
        if not arabic_file.exists():
            result['issues'].append("Arabic translation file missing")
            return result
        
        try:
            # Read Arabic file
            with open(arabic_file, 'r', encoding='utf-8') as f:
                arabic_content = f.read()
            
            if not arabic_content.strip():
                result['issues'].append("Arabic file is empty")
                self.stats['empty_files'] += 1
                return result
            
            # Extract frontmatter and content
            arabic_frontmatter, arabic_body = self.extract_frontmatter(arabic_content)
            
            # Check frontmatter quality
            if not arabic_frontmatter:
                result['issues'].append("Missing or invalid frontmatter")
                self.stats['missing_frontmatter'] += 1
            else:
                frontmatter_issues = self.check_frontmatter_quality(arabic_frontmatter, arabic_file)
                result['issues'].extend(frontmatter_issues)
            
            # Check content quality
            content_issues, is_placeholder = self.check_content_quality(arabic_body, arabic_file)
            result['issues'].extend(content_issues)
            result['is_placeholder'] = is_placeholder
            
            if is_placeholder:
                self.stats['placeholder_only'] += 1
            
            # Calculate quality score
            max_score = 100
            score_deductions = len(result['issues']) * 15
            if is_placeholder:
                score_deductions += 20  # Placeholder content gets lower score
            
            result['quality_score'] = max(0, max_score - score_deductions)
            
        except Exception as e:
            result['issues'].append(f"Error reading Arabic file: {str(e)}")
            result['quality_score'] = 0
        
        return result
    
    def run_quality_check(self, sample_size=None):
        """Run comprehensive quality check on translations."""
        logger.info("Starting comprehensive translation quality check...")
        
        # Find all English markdown files
        english_files = []
        for md_file in self.content_root.rglob("*.md"):
            if not md_file.name.endswith('-ar.md'):
                english_files.append(md_file)
        
        logger.info(f"Found {len(english_files)} English files to check")
        
        # Sample if requested
        if sample_size and sample_size < len(english_files):
            import random
            english_files = random.sample(english_files, sample_size)
            logger.info(f"Sampling {sample_size} files for quality check")
        
        results = []
        
        for i, english_file in enumerate(english_files):
            if i % 500 == 0:
                logger.info(f"Checked {i}/{len(english_files)} files...")
            
            result = self.check_file_pair(english_file)
            results.append(result)
            
            self.stats['total_files_checked'] += 1
            self.stats['quality_scores'].append(result['quality_score'])
            
            if result['issues']:
                self.stats['files_with_issues'] += 1
            else:
                self.stats['perfect_translations'] += 1
        
        # Calculate overall statistics
        quality_scores = self.stats['quality_scores']
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_files': len(english_files),
            'average_quality_score': round(avg_quality, 2),
            'perfect_translations': self.stats['perfect_translations'],
            'files_with_issues': self.stats['files_with_issues'],
            'placeholder_only': self.stats['placeholder_only'],
            'missing_frontmatter': self.stats['missing_frontmatter'],
            'empty_files': self.stats['empty_files'],
            'quality_distribution': {
                'excellent': len([s for s in quality_scores if s >= 85]),
                'good': len([s for s in quality_scores if 70 <= s < 85]),
                'fair': len([s for s in quality_scores if 50 <= s < 70]),
                'poor': len([s for s in quality_scores if s < 50])
            },
            'sample_issues': results[:20]  # First 20 results for examination
        }
        
        return summary
    
    def generate_quality_report(self, results, output_file=None):
        """Generate a comprehensive quality report."""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"quality_report_{timestamp}.json"
        
        # Save detailed results
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "="*70)
        print("COMPREHENSIVE TRANSLATION QUALITY ANALYSIS")
        print("="*70)
        print(f"Analysis Date: {results['timestamp']}")
        print(f"Total Files Analyzed: {results['total_files']}")
        print(f"Average Quality Score: {results['average_quality_score']}/100")
        print()
        
        print("QUALITY DISTRIBUTION")
        print("--------------------")
        dist = results['quality_distribution']
        total = results['total_files']
        print(f"Excellent (85-100): {dist['excellent']} files ({dist['excellent']/total*100:.1f}%)")
        print(f"Good (70-84):       {dist['good']} files ({dist['good']/total*100:.1f}%)")
        print(f"Fair (50-69):       {dist['fair']} files ({dist['fair']/total*100:.1f}%)")
        print(f"Poor (<50):         {dist['poor']} files ({dist['poor']/total*100:.1f}%)")
        print()
        
        print("ISSUE SUMMARY")
        print("-------------")
        print(f"Perfect Translations: {results['perfect_translations']}")
        print(f"Files with Issues:    {results['files_with_issues']}")
        print(f"Placeholder Only:     {results['placeholder_only']}")
        print(f"Missing Frontmatter:  {results['missing_frontmatter']}")
        print(f"Empty Files:          {results['empty_files']}")
        print()
        
        # Show some examples of issues
        print("SAMPLE ISSUES FOUND")
        print("-------------------")
        issue_count = 0
        for result in results['sample_issues']:
            if result['issues'] and issue_count < 10:
                print(f"File: {result['arabic_file']} (Score: {result['quality_score']})")
                for issue in result['issues'][:2]:  # Show first 2 issues
                    print(f"  • {issue}")
                print()
                issue_count += 1
        
        if results['files_with_issues'] == 0:
            print("🎉 NO ISSUES FOUND! All translations appear to be perfect!")
        elif results['average_quality_score'] >= 85:
            print("✅ EXCELLENT QUALITY! Most translations are very good.")
        elif results['average_quality_score'] >= 70:
            print("👍 GOOD QUALITY! Translations are generally well done.")
        else:
            print("⚠️  NEEDS IMPROVEMENT! Some translations may need attention.")
        
        print(f"\nDetailed results saved to: {output_file}")
        
        return output_file

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Check translation quality comprehensively")
    parser.add_argument("--sample", type=int, help="Check only a sample of files (for faster testing)")
    parser.add_argument("--output", help="Output file for detailed results")
    args = parser.parse_args()
    
    checker = SimpleQualityChecker()
    results = checker.run_quality_check(sample_size=args.sample)
    checker.generate_quality_report(results, args.output)

if __name__ == "__main__":
    main()