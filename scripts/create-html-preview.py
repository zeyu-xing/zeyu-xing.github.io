"""Export the built Home and Research pages as one offline HTML preview."""
import argparse
import base64
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument('--site', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()

home = (args.site / 'index.html').read_text()
research = (args.site / 'research/index.html').read_text()

def extract(pattern, source):
    match = re.search(pattern, source, re.S)
    if not match:
        raise ValueError('The built page does not match the academic layout.')
    return match.group(1)

def local_navigation(source):
    return source.replace('href="/research/"', 'href="#research"').replace('href="/"', 'href="#home"')

head = extract(r'<head>(.*?)</head>', home)
head = re.sub(r'\s*<link\b[^>]*>', '', head)
head = re.sub(r'\s*<script\b[^>]*>.*?</script>', '', head, flags=re.S)
head = re.sub(r'<title>.*?</title>', '<title>Zeyu Xing — Homepage Preview</title>', head, flags=re.S)
css = (args.site / 'assets/css/academic.css').read_text()
contact = (args.site / 'assets/js/contact.js').read_text()
favicon = base64.b64encode((args.site / 'images/favicon.svg').read_bytes()).decode()
header = local_navigation(extract(r'(<header class="site-header">.*?</header>)', home))
home_content = local_navigation(extract(r'<main\b[^>]*>(.*?)</main>', home))
research_content = local_navigation(extract(r'<main\b[^>]*>(.*?)</main>', research))

navigation = """
(() => {
  const pages = [...document.querySelectorAll('[data-preview-page]')];
  function showPage() {
    if (location.hash && !['#home', '#research'].includes(location.hash)) return;
    const name = location.hash === '#research' ? 'research' : 'home';
    for (const page of pages) page.hidden = page.dataset.previewPage !== name;
    for (const link of document.querySelectorAll('nav a')) {
      if (link.hash === '#' + name) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    }
    document.title = (name === 'research' ? 'Research | ' : '') + 'Zeyu Xing';
    window.scrollTo(0, 0);
  }
  window.addEventListener('hashchange', showPage);
  showPage();
})();
"""

preview = f'''<!doctype html>
<html lang="en-US">
<head>{head}
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,{favicon}">
<style>{css}\n[hidden] {{ display: none !important; }}</style>
</head>
<body>
  <a class="skip-link" href="#content">Skip to content</a>
  <div class="academic-shell">
    {header}
    <div id="content">
      <main class="home-page" data-preview-page="home">{home_content}</main>
      <main class="research-page" data-preview-page="research" hidden>{research_content}</main>
    </div>
  </div>
<script>{contact}\n{navigation}</script>
</body>
</html>
'''
assert 'src="/' not in preview and 'href="/' not in preview
assert '<footer' not in preview
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(preview)
print('Created standalone HTML preview:', args.output.name)
