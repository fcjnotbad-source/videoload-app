"""Validate the rendered pages as crawlers see them, without JavaScript."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

from content import BASE, CONTACT_EMAIL, COPY, LOCALES, REPO

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'dist'


class Document(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.text = []
        self.schemas = []
        self.json_block = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if tag == 'script' and attrs.get('type') == 'application/ld+json':
            self.json_block = []

    def handle_endtag(self, tag):
        if tag == 'script' and self.json_block is not None:
            self.schemas.append(json.loads(''.join(self.json_block)))
            self.json_block = None

    def handle_data(self, text):
        if self.json_block is not None:
            self.json_block.append(text)
        else:
            self.text.append(text)


def resolve(path):
    target = OUT / path.lstrip('/')
    return target / 'index.html' if path.endswith('/') or not path else target


def check():
    documents = {}
    titles = set()
    descriptions = set()
    for lang, copy in COPY.items():
        for page in ('', 'faq/', 'download/'):
            path = copy['prefix'] + page
            html = resolve(path).read_text(encoding='utf-8')
            doc = Document(html)
            documents[path] = doc
            assert sum(tag == 'h1' for tag, _ in doc.tags) == 1, path
            assert any(tag == 'main' for tag, _ in doc.tags), path
            assert any(tag == 'html' and attr.get('lang') == copy['lang'] for tag, attr in doc.tags), path
            canonicals = [attr['href'] for tag, attr in doc.tags if tag == 'link' and attr.get('rel') == 'canonical']
            assert canonicals == [BASE + path], (path, canonicals)
            alternates = {attr.get('hreflang'): attr.get('href') for tag, attr in doc.tags if tag == 'link' and attr.get('hreflang')}
            expected_alternates = {c['hreflang']: BASE + c['prefix'] + page for c in COPY.values()}
            expected_alternates['x-default'] = BASE + '/' + page
            assert alternates == expected_alternates, path
            assert any(tag == 'meta' and attr.get('name') == 'robots' and attr.get('content', '').startswith('index,') for tag, attr in doc.tags), path
            assert REPO in html and 'issues/new/choose' in html, path
            assert f'mailto:{CONTACT_EMAIL}' in html, path
            assert any(tag == 'html' and attr.get('dir') == copy['direction'] for tag, attr in doc.tags), path
            language_links = [attr for tag, attr in doc.tags if tag == 'a' and attr.get('hreflang')]
            assert {a['href'] for a in language_links} == {c['prefix'] + page for c in COPY.values()}, path
            assert sum(a.get('aria-current') == 'page' for a in language_links) == 1, path
            assert all(not attr.get('src') and attr.get('type') == 'application/ld+json' for tag, attr in doc.tags if tag == 'script'), path
            assert all('alt' in attr and 'width' in attr and 'height' in attr for tag, attr in doc.tags if tag == 'img'), path
            assert len(doc.schemas) == 1, path
            graph = doc.schemas[0]['@graph']
            description = next(attr['content'] for tag, attr in doc.tags if tag == 'meta' and attr.get('name') == 'description')
            assert description not in descriptions, path
            descriptions.add(description)
            web = next(item for item in graph if item['@type'] == 'WebPage')
            assert web['description'] == description
            app = next(item for item in graph if item['@type'] == 'SoftwareApplication')
            assert 'offers' not in app and 'aggregateRating' not in app and 'review' not in app
            assert 'coming soon' in app['operatingSystem'] and 'apps.apple.com' not in html
            if page == 'faq/':
                faq = next(item for item in graph if item['@type'] == 'FAQPage')
                visible = ' '.join(doc.text)
                for item in faq['mainEntity']:
                    assert item['name'] in visible and item['acceptedAnswer']['text'] in visible, (path, item['name'])
                assert len(faq['mainEntity']) == len(copy['faq'])
            title = html.split('<title>', 1)[1].split('</title>', 1)[0]
            assert (lang, title) not in titles, title
            titles.add((lang, title))
    link_count = 0
    for route, doc in documents.items():
        for tag, attr in doc.tags:
            target = attr.get('href') if tag == 'a' else attr.get('src')
            if not target or urlsplit(target).scheme:
                continue
            parts = urlsplit(target)
            path = unquote(parts.path) or route
            file = resolve(path)
            assert file.is_file(), (route, target)
            if parts.fragment:
                linked = documents.get(path) or Document(file.read_text())
                assert any(a.get('id') == parts.fragment for _, a in linked.tags), (route, target)
            link_count += 1
    sitemap = ET.parse(OUT / 'sitemap.xml')
    locs = {node.text for node in sitemap.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}
    assert locs == {BASE + route for route in documents}
    robots = (OUT / 'robots.txt').read_text()
    assert 'Allow: /' in robots and 'Disallow: /' not in robots and BASE + '/sitemap.xml' in robots
    facts = json.loads((OUT / 'product.json').read_text())
    assert facts['platforms']['ios']['appStoreURL'] is None
    assert facts['community'] == REPO
    assert facts['contactEmail'] == CONTACT_EMAIL
    assert len(facts['languages']) == len(LOCALES)
    assert set(facts['description']) == {c['lang'] for c in COPY.values()}
    assert {x['url'] for x in facts['languages']} == {BASE + c['prefix'] for c in COPY.values()}
    for path, route_doc in documents.items():
        assert BASE + path in (OUT / 'llms.txt').read_text(), path
    assert 'noindex' in (OUT / '404.html').read_text()
    for p in OUT.rglob('*'):
        if p.is_file():
            assert p.suffix in {'.html', '.css', '.json', '.xml', '.txt', '.png', ''}, p
            if p.suffix != '.png':
                text = p.read_text()
                assert 'cfat_' not in text and 'PRIVATE KEY' not in text and '/Users/' not in text, p
    print(f'PASS: {len(documents)} HTML pages in {len(COPY)} languages; unique titles, headings, canonicals and reciprocal hreflang; {link_count} internal links/assets; visible FAQ/schema agreement; sitemap/robots; product facts; public artifact allowlist.')


if __name__ == '__main__':
    check()
