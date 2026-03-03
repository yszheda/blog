# Galoisplusplus Blog

A personal blog about technology, classical music, and more, built with [Pelican](https://getpelican.com/) static site generator.

## Features

- **Modern Theme**: Uses the [pelican-fh5co-marble](https://github.com/claudio-walser/pelican-fh5co-marble) theme with responsive design
- **Multilingual Support**: Content available in both Chinese (zh) and English (en)
- **Static Site**: Fast, secure, and hosted on GitHub Pages
- **Markdown Content**: All articles written in Markdown format

## Directory Structure

```
├── content/              # Blog posts and pages (Markdown files)
├── static/               # Static files (images, downloads, CSS)
│   ├── images/           # Article images and assets
│   ├── downloads/        # Downloadable files
│   └── css/              # Custom CSS overrides
├── themes/               # Custom themes
│   └── pelican-fh5co-marble/  # Current theme
├── pelicanconf.py        # Development configuration
├── publishconf.py        # Production configuration
└── Makefile              # Build and deployment commands
```

## Development Setup

### Prerequisites

- Python 3.6+
- pip package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/yszheda/blog.git
cd blog

# Install dependencies
pip install pelican[markdown]
```

### Local Development

```bash
# Build the site locally
pelican content -s pelicanconf.py -o output
cp -r static/* output/

# Serve locally (if you have Python's HTTP server)
python -m http.server -d output 8000
```

### Using Makefile (if available)

```bash
# Build site
make html

# Build and serve locally  
make serve

# Clean output directory
make clean
```

## Deployment

The site is automatically deployed to GitHub Pages using the following process:

1. Build the site with production settings: `pelican content -s publishconf.py -o output`
2. Copy static files: `cp -r static/* output/`
3. Deploy to gh-pages branch

### Manual Deployment

```bash
# Build for production
rm -rf output && pelican content -s publishconf.py -o output && cp -r static/* output/

# Deploy using ghp-import (if installed)
ghp-import -n -p -f output

# Or use manual git deployment (see Makefile for details)
```

## Content Management

### Creating New Posts

Create new Markdown files in the `content/` directory with the following format:

```markdown
Title: Your Post Title
Date: 2023-12-01 10:00:00
Category: tech
Tags: python, pelican, static-site
Slug: your-post-slug

Your post content here...
```

### Images

Place images in the `static/images/` directory and reference them in your posts as:

```markdown
![Image description](/images/your-image.jpg)
```

## Configuration

- **pelicanconf.py**: Development configuration (local preview)
- **publishconf.py**: Production configuration (GitHub Pages deployment)

Key configuration options include:
- `SITEURL`: Base URL for the site
- `THEME`: Current theme path
- `STATIC_PATHS`: Static file directories to copy
- `I18N_SUBSITES`: Multilingual support configuration

## License

This blog content is © Galoisplusplus. The source code and configuration are available under the MIT License.

## Acknowledgments

- [Pelican](https://getpelican.com/) - Static site generator
- [pelican-fh5co-marble](https://github.com/claudio-walser/pelican-fh5co-marble) - Theme by Claudio Walser
- [FreeHTML5.co](https://freehtml5.co/) - Original theme design