"""Render the film's dedicated, video-first viewing page."""
from html import escape as e

from content import COPY, FEEDBACK
from promo import METADATA, media_url
from render import button, page_html


def watch(lang):
    copy = COPY[lang]
    transcript = (METADATA.parent / 'transcript.en.txt').read_text(encoding='utf-8')
    paragraphs = ''.join(f'<p>{e(text)}</p>' for text in transcript.strip().split('\n\n'))
    body = f'''<article class="watch-page wrap">
<header class="watch-heading"><h1 id="watch-title">{e(copy['video_page_title'])}</h1><p id="watch-description">{e(copy['video_page_description'])}</p></header>
<div class="film-player watch-player"><video width="1920" height="1080" controls playsinline preload="metadata" poster="/assets/promo/videoload-overview-poster.jpg" aria-labelledby="watch-title" aria-describedby="watch-description" lang="en"><source src="{e(media_url('videoload-overview-en.mp4'))}" type="video/mp4"><track kind="captions" srclang="en" label="English" src="{e(media_url('videoload-overview-en.vtt'))}"><p><a href="{e(media_url('videoload-overview-en.mp4'))}">{e(copy['video_page_title'])} · MP4</a></p></video></div>
<div class="watch-actions">{button(copy['cta'], copy['prefix']+'download/')}<a class="text-link" href="{copy['prefix']}#features">{e(copy['nav'][0])} ↗</a><a class="text-link" href="{e(media_url('videoload-overview-en.mp4'))}" download>MP4 ↓</a></div>
<section class="watch-transcript" aria-labelledby="transcript-title"><h2 id="transcript-title">{e(copy['video_transcript_title'])}</h2><div lang="en" dir="ltr">{paragraphs}</div><a class="text-link" href="{e(media_url('transcript.en.txt'))}">{e(copy['promo_transcript_label'])} ↗</a><p><a class="text-link" href="{FEEDBACK}">{e(copy['feedback_cta'])} ↗</a></p></section>
</article>'''
    return page_html(lang, 'video/', body, copy['video_page_title'])
