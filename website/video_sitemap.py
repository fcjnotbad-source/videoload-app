"""List only the film's dedicated watch pages in Google's video sitemap."""
from xml.sax.saxutils import escape

from content import COPY
from promo import video_schema, watch_url


def build_video_sitemap():
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">']
    for copy in COPY.values():
        film = video_schema(copy)
        lines.extend([
            f'<url><loc>{escape(watch_url(copy))}</loc><video:video>',
            f'<video:thumbnail_loc>{escape(film["thumbnailUrl"])}</video:thumbnail_loc>',
            f'<video:title>{escape(film["name"])}</video:title>',
            f'<video:description>{escape(film["description"])}</video:description>',
            f'<video:content_loc>{escape(film["contentUrl"])}</video:content_loc>',
            f'<video:duration>{float(film["duration"][2:-1]):g}</video:duration>',
            f'<video:publication_date>{escape(film["uploadDate"])}</video:publication_date>',
            '</video:video></url>',
        ])
    return '\n'.join(lines + ['</urlset>']) + '\n'
