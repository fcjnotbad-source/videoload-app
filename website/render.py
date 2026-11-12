"""Semantic, script-independent page rendering."""
import json
from html import escape as e

from content import APK, BASE, COPY, DEMO, FEEDBACK, PLAY, POLICY, REPO, UPDATED


def button(label, url, secondary=False, small=False):
    classes = 'button' + (' secondary' if secondary else '') + (' small' if small else '')
    return f'<a class="{classes}" href="{e(url)}">{e(label)}<span class="arrow" aria-hidden="true">↗</span></a>'


def description(c, page):
    return c.get({'faq/': 'faq_description', 'download/': 'download_description'}.get(page, 'description'))


def schemas(lang, page):
    c = COPY[lang]
    url = BASE + c['prefix'] + page
    data = [
        {'@type': 'WebSite', '@id': BASE + '/#website', 'url': BASE + '/', 'name': 'VideoLoad', 'inLanguage': ['en', 'zh-CN']},
        {'@type': 'SoftwareApplication', '@id': BASE + '/#app', 'name': 'VideoLoad', 'url': BASE + '/', 'applicationCategory': 'MultimediaApplication', 'operatingSystem': 'Android 8.0+; iOS (coming soon)', 'description': COPY['en']['description'], 'featureList': ['Video browser and local library', 'Clip marking and looping', 'Optional one-time Pro for local import, independent two-video comparison and compatible MP4/GIF export'], 'image': BASE + '/assets/app-icon.png', 'screenshot': BASE + '/assets/screenshots/player.png', 'sameAs': [REPO], 'downloadUrl': PLAY, 'softwareHelp': {'@type': 'WebPage', 'url': BASE + '/faq/'}},
        {'@type': 'WebPage', '@id': url + '#webpage', 'url': url, 'name': c['title'] if not page else (c['faq_heading'] if page == 'faq/' else c['downloads']) + ' · VideoLoad', 'description': description(c,page), 'inLanguage': c['lang'], 'isPartOf': {'@id': BASE + '/#website'}, 'about': {'@id': BASE + '/#app'}, 'dateModified': UPDATED},
    ]
    if page == 'faq/':
        data.append({'@type': 'FAQPage', '@id': url + '#faq', 'inLanguage': c['lang'], 'mainEntity': [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in c['faq']]})
    if page:
        data.append({'@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': c['home'], 'item': BASE + c['prefix']}, {'@type': 'ListItem', 'position': 2, 'name': c['nav'][1] if page == 'faq/' else c['downloads'], 'item': url}]})
    return json.dumps({'@context': 'https://schema.org', '@graph': data}, ensure_ascii=False).replace('<', '\\u003c')


def header(c, page):
    return f'''<a class="skip" href="#main">Skip to content / 跳转正文</a>
<header class="site-header"><div class="wrap header-inner">
<a class="brand" href="{c['prefix']}" aria-label="VideoLoad · {c['home']}"><img src="/assets/app-icon.png" width="40" height="40" alt="">VideoLoad</a>
<nav class="nav" aria-label="Main navigation"><a class="features-link" href="{c['prefix']}#features">{c['nav'][0]}</a><a class="faq-link" href="{c['prefix']}faq/">{c['nav'][1]}</a><a class="github-link" href="{REPO}">GitHub ↗</a><a class="language" href="{c['other_prefix']}{page}" lang="{'zh-CN' if c['lang']=='en' else 'en'}">{c['other']}</a><span class="header-cta">{button(c['nav'][3], c['prefix']+'download/', small=True)}</span></nav>
</div></header>'''


def footer(c):
    ios_policy = 'privacy-zh.html' if c['lang'] == 'zh-CN' else 'privacy.html'
    return f'''<footer class="site-footer"><div class="wrap"><div class="footer-top"><div class="footer-brand">{c['footer']}</div><nav class="footer-links" aria-label="Footer"><a href="{c['prefix']}download/">{c['downloads']}</a><a href="{c['prefix']}faq/">{c['nav'][1]}</a><a href="{REPO}">GitHub ↗</a><a href="{POLICY}privacy.html">Android {c['privacy']}</a><a href="{POLICY}ios/{ios_policy}">iOS {c['privacy']}</a></nav></div><p class="fineprint">{c['limits']}</p><p class="updated">{c['updated']} © 2026 VideoLoad.</p></div></footer>'''


