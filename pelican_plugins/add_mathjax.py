"""Pelican plugin: Add MathJax to articles page content."""

from pelican import signals
from bs4 import BeautifulSoup


def inject_mathjax(content):
    """Inject MathJax into HTML content."""
    if not hasattr(content, '_content'):
        return content
    
    try:
        soup = BeautifulSoup(content._content, 'html.parser')
    except:
        return content
    
    # Check for LaTeX patterns
    html_content = content._content or ""
    has_latex = any(pattern in html_content 
                   for pattern in ['\(', '\)', '\[', '\]', '$$', '<code>'])
    
    if has_latex:
        mathjax_script = '''
<script type="text/x-mathjax-config">
  MathJax.Hub.Config({
    tex2jax: {
      inlineMath: [['$', '$'], ['\\(', '\\)']],
      displayMath: [['$$', '$$'], ['\\[', '\\]']],
      processEscapes: true
    }
  });
</script>
<script async src="https://cdn.jsdelivr.net/npm/mathjax@2.7.9/MathJax.js?config=TeX-MML-AM_CHTML"></script>
'''
        if soup.head:
            soup.head.append(BeautifulSoup(mathjax_script, 'html.parser'))
            content._content = str(soup)
    
    return content


def register():
    signals.content_object_init.connect(inject_mathjax)
