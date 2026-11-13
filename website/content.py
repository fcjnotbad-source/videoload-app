"""Locale registry and validated public translations; no English fallback."""
import json
from pathlib import Path

BASE = 'https://videoload.pdos.work'
REPO = 'https://github.com/fcjnotbad-source/videoload-app'
PLAY = 'https://play.google.com/store/apps/details?id=com.fcj.videoload'
APK = 'https://vdb.aivest.art/apps/jiange-kuaixia'
FEEDBACK = REPO + '/issues/new/choose'
DEMO = 'https://fcjnotbad-source.github.io/videoload-review-media/ios/review.html'
POLICY = 'https://fcjnotbad-source.github.io/videoload-review-media/'
CONTACT_EMAIL = 'fcjnotbad@gmail.com'
UPDATED = '2026-11-13'

# The Android/iOS app settings both expose these fourteen languages.
# Keep the existing /zh/ URL; use Google's supported generic 'es' hreflang
# for the es-419 page because Google does not support numeric region 419.
LOCALES = {
    'en': ('en', '/', 'English', 'en', 'en_US'),
    'zh': ('zh-Hans', '/zh/', '简体中文', 'zh-Hans', 'zh_CN'),
    'zh-Hant': ('zh-Hant', '/zh-Hant/', '繁體中文', 'zh-Hant', 'zh_TW'),
    'ja': ('ja', '/ja/', '日本語', 'ja', 'ja_JP'),
    'de': ('de', '/de/', 'Deutsch', 'de', 'de_DE'),
    'fr': ('fr', '/fr/', 'Français', 'fr', 'fr_FR'),
    'ko': ('ko', '/ko/', '한국어', 'ko', 'ko_KR'),
    'es-419': ('es-419', '/es-419/', 'Español (Latinoamérica)', 'es', 'es_MX'),
    'pt-BR': ('pt-BR', '/pt-BR/', 'Português (Brasil)', 'pt-BR', 'pt_BR'),
    'id': ('id', '/id/', 'Bahasa Indonesia', 'id', 'id_ID'),
    'ar': ('ar', '/ar/', 'العربية', 'ar', 'ar_AR'),
    'hi': ('hi', '/hi/', 'हिन्दी', 'hi', 'hi_IN'),
    'it': ('it', '/it/', 'Italiano', 'it', 'it_IT'),
    'he': ('he', '/he/', 'עברית', 'he', 'he_IL'),
}


def load_copy():
    directory = Path(__file__).with_name('locales')
    reference = json.loads((directory / 'en.json').read_text(encoding='utf-8'))
    result = {}
    for key, (lang, prefix, native, hreflang, og_locale) in LOCALES.items():
        copy = json.loads((directory / (key + '.json')).read_text(encoding='utf-8'))
        if copy.keys() != reference.keys():
            raise ValueError('Missing or unexpected translation keys: ' + key)
        copy.update(locale_key=key, lang=lang, prefix=prefix, native_name=native,
                    hreflang=hreflang, og_locale=og_locale,
                    direction='rtl' if key in {'ar', 'he'} else 'ltr')
        result[key] = copy
    return result


COPY = load_copy()
