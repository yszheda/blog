#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

# Production configuration for GitHub Pages deployment
AUTHOR = "Galoisplusplus"
SITENAME = "Galoisplusplus"

# GitHub Pages URL - uncomment and set your actual URL
# For GitHub Pages project site
SITEURL = "https://yszheda.github.io/blog"

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

# Theme settings - Using Pelican built-in notmyidea theme (has CSS)
THEME = "notmyidea"

# Static files - only include necessary paths
STATIC_PATHS = [
    "static/images",
    "static/downloads",
    "static/css",
]

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

# For GitHub Pages deployment
RELATIVE_URLS = True
