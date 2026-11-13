"""Semantic, script-independent page rendering."""
import json
from html import escape as e

from content import APK, BASE, CONTACT_EMAIL, COPY, DEMO, FEEDBACK, PLAY, POLICY, REPO, UPDATED
from promo import VIDEO_ID, video_schema


def button(label, url, secondary=False, small=False):
    classes = 'button' + (' secondary' if secondary else '') + (' small' if small else '')
    return f'<a class="{classes}" href="{e(url)}">{e(label)}<span class="arrow" aria-hidden="true">↗</span></a>'


def description(c, page):
    return c.get({'faq/': 'faq_description', 'download/': 'download_description'}.get(page, 'description'))


def schemas(lang, page):
    c = COPY[lang]
    url = BASE + c['prefix'] + page
    data = [
        {'@type': 'WebSite', '@id': BASE + '/#website', 'url': BASE + '/', 'name': 'VideoLoad', 'inLanguage': [locale['lang'] for locale in COPY.values()]},
        {'@type': 'SoftwareApplication', '@id': BASE + '/#app', 'name': 'VideoLoad', 'url': BASE + '/', 'applicationCategory': 'MultimediaApplication', 'operatingSystem': 'Android 8.0+; iOS (coming soon)', 'description': c['description'], 'inLanguage': c['lang'], 'featureList': [feature[1] + ': ' + feature[2] for feature in c['features']], 'image': BASE + '/assets/app-icon.png', 'screenshot': BASE + '/assets/screenshots/player.png', 'sameAs': [REPO], 'downloadUrl': APK, 'softwareHelp': {'@type': 'WebPage', 'url': BASE + c['prefix'] + 'faq/'}},
        {'@type': 'WebPage', '@id': url + '#webpage', 'url': url, 'name': c['title'] if not page else (c['faq_heading'] if page == 'faq/' else c['downloads']) + ' · VideoLoad', 'description': description(c,page), 'inLanguage': c['lang'], 'isPartOf': {'@id': BASE + '/#website'}, 'about': {'@id': BASE + '/#app'}, 'dateModified': UPDATED},
    ]
    if page == '':
        video = video_schema(c)
        if video:
            data.append(video)
            data[2]['video'] = {'@id': VIDEO_ID}
    if page == 'faq/':
        data.append({'@type': 'FAQPage', '@id': url + '#faq', 'inLanguage': c['lang'], 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in c['faq']]})
    if page:
        data.append({'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': c['home'], 'item': BASE + c['prefix']}, {'@type': 'ListItem', 'position': 2, 'name': c['nav'][1] if page == 'faq/' else c['downloads'], 'item': url}]})
    return json.dumps({'@context': 'https://schema.org', '@graph': data}, ensure_ascii=False).replace('<', '\\u003c')


def language_menu(c, page):
    items = []
    for locale in COPY.values():
        current = ' aria-current="page"' if locale['locale_key'] == c['locale_key'] else ''
        items.append(f'<a href="{locale["prefix"]}{page}" lang="{locale["lang"]}" hreflang="{locale["hreflang"]}" dir="auto"{current}>{e(locale["native_name"])}</a>')
    return f'<details class="language-menu"><summary aria-label="{e(c["language_label"])}"><span aria-hidden="true">◎</span> <bdi>{e(c["native_name"])}</bdi><span aria-hidden="true">⌄</span></summary><div class="language-options" dir="ltr">{"".join(items)}</div></details>'


def header(c, page):
    return f'''<a class="skip" href="#main">{c['skip']}</a>
<header class="site-header"><div class="wrap header-inner">
<a class="brand" href="{c['prefix']}" aria-label="VideoLoad · {c['home']}" dir="ltr"><img src="/assets/app-icon.png" width="40" height="40" alt="">VideoLoad</a>
<nav class="nav" aria-label="{e(c['navigation_label'])}"><a class="features-link" href="{c['prefix']}#features">{c['nav'][0]}</a><a class="faq-link" href="{c['prefix']}faq/">{c['nav'][1]}</a><a class="github-link" href="{REPO}">GitHub ↗</a>{language_menu(c,page)}<span class="header-cta">{button(c['nav'][3], c['prefix']+'download/', small=True)}</span></nav>
</div></header>'''


