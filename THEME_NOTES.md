# Elegant Theme Configuration

## Theme Details
- **Name**: Elegant
- **Repository**: https://github.com/Pelican-Elegant/elegant
- **Type**: Professional tech blog theme
- **Location**: themes/elegant/

## Installation
```bash
git clone https://github.com/Pelican-Elegant/elegant.git themes/elegant
```

## Configuration

### Required Settings (pelicanconf.py)
```python
THEME = 'themes/elegant'

DIRECT_TEMPLATES = (
    "index",
    "tags",
    "categories",
    "authors",
    "archives",
)

STATIC_PATHS = ["images", "theme/images", "theme/css"]
```

### Custom Features Added

#### 1. MathJax Integration
- **File**: themes/elegant/templates/base.html
- **Version**: MathJax 2.7.9
- **Purpose**: LaTeX formula rendering
- **Inline math**: `$x$` or `\(x\)`
- **Display math**: `$$x$$` or `\[x\]`

#### 2. Custom CSS Style Overrides
- **File**: theme/css/custom.css
- **Purpose**: Enhanced styling for technical content
- **Improvements**:
  - Better code block styling
  - Improved typography
  - Cleaner link styling
  - Professional table design
  - Enhanced blockquotes
  - Inline code highlighting

### Styling Overview

#### Colors
- Primary: Slate/Gray tones (professional)
- Links: Blue (#007bff) with hover effects
- Code blocks: Light gray background (#f8f9fa)
- Borders: Light gray (#e9ecef)

#### Typography
- Article text: Line-height 1.8 for readability
- Headings: Bold, with bottom borders
- Navigation: Clean, sans-serif

#### Code Display
- Pygments style: monokai
- Line numbers: Enabled
- Syntax highlighting: Full language support

## Customization

### To modify colors
Edit `theme/css/custom.css` and update color values.

### To change Pygments theme
Edit `pelicanconf.py`:
```python
PYGMENTS_STYLE = "monokai"  # Try: 'default', 'pastie', 'tango', etc.
```

### To adjust navigation
Edit `pelicanconf.py`:
```python
LINKS = (
    ("Link Name", "URL"),
)
SOCIAL = (
    ("GitHub", "https://github.com/username"),
    ("Twitter", "https://twitter.com/username"),
)
```

## Preview
```bash
pelican content -s pelicanconf.py -o output -l
# Visit http://localhost:8000
```

## Build
```bash
pelican content -s pelicanconf.py -o output
```

## Why Elegant?

1. **Content-Focused**: Minimal design, emphasis on reading
2. **Professional**: Suitable for technical and academic blogs
3. **Code-Friendly**: Excellent syntax highlighting integration
4. **Well-Maintained**: Active development and community
5. **Responsive**: Works perfectly on mobile devices
6. **Features**: Includes search, categories, tags, archives
7. **Customizable**: Easy to extend with custom CSS
8. **Fast**: Minimal JavaScript dependency

## Alternatives Considered
- bootstrap3: Feature-rich but too generic
- attila: Good but less polished
- flex: Clean but fewer features

Elegant was selected for its balance of professionalism, features, and suitability for technical content with code and mathematics.
