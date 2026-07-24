"""Text-to-speech with a fallback chain: aiy.voice.tts (pico2wave, only
available on the AIY Raspbian image) first, then espeak-ng via subprocess,
then just a log message if neither is installed.
"""

import logging
import subprocess

try:
    from aiy.voice import tts as _aiy_tts
except ImportError:
    _aiy_tts = None


def say(text, lang='es-ES'):
    if _aiy_tts:
        _aiy_tts.say(text, lang=lang)
        return
    try:
        subprocess.run(['espeak-ng', '-v', lang.split('-')[0], text], check=True)
    except FileNotFoundError:
        logging.warning('No hay motor de TTS disponible, no se puede decir: %s', text)