def footer(c):
    ios_policy = 'privacy-zh.html' if c['locale_key'] in {'zh', 'zh-Hant'} else 'privacy.html'
    return f'''<footer class="site-footer"><div class="wrap"><div class="footer-top"><div class="footer-brand">{c['footer']}</div><nav class="footer-links" aria-label="{e(c['footer_navigation'])}"><a href="{c['prefix']}download/">{c['downloads']}</a><a href="{c['prefix']}faq/">{c['nav'][1]}</a><a href="{REPO}">GitHub ↗</a><a href="mailto:{CONTACT_EMAIL}" dir="ltr">{CONTACT_EMAIL}</a><a href="{POLICY}privacy.html">Android {c['privacy']}</a><a href="{POLICY}ios/{ios_policy}">iOS {c['privacy']}</a></nav></div><p class="fineprint">{c['limits']}</p><p class="updated">{c['updated']} © 2026 VideoLoad.</p></div></footer>'''


def page_html(lang, page, body, title=None, noindex=False):
    c = COPY[lang]
    canonical = BASE + c['prefix'] + page
    title = title or c['title']
    desc = description(c,page)
    robots = 'noindex, follow' if noindex else 'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1'
    alternates = ''.join(f'<link rel="alternate" hreflang="{locale["hreflang"]}" href="{BASE}{locale["prefix"]}{page}">' for locale in COPY.values())
    alternates += f'<link rel="alternate" hreflang="x-default" href="{BASE}/{page}">'
    return f'''<!doctype html>
<html lang="{c['lang']}" dir="{c['direction']}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><meta name="robots" content="{robots}">
<link rel="canonical" href="{canonical}">{alternates}
<meta property="og:type" content="website"><meta property="og:site_name" content="VideoLoad"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{BASE}/assets/screenshots/player.png"><meta property="og:image:alt" content="{e(c['alt_player'])}"><meta property="og:locale" content="{c['og_locale']}"><meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#faf9f6"><link rel="icon" href="/assets/app-icon.png" type="image/png"><link rel="stylesheet" href="/style.css"><link rel="alternate" type="text/plain" title="{e(c['machine_summary_label'])}" href="/llms.txt"><link rel="alternate" type="application/json" title="{e(c['product_facts_label'])}" href="/product.json">
<script type="application/ld+json">{schemas(lang, page)}</script></head><body>{header(c,page)}<main id="main">{body}</main>{footer(c)}</body></html>'''


