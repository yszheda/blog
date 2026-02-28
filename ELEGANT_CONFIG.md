# Elegant Theme Configuration

# Add to your pelicanconf.py:

DIRECT_TEMPLATES = (('index', 'tags', 'categories', 'authors', 'archives', 'search'))
PAGINATION_PATTERNS = (
    (1, '{base_url}/', '{base_url}/'),
    (2, '{base_url}/page/{number}/', '{base_url}/page/{number}/'),
)

# Enable summary on index pages (shows first paragraph)
# PAGINATED_TEMPLATES = (('index', 'tags', 'categories', 'authors', 'archives'),)

# Favicon
FAVICON = 'images/favicon.png'

# Sidebar
ABOUT_ME = ''
LINKS = (('GitHub', 'https://github.com/yszheda'),)
SOCIAL = (('Twitter', 'twitter.com/yszheda'),)

# Article meta
SHOW_ARTICLE_AUTHOR = True
SHOW_DATE_MODIFIED = True

# Colors and styling
THEME_COLOR = '#34495e'
