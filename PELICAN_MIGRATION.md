# Octopress to Pelican Migration Guide

## Overview
This guide documents the migration of the blog from Octopress to Pelican static site generator.

## Migration Summary

### What Was Done
- **Articles Converted**: 84 blog posts converted from Octopress markdown to Pelican format
- **Configuration**: Complete Pelican setup with pelicanconf.py
- **Theme**: Using pelican-bootstrap3 theme
- **Code Highlighting**: Pygments with monokai style
- **MathJax**: Integrated for LaTeX rendering
- **Build System**: Makefile created for easy site generation

## Files Created/Modified

### Configuration Files
- `pelicanconf.py` - Main Pelican configuration
- `publishconf.py` - Production settings
- `Makefile` - Build automation
- `convert_octopress_to_pelican.py` - Migration script

### Content
- `content/` - All markdown articles (84 files)
- `output/` - Generated HTML site

### Theme
- `pelican-themes/` - Cloned theme repository

## How to Build and Run

### Build the Site
```bash
make html
# or
pelican content -s pelicanconf.py -o output
```

### Preview Locally
```bash
make serve
# or
pelican content -s pelicanconf.py -o output -l
```
Then open http://localhost:8000

### Clean Output
```bash
make clean
# or
rm -rf output
```

### Publish for Production
```bash
make publish
# or
pelican content -s publishconf.py -o output
```

## Key Features

### Code Syntax Highlighting
- Uses Pygments
- Style: monokai
- Supports line numbers
- Fenced code blocks (```lang) work automatically

### LaTeX/MathJax Support
- MathJax 2.7.9 loaded automatically
- Inline math: $formula$ or \(formula\)
- Display math: $$formula$$ or \[formula\]

### Article Meta
Converted from Octopress front matter:
```markdown
Title: Article Title
Date: YYYY-MM-DD HH:MM:SS
Tags: tag1, tag2, tag3
Slug: yyyy-mm-dd-article-title
Description: Article description
```

### URL Structure
Articles: `/{year}/{month}/{day}/{slug}.html`
Categories: `/category/{name}.html`
Tags: `/tag/{name}.html`

## Differences from Octopress

### Liquid Tags Conversion
- `{% img /path/to/image %}` → `![image](/path/to/image)`
- `{% imgcap /image.png 'caption' %}` → `![caption](/image.png)`
- `{% codeblock lang:xxx %}` → \```xxx
- `{% include_code file.ext %}` → `[Code: file.ext]` (placeholder)

### Front Matter
- Octopress: YAML format with `---`
- Pelican: Key: Value format without markers

### Categories vs Tags
- Octopress: Supports multiple categories
- Pelican: Uses tags mainly (categories converted to tags)

## Known Issues

1. **Images**: Original Octopress images in `{% img %}` tags need to be manually handled
2. **Include Code**: The `{% include_code %}` feature is not fully converted
3. **Image Captions**: Some image captions may need manual adjustment

## Next Steps

1. **Test**: Run `make serve` and test in browser
2. **Check Links**: Verify internal and external links work
3. **Images**: Copy any missing images to appropriate directories
4. **Deploy**: Set up deployment to GitHub Pages or hosting service

## Deployment

For GitHub Pages:
```bash
rm -rf .git
cd output
git init
git add .
git commit -m "Initial Pelican site"
git remote add origin git@github.com:username/username.github.io.git
git branch -M gh-pages
git push -u origin gh-pages
```

Or use gh-pages branch pattern in main repository.

## Resources

- Pelican Docs: https://docs.getpelican.com/
- pelican-bootstrap3 Theme: https://github.com/getpelican/pelican-bootstrap3
- MathJax: https://www.mathjax.org/
