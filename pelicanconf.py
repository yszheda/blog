#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = "Galoisplusplus"
SITENAME = "Galoisplusplus"

# LOCAL PREVIEW SETTINGS
# For local development, use empty SITEURL to make links work locally
SITEURL = ""

# For GitHub Pages deployment, uncomment the line below:
# SITEURL = "http://yszheda.github.io/blog"

PATH = "content"

TIMEZONE = "Asia/Shanghai"

DEFAULT_LANG = "zh"

# Feed generation
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (
    ("Pelican", "http://getpelican.com/"),
    ("Python.org", "http://python.org/"),
)

# Social widget
SOCIAL = (
    ("GitHub", "https://github.com/yszheda"),
    ("Twitter", "https://twitter.com/yszheda"),
)

DEFAULT_PAGINATION = 10

# Theme settings - Elegant
THEME = "themes/elegant"

# Elegant theme configuration
DIRECT_TEMPLATES = (
    "index",
    "tags",
    "categories",
    "authors",
    "archives",
)

PAGINATED_TEMPLATES = (
    (
        "index",
        "tags",
        "categories",
        "authors",
    ),
)

# Static files
STATIC_PATHS = ["static/images", "static/downloads", "static/css", "theme/images", "theme/css"]

EXTRA_PATH_METADATA = {
    "static/css/custom.css": {"path": "static/css/custom.css"},
    "static/css/monokai.css": {"path": "static/css/monokai.css"},
}


# URL configuration matching Octopress structure
ARTICLE_URL = "{date:%Y}/{date:%m}/{date:%d}/{slug}.html"
ARTICLE_SAVE_AS = "{date:%Y}/{date:%m}/{date:%d}/{slug}.html"
CATEGORY_URL = "category/{slug}.html"
CATEGORY_SAVE_AS = "category/{slug}.html"
TAG_URL = "tag/{slug}.html"
TAG_SAVE_AS = "tag/{slug}.html"
AUTHOR_URL = "author/{slug}.html"
AUTHOR_SAVE_AS = "author/{slug}.html"

# Markdown configuration
MARKDOWN = {
    "extension_configs": {
        "markdown.extensions.codehilite": {
            "linenums": True,
            "css_class": "highlight",
        },
        "markdown.extensions.extra": {},
        "markdown.extensions.meta": {},
        "markdown.extensions.toc": {},
        "markdown.extensions.tables": {},
        "markdown.extensions.fenced_code": {},
    },
    "output_format": "html5",
}

# Code highlighting
PYGMENTS_STYLE = "monokai"

# Plugins
PLUGIN_PATHS = ["pelican_plugins"]
PLUGINS = []

# Content processing
READERS = {}

# Optional: Enable typographic enhancements
TYPOGRIFY = False

# Article settings
SHOW_ARTICLE_AUTHOR = True
SHOW_DATE_MODIFIED = True

# RELATIVE URL SETTING
# Set to True for local development preview
# Set to False for production (GitHub Pages)
# This is now controlled by SITEURL being empty or set
