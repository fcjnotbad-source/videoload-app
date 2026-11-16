"""Validate the rendered pages as crawlers see them, without JavaScript."""
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

from content import APK, APPSTORE, BASE, CONTACT_EMAIL, COPY, GOOGLE_SITE_VERIFICATION, LOCALES, REPO
from promo import METADATA, media_url, video_id, watch_url

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
        for page in ('', 'faq/', 'download/', 'video/'):
            path = copy['prefix'] + page
            html = resolve(path).read_text(encoding='utf-8')
            doc = Document(html)
            documents[path] = doc
            verification = [attr.get('content') for tag, attr in doc.tags if tag == 'meta' and attr.get('name') == 'google-site-verification']
            assert verification == [GOOGLE_SITE_VERIFICATION], path
            assert f'<meta name="google-site-verification" content="{GOOGLE_SITE_VERIFICATION}">' in html.split('</head>', 1)[0], path
            assert sum(tag == 'h1' for tag, _ in doc.tags) == 1, path
            assert any(tag == 'main' for tag, _ in doc.tags), path
            assert any(tag == 'link' and attr.get('rel') == 'stylesheet' and attr.get('href', '').startswith('/style.css?v=') for tag, attr in doc.tags), path
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
            if page in ('', 'video/'):
                videos = [attr for tag, attr in doc.tags if tag == 'video']
                assert len(videos) == 1, path
                video = videos[0]
                assert 'controls' in video and 'playsinline' in video and 'autoplay' not in video, path
                assert video.get('preload') == 'metadata', path
                assert video.get('poster') == '/assets/promo/videoload-overview-poster.jpg', path
                assert video.get('lang') == 'en', path
                assert resolve(video['poster']).is_file(), path
                assert any(tag == 'source' and attr.get('src') == media_url('videoload-overview-en.mp4') and attr.get('type') == 'video/mp4' for tag, attr in doc.tags), path
                assert any(tag == 'track' and attr.get('kind') == 'captions' and attr.get('srclang') == 'en' and attr.get('src') == media_url('videoload-overview-en.vtt') for tag, attr in doc.tags), path
                if page == '':
                    assert any(tag == 'section' and attr.get('id') == 'film' for tag, attr in doc.tags), path
                    assert any(tag == 'img' and attr.get('src') == '/assets/screenshots/compare-portraits.png' for tag, attr in doc.tags), path
                else:
                    assert doc.tags.index(next(item for item in doc.tags if item[0] == 'video')) < doc.tags.index(next(item for item in doc.tags if item[0] == 'h2')), path
                    assert any(tag == 'meta' and attr.get('property') == 'og:image' and attr.get('content') == BASE + '/assets/promo/videoload-overview-poster.jpg' for tag, attr in doc.tags), path
            graph = doc.schemas[0]['@graph']
            description = next(attr['content'] for tag, attr in doc.tags if tag == 'meta' and attr.get('name') == 'description')
            assert description not in descriptions, path
            descriptions.add(description)
            web = next(item for item in graph if item['@type'] == 'WebPage')
            assert web['description'] == description
            app = next(item for item in graph if item['@type'] == 'SoftwareApplication')
            assert app['downloadUrl'] == APK, path
            assert 'offers' not in app and 'aggregateRating' not in app and 'review' not in app
            assert app['operatingSystem'] == 'Android 8.0+; iOS 17.0+', path
            assert APPSTORE in app['sameAs'], path
            if page in ('', 'download/'):
                assert any(tag == 'a' and attr.get('href') == APPSTORE for tag, attr in doc.tags), path
            film_objects = [item for item in graph if item['@type'] == 'VideoObject']
            if page in ('', 'video/') and METADATA.is_file():
                metadata = json.loads(METADATA.read_text())
                assert len(film_objects) == 1, path
                film = film_objects[0]
                assert film['@id'] == video_id(copy) and web['video'] == {'@id': video_id(copy)}, path
                assert film['name'] == copy['video_page_title'] and film['description'] == copy['video_page_description'], path
                assert film['duration'] == f'PT{float(metadata["durationSeconds"]):g}S', path
                assert film['uploadDate'] == metadata['uploadDate'], path
                assert film['contentUrl'] == BASE + media_url('videoload-overview-en.mp4'), path
                assert film['thumbnailUrl'] == BASE + '/assets/promo/videoload-overview-poster.jpg', path
                assert film['inLanguage'] == 'en' and film['caption']['inLanguage'] == 'en', path
                assert film['url'] == watch_url(copy) and film['mainEntityOfPage'] == {'@id': watch_url(copy) + '#webpage'}, path
                if page == 'video/':
                    assert web['mainEntity'] == {'@id': film['@id']}, path
                    for paragraph in film['transcript'].split('\n\n'):
                        assert paragraph in ' '.join(doc.text), path
            elif page != '':
                assert not film_objects and 'video' not in web, path
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
    assert 'Allow: /' in robots and 'Disallow: /' not in robots and BASE + '/sitemap.xml' in robots and BASE + '/video-sitemap.xml' in robots
    facts = json.loads((OUT / 'product.json').read_text())
    assert facts['platforms']['ios']['appStoreURL'] == APPSTORE
    assert facts['platforms']['ios']['minimumOS'] == '17.0'
    video_map = ET.parse(OUT / 'video-sitemap.xml')
    ns = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9', 'v': 'http://www.google.com/schemas/sitemap-video/1.1'}
    entries = video_map.findall('s:url', ns)
    expected_watch = {watch_url(c): c for c in COPY.values()}
    assert len(entries) == len(COPY)
    assert {entry.findtext('s:loc', namespaces=ns) for entry in entries} == set(expected_watch)
    metadata = json.loads(METADATA.read_text())
    for entry in entries:
        c = expected_watch[entry.findtext('s:loc', namespaces=ns)]
        assert entry.findtext('v:video/v:content_loc', namespaces=ns) == BASE + media_url('videoload-overview-en.mp4')
        assert entry.findtext('v:video/v:thumbnail_loc', namespaces=ns) == BASE + '/assets/promo/videoload-overview-poster.jpg'
        assert entry.findtext('v:video/v:title', namespaces=ns) == c['video_page_title']
        assert 0 < len(c['video_page_title']) <= 100
        assert 0 < len(c['video_page_description']) <= 2048
        assert entry.findtext('v:video/v:description', namespaces=ns) == c['video_page_description']
        assert float(entry.findtext('v:video/v:duration', namespaces=ns)) == metadata['durationSeconds']
        assert entry.findtext('v:video/v:publication_date', namespaces=ns) == metadata['uploadDate']
    assert facts['promotionalVideo']['watchPage'] == BASE + '/video/'
    assert set(facts['promotionalVideo']['localizedWatchPages'].values()) == set(expected_watch)
    assert facts['officialWebsite'] == BASE + '/'
    assert set(facts['positioning']) == {c['lang'] for c in COPY.values()}
    assert facts['community'] == REPO
    assert facts['contactEmail'] == CONTACT_EMAIL
    assert facts['officialWebsiteEdition']['price'] == 'Free'
    assert len(facts['languages']) == len(LOCALES)
    assert set(facts['description']) == {c['lang'] for c in COPY.values()}
    assert {x['url'] for x in facts['languages']} == {BASE + c['prefix'] for c in COPY.values()}
    for path, route_doc in documents.items():
        assert BASE + path in (OUT / 'llms.txt').read_text(), path
    assert 'noindex' in (OUT / '404.html').read_text()
    routing = json.loads((OUT / '_routes.json').read_text())
    assert '/.well-known/acme-challenge/*' in routing['exclude']
    assert '__CANONICAL_ORIGIN__' not in (OUT / '_worker.js').read_text()
    assert '__MEDIA_SIZES__' not in (OUT / '_worker.js').read_text()
    film_bytes = (OUT / 'assets/promo/videoload-overview-en.mp4').stat().st_size
    assert f'"/assets/promo/videoload-overview-en.mp4": {film_bytes}' in (OUT / '_worker.js').read_text()
    assert BASE in (OUT / '_worker.js').read_text()
    assert "media-src 'self'" in (OUT / '_headers').read_text()
    promo = OUT / 'assets/promo'
    expected_promo = {'videoload-overview-en.mp4', 'videoload-overview-en.vtt', 'videoload-overview-en.srt', 'videoload-overview-poster.jpg', 'transcript.en.txt', 'metadata.json'}
    assert promo.is_dir(), 'Product film assets are missing'
    assert {p.name for p in promo.iterdir() if p.is_file()} <= expected_promo, 'Only final public film assets belong in the promotional media folder'
    assert (promo / 'videoload-overview-en.mp4').stat().st_size <= 25 * 1024 * 1024, 'Film exceeds Pages asset limit'
    assert (promo / 'videoload-overview-en.vtt').read_text().startswith('WEBVTT')
    assert ' --> ' in (promo / 'videoload-overview-en.srt').read_text()
    assert len((promo / 'transcript.en.txt').read_text().strip()) > 40
    for p in OUT.rglob('*'):
        if p.is_file():
            assert p.suffix in {'.html', '.css', '.json', '.xml', '.txt', '.png', '.jpg', '.mp4', '.vtt', '.srt', ''} or p.name == '_worker.js', p
            if p.suffix not in {'.png', '.jpg', '.mp4'}:
                text = p.read_text()
                assert 'cfat_' not in text and 'PRIVATE KEY' not in text and '/Users/' not in text, p
    print(f'PASS: {len(documents)} HTML pages in {len(COPY)} languages; unique titles, headings, canonicals and reciprocal hreflang; {link_count} internal links/assets; visible FAQ/schema agreement; sitemap/robots; product facts; public artifact allowlist.')


if __name__ == '__main__':
    check()
