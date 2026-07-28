"""Text-to-speech with a fallback chain: Piper (natural neural voice, if
PIPER_BIN/PIPER_MODEL are set) -> aiy.voice.tts (pico2wave, only available
on the AIY Raspbian image) -> espeak-ng -> just a log message if nothing
is available.

Piper reloads its model on every call (a few seconds of latency) rather
than staying resident -- simpler and more robust than managing a
long-lived subprocess, at the cost of speed.
"""

import logging
import os
import subprocess

try:
    from aiy.voice import tts as _aiy_tts
except ImportError:
    _aiy_tts = None

PIPER_BIN = os.getenv('PIPER_BIN')
PIPER_MODEL = os.getenv('PIPER_MODEL')
_PIPER_OUTPUT = '/tmp/piper_say.wav'


def say(text, lang='es-ES'):
    if PIPER_BIN and PIPER_MODEL:
        subprocess.run(
            [PIPER_BIN, '--model', PIPER_MODEL, '--output_file', _PIPER_OUTPUT],
            input=text, text=True, check=True, capture_output=True,
        )
        subprocess.run(['aplay', '-q', _PIPER_OUTPUT], check=True)
        return
    if _aiy_tts:
        _aiy_tts.say(text, lang=lang)
        return
    try:
        subprocess.run(['espeak-ng', '-v', lang.split('-')[0], text], check=True)
    except FileNotFoundError:
        logging.warning('No hay motor de TTS disponible, no se puede decir: %s', text)
