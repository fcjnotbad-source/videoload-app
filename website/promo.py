"""Describe the final public film using its published metadata only."""
from datetime import datetime
import json
import math
from pathlib import Path

from content import BASE

METADATA = Path(__file__).resolve().parent.parent / 'assets/promo/metadata.json'
VIDEO_ID = BASE + '/#film-video'


def video_schema(copy):
    if not METADATA.is_file():
        return None
    metadata = json.loads(METADATA.read_text(encoding='utf-8'))
    seconds = float(metadata['durationSeconds'])
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError('The public film duration must be positive and finite')
    width, height = int(metadata['width']), int(metadata['height'])
    if width <= 0 or height <= 0:
        raise ValueError('The public film dimensions must be positive')
    uploaded = datetime.fromisoformat(metadata['uploadDate'].replace('Z', '+00:00'))
    if uploaded.tzinfo is None:
        raise ValueError('The public film upload date must include its timezone')
    if metadata['inLanguage'] != 'en' or metadata['captionLanguage'] != 'en':
        raise ValueError('The published film has English narration and captions')
    return {
        '@type': 'VideoObject',
        '@id': VIDEO_ID,
        'name': copy['promo_title'],
        'description': copy['promo_note'],
        'contentUrl': BASE + '/assets/promo/videoload-overview-en.mp4',
        'thumbnailUrl': BASE + '/assets/promo/videoload-overview-poster.jpg',
        'uploadDate': metadata['uploadDate'],
        'duration': f'PT{seconds:g}S',
        'width': width,
        'height': height,
        'inLanguage': metadata['inLanguage'],
        'caption': {
            '@type': 'MediaObject',
            'contentUrl': BASE + '/assets/promo/videoload-overview-en.vtt',
            'encodingFormat': 'text/vtt',
            'inLanguage': metadata['captionLanguage'],
        },
    }
