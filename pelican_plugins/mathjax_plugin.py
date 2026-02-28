"""Pelican plugin to inject MathJax into pages with math content."""

from pelican import signals
import re


def inject_mathjax(content):
    """Inject MathJax CDN into HTML content if math delimiters are found"""
    if isinstance(content, str):
        # Check if content has LaTeX math patterns
        # Patterns like $...$, $$...$$, \[...\], \(...\)
        math_patterns = [
            r"\$\$[^$]+\$\$",  # $$...$$ display math
            r"(?<!\$)\$[^$]+?\$(?!\$)",  # $...$ inline math (no double dollar)
            r"\\?\[.*?\\?\]",  # \[...\] display math
            r"\\?\(.*?\\?\)",  # \(...\) inline math
        ]

        has_math = any(re.search(pattern, content) for pattern in math_patterns)

        if has_math:
            mathjax_script = """
<script type="text/x-mathjax-config">
  MathJax.Hub.Config({
    tex2jax: {
      inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
      displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
      processEscapes: true,
      processEnvironments: true,
      skipTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code']
    },
    "HTML-CSS": {
      linebreaks: { automatic: true, width: "container" }
    }
  });
</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@2.7.9/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>
"""
            # Insert before </head>
            content = content.replace("</head>", mathjax_script + "</head>")

    return content


def content_object_init(instance):
    """Hook to modify content object before it's processed"""
    if hasattr(instance, "_content"):
        instance._content = inject_mathjax(instance._content)


def register():
    """Register plugin signals"""
    signals.content_object_init.connect(content_object_init)
