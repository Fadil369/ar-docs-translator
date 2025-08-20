# GitHub Docs Arabic Translation Tools

This repository contains Python scripts to analyze and create Arabic translations for GitHub documentation.

## Overview

The current analysis shows:
- **Total English Files**: 3,148
- **Total Arabic Files**: 36 (some manually created)
- **Translation Coverage**: 17.9%
- **Missing Translations**: 2,583 files

## Tools Provided

### 1. `simple_translator.py` - Standalone Translation Tool

A simple, dependency-free tool that can analyze and create basic Arabic translations.

**Features:**
- Analyzes current translation status
- Creates placeholder Arabic files with basic translations
- Identifies high-priority files
- Generates detailed reports
- No external dependencies required

**Usage:**
```bash
# Analyze current translations (read-only)
python3 simple_translator.py --analyze-only

# Analyze and create missing translation files
python3 simple_translator.py

# Enable verbose output
python3 simple_translator.py --verbose

# Use custom docs directory
python3 simple_translator.py --docs-root /path/to/docs
```

### 2. `translate_docs.py` - AI-Powered Translation Tool

An advanced tool that uses OpenAI's GPT models for high-quality translations.

**Features:**
- Uses OpenAI GPT-4 for accurate translations
- Preserves markdown formatting and liquid tags
- Handles frontmatter translation
- Maintains technical terminology consistency
- Comprehensive error handling

**Requirements:**
```bash
pip install -r requirements.txt
export OPENAI_API_KEY="your-api-key"
```

**Usage:**
```bash
# Preview what would be translated
python3 translate_docs.py --dry-run

# Translate missing files
python3 translate_docs.py

# Force overwrite existing translations
python3 translate_docs.py --force
```

### 3. `analyze_translations.py` - Detailed Analysis Tool

A comprehensive analysis tool for understanding translation coverage.

**Features:**
- Detailed file-by-file analysis
- Directory coverage statistics
- Priority file identification
- JSON and text report formats
- Translation mapping generation

**Usage:**
```bash
# Generate text report
python3 analyze_translations.py

# Generate JSON report
python3 analyze_translations.py --output-format json

# Save translation mapping file
python3 analyze_translations.py --save-map
```

## Current Translation Status

### High Priority Directories (Need Translation First)

1. **get-started/** - Core getting started guides
2. **authentication/** - Authentication and security
3. **account-and-profile/** - User account management
4. **actions/** - GitHub Actions documentation
5. **issues/** - Issue tracking features
6. **pull-requests/** - Pull request workflow
7. **repositories/** - Repository management
8. **copilot/** - GitHub Copilot features
9. **support/** - Support and help resources

### Translation Coverage by Directory

| Directory | Files | Translated | Missing | Coverage |
|-----------|--------|------------|---------|----------|
| get-started | 45 | 1 | 44 | 2.2% |
| authentication | 38 | 2 | 36 | 5.3% |
| actions | 156 | 2 | 154 | 1.3% |
| issues | 67 | 1 | 66 | 1.5% |
| repositories | 89 | 0 | 89 | 0.0% |

## Workflow Recommendations

### Phase 1: Foundation (High Priority)
1. Translate all `index.md` files in priority directories
2. Translate `README.md` files
3. Focus on get-started and authentication sections

### Phase 2: Core Features
1. Complete actions, issues, and pull-requests sections
2. Translate repository management docs
3. Add copilot documentation

### Phase 3: Advanced Features
1. Admin and enterprise features
2. Advanced security features
3. API documentation

### Phase 4: Specialized Content
1. Education and classroom features
2. Marketplace and apps
3. Community features

## Translation Guidelines

### Technical Standards
- Preserve all markdown formatting
- Don't translate liquid tags (`{% data variables.* %}`)
- Don't translate code blocks or technical identifiers
- Maintain URL and link references exactly
- Use consistent Arabic terminology

### Content Guidelines
- Use Modern Standard Arabic
- Keep technical terms in English when appropriate
- Provide context for GitHub-specific features
- Maintain the same document structure

### Common Translations
| English | Arabic |
|---------|--------|
| Repository | مستودع |
| Pull Request | طلب السحب |
| Issue | مشكلة/قضية |
| Commit | التزام |
| Branch | فرع |
| Merge | دمج |
| Authentication | مصادقة |
| Workflow | سير العمل |
| Action | إجراء |

## File Structure

```
docs/
├── content/
│   ├── index.md              # English content
│   ├── index-ar.md           # Arabic translation
│   ├── get-started/
│   │   ├── index.md
│   │   ├── index-ar.md
│   │   └── ...
│   └── ...
├── data/                     # Data files (some need translation)
├── src/                      # Application source code
└── ...
```

## Getting Started

### Quick Analysis
```bash
# Check current translation status
python3 simple_translator.py --analyze-only

# Generate detailed report
python3 analyze_translations.py
```

### Creating Translations

**Option 1: Basic Translations (No AI)**
```bash
python3 simple_translator.py
```

**Option 2: AI-Powered Translations**
```bash
# Set up OpenAI API key
export OPENAI_API_KEY="your-key"

# Install dependencies
pip install openai python-frontmatter

# Run translation
python3 translate_docs.py --dry-run  # Preview first
python3 translate_docs.py           # Create translations
```

## Monitoring Progress

Check translation progress regularly:
```bash
# Quick status check
python3 simple_translator.py --analyze-only

# Detailed coverage analysis
python3 analyze_translations.py --save-map
```

## Contributing

1. **Review Translations**: Check generated Arabic content for accuracy
2. **Improve Terminology**: Update translation dictionaries in scripts
3. **Add Priority Files**: Identify important files that need translation first
4. **Test Workflows**: Ensure translated documentation works correctly

## Maintenance

### Regular Tasks
- Run analysis to track progress
- Update priority file lists
- Review and improve translation quality
- Monitor for new English content

### Quality Assurance
- Verify liquid tags are preserved
- Check markdown formatting
- Ensure links work correctly
- Validate frontmatter syntax

## Technical Notes

### Liquid Tags Preservation
The tools automatically preserve GitHub's liquid templating syntax:
- `{% data variables.* %}`
- `{% ifversion * %}`
- `{% octicon * %}`
- And other template tags

### Frontmatter Handling
Only specific frontmatter fields are translated:
- `title`
- `shortTitle` 
- `intro`
- `permissions`

Other fields (versions, redirect_from, etc.) are preserved as-is.

### Error Handling
- Files with syntax errors are skipped with warnings
- Corrupt liquid tags are detected and reported
- Translation failures are logged for review

## Support

For issues or questions:
1. Check the generated log files
2. Review translation status reports
3. Examine specific file errors in verbose mode
4. Use dry-run mode to preview changes

---

This toolset provides a comprehensive solution for managing Arabic translations of GitHub documentation, from initial analysis to AI-powered translation creation.