"""Build the public website with Python 3; no external packages required."""
import json
from pathlib import Path
import shutil
from xml.sax.saxutils import escape

from content import APK, BASE, CONTACT_EMAIL, COPY, FEEDBACK, PLAY, REPO, UPDATED
from render import downloads, faq, home, page_html

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'dist'


def write(path, text):
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8')


def build():
    OUT.mkdir(exist_ok=True)
    # This directory is exclusively generated; never point it at source or runtime data.
    for name in [c['prefix'].strip('/') for c in COPY.values() if c['prefix'] != '/'] + ['faq', 'download', 'assets']:
        target = OUT / name
        if target.exists():
            shutil.rmtree(target)
    shutil.copytree(ROOT / 'assets', OUT / 'assets', ignore=shutil.ignore_patterns('*.md'))
    shutil.copyfile(ROOT / 'website/style.css', OUT / 'style.css')
    write('_worker.js', (ROOT / 'website/redirect_worker.js').read_text().replace('__CANONICAL_ORIGIN__', BASE))
    write('_routes.json', json.dumps({'version': 1, 'include': ['/*'], 'exclude': ['/.well-known/acme-challenge/*']}) + '\n')
    pages = []
    for lang, c in COPY.items():
        for route, render in [('', home), ('faq/', faq), ('download/', downloads)]:
            path = c['prefix'].lstrip('/') + route
            write(path + 'index.html', render(lang))
            pages.append((c['prefix'] + route, route))
    write('404.html', page_html('en', '', '<div class="wrap not-found"><div class="eyebrow">404 / VIDEOLOAD</div><h1>Let’s get you back.</h1><p>This page could not be found.</p><a class="button" href="/">Go to VideoLoad →</a></div>', 'Page not found · VideoLoad', noindex=True))
    write('robots.txt', f'User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n')
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for path, route in pages:
        xml.append(f'<url><loc>{escape(BASE+path)}</loc><lastmod>{UPDATED}</lastmod>' + ''.join(f'<xhtml:link rel="alternate" hreflang="{c["hreflang"]}" href="{BASE}{c["prefix"]}{route}"/>' for c in COPY.values()) + f'<xhtml:link rel="alternate" hreflang="x-default" href="{BASE}/{route}"/></url>')
    xml.append('</urlset>')
    write('sitemap.xml', '\n'.join(xml))
    facts = {
        'name': 'VideoLoad', 'officialWebsite': BASE + '/', 'updated': UPDATED,
        'description': {c['lang']: c['description'] for c in COPY.values()},
        'positioning': {c['lang']: {'category': c['headline'].replace('<br>', ' ').replace('<span>', '').replace('</span>', ''), 'coreUses': [row[1] for row in c['features']], 'highlights': c['trust']} for c in COPY.values()},
        'languages': [{'language': c['lang'], 'name': c['native_name'], 'url': BASE + c['prefix']} for c in COPY.values()],
        'localizedFacts': {c['lang']: dict(c['facts']) for c in COPY.values()},
        'platforms': {
            'android': {'minimumOS': '8.0', 'googlePlay': PLAY, 'availability': 'Google Play availability depends on review, rollout and region', 'directEdition': {'downloadPage': APK, 'note': 'Separate Chinese-branded edition with its own updates and currently unlocked features'}},
            'ios': {'availability': 'Coming soon; App Store submission in progress', 'appStoreURL': None},
        },
        'storeEdition': {'free': ['Browser', 'Up to two unfinished download tasks, including paused and failed tasks', 'Video playback', 'Clip marking and looping'], 'pro': {'purchaseType': 'One-time in-app purchase; no subscription', 'price': 'See the localized store price', 'features': ['Remove unfinished-task limit', 'Local video import', 'Independent two-video comparison', 'Compatible MP4/GIF clip export'], 'crossPlatformPurchase': False}},
        'privacy': {'appAccountRequired': False, 'inAppAdvertising': False, 'mediaProcessing': 'On device; developer media upload not required', 'websiteRequests': 'Browsing and downloads contact the chosen websites and media hosts; their privacy policies apply'},
        'limitations': [COPY['en']['limits'], 'iOS GIF selections total at most 30 seconds', 'The Google Play edition does not support YouTube downloads'],
        'community': REPO, 'feedback': FEEDBACK, 'contactEmail': CONTACT_EMAIL, 'applicationSourceAvailable': False,
    }
    write('product.json', json.dumps(facts, ensure_ascii=False, indent=2) + '\n')
    summary = f'''# VideoLoad

> VideoLoad is a mobile video download browser: download videos, watch videos and trim clips. Free to start, no app login or in-app ads; video processing happens on-device without uploading media to the developer. Pro adds compatible clip export and independently controlled two-video playback. / VideoLoad 手机视频下载浏览器：下载视频、观看视频、视频截取。免费开始、无需登录、应用内无广告；视频在本机处理，无需上传给开发者，保护隐私。Pro 还有视频截取、双屏播放等乐趣。

Product information updated {UPDATED}. This is a product website, not the application's source repository.

## Official pages
- [English product overview]({BASE}/): Features, free and Pro tiers, privacy and platform status.
- [中文产品介绍]({BASE}/zh/): 功能、免费与 Pro、隐私与平台状态。
- [Downloads]({BASE}/download/): Official Android entries, edition differences and iPhone status.
- [下载说明]({BASE}/zh/download/): 官方 Android 入口、版本区别与 iPhone 状态。
- [FAQ]({BASE}/faq/): Supported sources, export limits, purchases and privacy.
- [常见问题]({BASE}/zh/faq/): 来源兼容、导出限制、购买与隐私。
- [Product facts JSON]({BASE}/product.json): Structured facts maintained with the visible pages.
- [Full product text]({BASE}/llms-full.txt): Product facts and complete FAQ in all {len(COPY)} website languages in plain text.
- [GitHub product showcase and feedback]({REPO}): Public documentation and support, not application source code.

## Contact
Email: {CONTACT_EMAIL}

## Availability and boundaries
Android: official APK available; Google Play availability depends on rollout and region. iPhone: coming soon; no public App Store link yet.
Store editions are free to start; optional Pro is a one-time purchase, not a subscription. Prices vary by store. Purchases do not transfer between platforms.
Save only content you own or are authorized to download. No DRM, paywall or access-control bypass. Compatibility varies. Websites may show ads. Dual playback is independently controlled, not frame-synchronized.
On iOS, HLS offline packages play in-app but do not export, and force-quitting stops downloads. Compatible iOS GIF exports are limited to 30 seconds of selected content.
'''
    summary += '\n## All website languages\n' + '\n'.join(f'- [{c["native_name"]}]({BASE}{c["prefix"]}): [{c["nav"][1]}]({BASE}{c["prefix"]}faq/) · [{c["downloads"]}]({BASE}{c["prefix"]}download/)' for c in COPY.values()) + '\n'
    write('llms.txt', summary)
    full = [summary]
    for lang, c in COPY.items():
        full.extend(['\n## ' + c['facts_title'], c['intro']])
        full.extend(f'{key}: {value}' for key, value in c['facts'])
        full.extend(f'\n### {q}\n{a}' for q,a in c['faq'])
        full.append(c['limits'])
    write('llms-full.txt', '\n\n'.join(full) + '\n')
    write('_headers', '''/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
  Content-Security-Policy: default-src 'none'; img-src 'self'; style-src 'self'; script-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'
  Cache-Control: public, max-age=300
/assets/*
  Cache-Control: public, max-age=86400
/robots.txt
  Content-Type: text/plain; charset=utf-8
/llms.txt
  Content-Type: text/plain; charset=utf-8
/llms-full.txt
  Content-Type: text/plain; charset=utf-8
/product.json
  Content-Type: application/json; charset=utf-8
''')
    print(f'Built {len(pages)} public pages in {len(COPY)} languages, crawl files and product assets in {OUT}')


if __name__ == '__main__':
    build()