def page_html(lang, page, body, title=None, noindex=False):
    c = COPY[lang]
    canonical = BASE + c['prefix'] + page
    title = title or c['title']
    desc = description(c,page)
    robots = 'noindex, follow' if noindex else 'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1'
    return f'''<!doctype html>
<html lang="{c['lang']}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><meta name="robots" content="{robots}">
<link rel="canonical" href="{canonical}"><link rel="alternate" hreflang="en" href="{BASE}/{page}"><link rel="alternate" hreflang="zh-CN" href="{BASE}/zh/{page}"><link rel="alternate" hreflang="x-default" href="{BASE}/{page}">
<meta property="og:type" content="website"><meta property="og:site_name" content="VideoLoad"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{BASE}/assets/screenshots/player.png"><meta property="og:image:alt" content="VideoLoad iPhone player with marked clips; iOS coming soon"><meta property="og:locale" content="{'en_US' if lang=='en' else 'zh_CN'}"><meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#faf9f6"><link rel="icon" href="/assets/app-icon.png" type="image/png"><link rel="stylesheet" href="/style.css"><link rel="alternate" type="text/plain" title="Machine-readable product summary" href="/llms.txt"><link rel="alternate" type="application/json" title="Product facts" href="/product.json">
<script type="application/ld+json">{schemas(lang, page)}</script></head><body>{header(c,page)}<main id="main">{body}</main>{footer(c)}</body></html>'''


def faq_list(c, limit=None, opened=False):
    return '<div class="faq-list">' + ''.join(f'<details{" open" if opened else ""}><summary>{e(q)}</summary><p>{e(a)}</p></details>' for q,a in c['faq'][:limit]) + '</div>'


def stores(c):
    rows = []
    for platform, name, note, label, url in c['store']:
        action = button(label, url) if url else f'<span class="coming">{e(label)}</span>'
        rows.append(f'<div class="store-row"><div><div class="platform">{platform}</div><h3>{name}</h3></div><div class="store-detail">{note}</div>{action}</div>')
    return '<div class="store-list">' + ''.join(rows) + '</div>'


def download_section(c, help_link=True):
    help_html = f'<a class="download-help" href="{c["prefix"]}download/">{c["download_help"]} →</a>' if help_link else ''
    return f'<section class="download-section" id="download"><div class="wrap"><h2>{c["download_title"]}</h2><p class="lead">{c["download_intro"]}</p>{stores(c)}{help_html}</div></section>'


def home(lang):
    c = COPY[lang]
    features = ''.join(f'<article class="feature"><span class="number">{n}</span><h3>{title}</h3><p>{text}</p></article>' for n,title,text in c['features'])
    facts = ''.join(f'<div class="fact-row"><dt>{k}</dt><dd>{v}</dd></div>' for k,v in c['facts'])
    body = f'''<div class="wrap"><section class="hero" aria-labelledby="hero-title"><div><div class="eyebrow">{c['eyebrow']}</div><h1 id="hero-title">{c['headline']}</h1><p class="lead">{c['intro']}</p><div class="actions">{button(c['cta'],c['prefix']+'download/')}{button(c['secondary'],'#features',secondary=True)}</div><p class="trust">{c['trust']}</p></div><figure class="hero-visual"><div class="screen"><img src="/assets/screenshots/player.png" width="1440" height="662" fetchpriority="high" alt="VideoLoad iPhone player showing two marked clips / iPhone 播放器与两段标注"></div><figcaption><strong>{c['caption']}</strong><p>{c['caption_detail']}</p><p class="preview-note">{c['preview']}</p></figcaption></figure></section><p class="platform-line">{c['platform']}</p>
<section class="section" id="features"><div class="section-head"><div><div class="eyebrow">{c['section_label']}</div><h2>{c['section_title']}</h2></div></div><div class="feature-list">{features}</div></section>
<section class="gallery-section"><h2>{c['gallery_title']}</h2><div class="gallery"><figure><div class="phone"><img src="/assets/screenshots/library.png" width="662" height="1440" loading="lazy" alt="VideoLoad iPhone video library / iPhone 视频库"></div><figcaption>{c['library']}</figcaption></figure><figure><div class="phone"><img src="/assets/screenshots/compare.png" width="662" height="1440" loading="lazy" alt="VideoLoad Pro independent two-video comparison / Pro 双屏独立控制"></div><figcaption>{c['compare']}</figcaption></figure></div><p class="gallery-note">{c['gallery_note']}</p></section>
<section class="section facts"><div><div class="eyebrow">{c['facts_label']}</div><h2>{c['facts_title']}</h2></div><dl class="fact-table">{facts}</dl></section></div>
{download_section(c)}
<div class="wrap"><section class="section"><div class="section-head"><h2>{c['faq_title']}</h2></div>{faq_list(c,3)}<p class="faq-more"><a class="text-link" href="{c['prefix']}faq/">{c['faq_more']} →</a></p></section>
<section class="feedback"><div><h2>{c['feedback_title']}</h2><p>{c['feedback_text']}</p></div><div><div class="actions">{button(c['feedback_cta'],FEEDBACK)}{button(c['github_cta'],REPO,secondary=True)}</div><p class="note">{c['feedback_note']}</p></div></section></div>'''
    return page_html(lang,'',body)


