"""Text-to-speech with a fallback chain: Piper (natural neural voice, if
PIPER_BIN/PIPER_MODEL are set) -> aiy.voice.tts (pico2wave, only available
on the AIY Raspbian image) -> espeak-ng -> just a log message if nothing
is available.

Piper is kept as a persistent background process (its model load is the
slow part, several seconds) instead of restarting it on every call.
"""

import glob
import logging
import os
import subprocess
import time

try:
    from aiy.voice import tts as _aiy_tts
except ImportError:
    _aiy_tts = None

PIPER_BIN = os.getenv('PIPER_BIN')
PIPER_MODEL = os.getenv('PIPER_MODEL')
_PIPER_OUTPUT_DIR = '/tmp/piper_out'
_piper_process = None


def _piper():
    global _piper_process
    if _piper_process is None or _piper_process.poll() is not None:
        os.makedirs(_PIPER_OUTPUT_DIR, exist_ok=True)
        _piper_process = subprocess.Popen(
            [PIPER_BIN, '--model', PIPER_MODEL, '--output_dir', _PIPER_OUTPUT_DIR],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            text=True,
        )
    return _piper_process


def _say_piper(text, timeout=15):
    proc = _piper()
    before = set(glob.glob(os.path.join(_PIPER_OUTPUT_DIR, '*.wav')))
    proc.stdin.write(text + '\n')
    proc.stdin.flush()

    deadline = time.time() + timeout
    new_file = None
    while time.time() < deadline:
        after = set(glob.glob(os.path.join(_PIPER_OUTPUT_DIR, '*.wav'))) - before
        if after:
            new_file = after.pop()
            break
        time.sleep(0.1)
    if not new_file:
        raise RuntimeError('Piper no genero audio a tiempo')

    last_size = -1
    while True:
        size = os.path.getsize(new_file)
        if size == last_size and size > 0:
            break
        last_size = size
        time.sleep(0.1)

    # -D pulse (no el "default" de ALSA a secas): en equipos con PulseAudio
    # corriendo (p.ej. la Jetson), el default de ALSA puede no coincidir
    # con el sink que PulseAudio tiene configurado como salida real.
    subprocess.run(['aplay', '-q', '-D', 'pulse', new_file], check=True)
    os.remove(new_file)


def say(text, lang='es-ES'):
    if PIPER_BIN and PIPER_MODEL:
        _say_piper(text)
        return
    if _aiy_tts:
        _aiy_tts.say(text, lang=lang)
        return
    try:
        subprocess.run(['espeak-ng', '-v', lang.split('-')[0], text], check=True)
    except FileNotFoundError:
        logging.warning('No hay motor de TTS disponible, no se puede decir: %s', text)
