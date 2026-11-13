"""Require complete translations, exact structures and unchanged official links."""
import json
from pathlib import Path
import re

from content import COPY, LOCALES


def shape(value):
    if isinstance(value, dict):
        return {key: shape(v) for key, v in value.items()}
    if isinstance(value, list):
        return [shape(v) for v in value]
    return type(value).__name__


def check_locales():
    directory = Path(__file__).with_name('locales')
    source = json.loads((directory / 'en.json').read_text())
    required = {'en', 'zh', 'zh-Hant', 'ja', 'de', 'fr', 'ko', 'es-419', 'pt-BR', 'id', 'ar', 'hi', 'it', 'he'}
    assert set(COPY) == required, 'App language coverage is incomplete'
    assert {p.stem for p in directory.glob('*.json')} == required
    for key, locale in COPY.items():
        raw = json.loads((directory / (key + '.json')).read_text())
        assert shape(raw) == shape(source), key
        assert len(locale['faq']) == 10 and len(locale['download_sections']) == 5, key
        assert [row[-1] for row in locale['store']] == [row[-1] for row in source['store']], key
        for heading in ('headline', 'section_title', 'download_title'):
            assert re.findall(r'<[^>]+>', locale[heading]) == re.findall(r'<[^>]+>', source[heading]), (key,heading)
        if key != 'en':
            for field in ('title', 'description', 'faq_description', 'download_description', 'intro', 'faq_intro'):
                assert raw[field] != source[field], (key, field, 'English fallback')
            assert all(a != source['faq'][i][1] for i, (_, a) in enumerate(raw['faq'])), key
            assert all(text != source['download_sections'][i]['paragraphs'][j] for i, section in enumerate(raw['download_sections']) for j, text in enumerate(section['paragraphs'])), key
        assert locale['direction'] == ('rtl' if key in {'ar', 'he'} else 'ltr'), key
        assert locale['hreflang'] != 'es-419', 'Use supported language-only es for search hreflang'
    print('PASS: all 14 app languages have complete, structurally matching translations with no English body fallback; URLs, heading markup and RTL language metadata verified.')


if __name__ == '__main__':
    check_locales()