def faq_list(c, limit=None, opened=False, indices=None):
    questions = [c['faq'][i] for i in indices] if indices is not None else c['faq'][:limit]
    return '<div class="faq-list">' + ''.join(f'<details{" open" if opened else ""}><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q,a in questions) + '</div>'


def stores(c):
    rows = []
    for platform, name, note, label, url in c['store']:
        action = button(label, url) if url else f'<span class="coming">{e(label)}</span>'
        rows.append(f'<div class="store-row"><div><div class="platform">{platform}</div><h3>{name}</h3></div><div class="store-detail">{note}</div>{action}</div>')
    return '<div class="store-list">' + ''.join(rows) + '</div>'


def download_section(c, help_link=True):
    help_html = f'<a class="download-help" href="{c["prefix"]}download/">{c["download_help"]} →</a>' if help_link else ''
    return f'<section class="download-section" id="download"><div class="wrap"><h2>{c["download_title"]}</h2><p class="lead">{c["download_intro"]}</p>{stores(c)}{help_html}</div></section>'


def promo_section(c):
    return f'''<section class="film-section" id="film" aria-labelledby="film-title"><header class="film-heading"><div><div class="eyebrow">VIDEOLOAD / FILM</div><h2 id="film-title">{e(c['promo_title'])}</h2></div><p id="film-note">{e(c['promo_note'])}</p></header><div class="film-player"><video width="1920" height="1080" controls playsinline preload="metadata" poster="/assets/promo/videoload-overview-poster.jpg" aria-labelledby="film-title" aria-describedby="film-note" lang="en"><source src="/assets/promo/videoload-overview-en.mp4" type="video/mp4"><track kind="captions" srclang="en" label="English" src="/assets/promo/videoload-overview-en.vtt"><p><a href="/assets/promo/videoload-overview-en.mp4">{e(c['promo_title'])} · MP4</a></p></video></div><div class="film-links"><a class="text-link" href="/assets/promo/transcript.en.txt">{e(c['promo_transcript_label'])} ↗</a><a class="text-link film-download" href="/assets/promo/videoload-overview-en.mp4" download>MP4 ↓</a></div></section>'''


def home(lang):
    c = COPY[lang]
    features = ''.join(f'<article class="feature"><span class="number">{n}</span><h3>{title}</h3><p>{text}</p></article>' for n,title,text in c['features'])
    facts = ''.join(f'<div class="fact-row"><dt>{k}</dt><dd>{v}</dd></div>' for k,v in c['facts'])
    body = f'''<div class="wrap"><section class="hero" aria-labelledby="hero-title"><div><div class="eyebrow">{c['eyebrow']}</div><h1 id="hero-title">{c['headline']}</h1><p class="lead">{c['intro']}</p><div class="actions">{button(c['cta'],c['prefix']+'download/')}{button(c['secondary'],'#features',secondary=True)}</div><p class="trust">{c['trust']}</p></div><figure class="hero-visual"><div class="screen"><img src="/assets/screenshots/player.png" width="1440" height="662" fetchpriority="high" alt="{e(c['alt_player'])}"></div><figcaption><strong>{c['caption']}</strong><p>{c['caption_detail']}</p><p class="preview-note">{c['preview']}</p></figcaption></figure></section><p class="platform-line">{c['platform']}</p>
{promo_section(c)}
<section class="section" id="features"><div class="section-head"><div><div class="eyebrow">{c['section_label']}</div><h2>{c['section_title']}</h2></div></div><div class="feature-list">{features}</div></section>
<section class="gallery-section"><h2>{c['gallery_title']}</h2><div class="gallery"><figure><div class="phone"><img src="/assets/screenshots/library.png" width="662" height="1440" loading="lazy" alt="{e(c['alt_library'])}"></div><figcaption>{c['library']}</figcaption></figure><figure><div class="phone"><img src="/assets/screenshots/compare.png" width="662" height="1440" loading="lazy" alt="{e(c['alt_compare'])}"></div><figcaption>{c['compare']}</figcaption></figure></div><p class="gallery-note">{c['gallery_note']}</p></section>
<section class="section facts"><div><div class="eyebrow">{c['facts_label']}</div><h2>{c['facts_title']}</h2></div><dl class="fact-table">{facts}</dl></section></div>
{download_section(c)}
<div class="wrap"><section class="section"><div class="section-head"><h2>{c['faq_title']}</h2></div>{faq_list(c,indices=[3,4,6])}<p class="faq-more"><a class="text-link" href="{c['prefix']}faq/">{c['faq_more']} →</a></p></section>
<section class="feedback"><div><h2>{c['feedback_title']}</h2><p>{c['feedback_text']}</p></div><div><div class="actions">{button(c['feedback_cta'],FEEDBACK)}{button(c['github_cta'],REPO,secondary=True)}</div><p class="note">{c['feedback_note']}</p><p class="contact-email"><a href="mailto:{CONTACT_EMAIL}" dir="ltr">{CONTACT_EMAIL}</a></p></div></section></div>'''
    return page_html(lang,'',body)


def faq(lang):
    c = COPY[lang]
    body = f'''<div class="wrap"><header class="page-intro"><p class="breadcrumb"><a href="{c['prefix']}">{c['home']}</a> / {c['nav'][1]}</p><div class="eyebrow">VIDEOLOAD / {c['nav'][1]}</div><h1>{c['faq_heading']}</h1><p class="lead">{c['faq_intro']}</p></header><section class="content-section">{faq_list(c,opened=True)}<div class="actions">{button(c['feedback_cta'],FEEDBACK)}{button(c['cta'],c['prefix']+'download/',secondary=True)}</div></section></div>'''
    return page_html(lang,'faq/',body,c['nav'][1]+' · VideoLoad')


def downloads(lang):
    c = COPY[lang]
    help_html = ''.join('<h2>' + e(section['title']) + '</h2>' + ''.join('<p>' + e(text) + '</p>' for text in section['paragraphs']) for section in c['download_sections'])
    demo = DEMO.replace('.html','-zh.html') if lang in {'zh', 'zh-Hant'} else DEMO
    help_html += f'<p><a href="{demo}">{e(c["demo_link"])} ↗</a></p>'
    body = download_section(c,False) + f'<div class="wrap"><section class="content-section prose">{help_html}<p><a href="{c["prefix"]}faq/">{c["faq_more"]} →</a> · <a href="{FEEDBACK}">{c["feedback_cta"]} ↗</a></p></section></div>'
    # Every page has an H1; the download section's visual heading becomes the page title.
    body = body.replace('<h2>', '<h1>', 1).replace('</h2>', '</h1>', 1)
    return page_html(lang,'download/',body,c['downloads']+' · VideoLoad')