def faq(lang):
    c = COPY[lang]
    body = f'''<div class="wrap"><header class="page-intro"><p class="breadcrumb"><a href="{c['prefix']}">{c['home']}</a> / {c['nav'][1]}</p><div class="eyebrow">VIDEOLOAD / FAQ</div><h1>{c['faq_heading']}</h1><p class="lead">{c['faq_intro']}</p></header><section class="content-section">{faq_list(c,opened=True)}<div class="actions">{button(c['feedback_cta'],FEEDBACK)}{button(c['cta'],c['prefix']+'download/',secondary=True)}</div></section></div>'''
    return page_html(lang,'faq/',body,c['nav'][1]+' · VideoLoad')


def downloads(lang):
    c = COPY[lang]
    if lang == 'en':
        help_html = f'''<h2>Which edition should I choose?</h2><p>The Google Play edition is free to start with optional one-time Pro. Its availability depends on store review, rollout and region. The <a href="{APK}">official direct APK</a> is a separate Chinese-branded Android app with its own updates and currently unlocked features. These are different app packages; store purchases do not transfer between them.</p><h2>Install on Android</h2><p>Android 8.0 or later is required. Use an official entry above. For an APK, Android may ask you to allow installation from your browser or file manager. Enable this only when needed for this installation and turn it off afterward. Do not disable system protection.</p><h2>iPhone is coming soon</h2><p>App Store submission is in progress. This page will add a verified App Store link after release. No iOS installation file is distributed here.</p><h2>Free and Pro</h2><p>Free store features include browsing, up to two unfinished downloads, playback, clip marking and looping. Paused or failed tasks count; completed or cancelled tasks do not.</p><p>Pro unlocks local import, independent dual-video comparison, compatible MP4/GIF export and removal of the task limit. It is a one-time in-app purchase, not a subscription. Your store shows the local price. Android and iOS purchases are separate. Use the original store account to recover a purchase; on iOS use Restore Purchases.</p><h2>Try a video you are allowed to save</h2><p>In the app browser, open our <a href="{DEMO}">original demo media page</a> and download the MP4 using the floating download button. Open the completed video, mark 1–3 seconds and 9–11 seconds, then try marked-only playback. Loop controls differ between platforms. Pro adds compatible export and two-video comparison.</p>'''
    else:
        help_html = f'''<h2>选择哪个版本？</h2><p>Google Play 版可免费开始使用，Pro 为可选买断内购。商店可用状态取决于审核、发布进度和地区。<a href="{APK}">官网直装 APK</a> 是独立中文品牌版本，采用独立更新渠道，当前功能已解锁。两个版本不是同一个安装包，商店购买权益不互通。</p><h2>Android 安装说明</h2><p>需要 Android 8.0 或更高版本，请从上方官方入口下载。安装 APK 时，系统可能要求允许当前浏览器或文件管理器安装应用；仅在本次安装需要时开启，用完可关闭。不要关闭系统安全保护。</p><h2>iPhone 即将上线</h2><p>目前正在提交 App Store，正式上架后将在本页补充核验过的官方入口。本站不分发 iOS 安装文件。</p><h2>免费版与 Pro</h2><p>商店免费版包含浏览、最多两条未完成下载任务、播放、标注和循环。暂停、失败计入任务限制，已完成或已取消不计入。</p><p>Pro 解锁本地导入、独立双屏对照、兼容来源 MP4/GIF 导出，并取消任务数量限制。一次买断，无订阅，实际价格以当地商店为准。Android 和 iOS 权益独立；恢复购买请使用原商店账号，iOS 可在 Pro 页面选择“恢复购买”。</p><h2>从原创演示视频开始</h2><p>在应用内浏览器打开<a href="{DEMO.replace('.html','-zh.html')}">原创演示素材页</a>，通过悬浮下载按钮保存 MP4。打开已完成视频，试着标记 1–3 秒、9–11 秒两段，体验只播标注；循环控制方式因平台而异。Pro 还可体验兼容来源导出和双屏对照。</p>'''
    body = download_section(c,False) + f'<div class="wrap"><section class="content-section prose">{help_html}<p><a href="{c["prefix"]}faq/">{c["faq_more"]} →</a> · <a href="{FEEDBACK}">{c["feedback_cta"]} ↗</a></p></section></div>'
    # Every page has an H1; the download section's visual heading becomes the page title.
    body = body.replace('<h2>', '<h1>', 1).replace('</h2>', '</h1>', 1)
    return page_html(lang,'download/',body,c['downloads']+' · VideoLoad')
