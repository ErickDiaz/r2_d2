"""Wake-word detection reusing Vosk's grammar-restricted recognition mode
instead of a separate wake-word library.
"""

import json

import vosk


class VoskWakeWordDetector:
    """Detects a fixed wake phrase using a grammar-restricted Vosk recognizer."""

    def __init__(self, model, wake_phrase, sample_rate=16000):
        self._wake_phrase = wake_phrase
        grammar = json.dumps([wake_phrase, '[unk]'])
        self._recognizer = vosk.KaldiRecognizer(model, sample_rate, grammar)

    def detect(self, chunk):
        """Feed one chunk of raw int16 PCM bytes. Returns True once the wake phrase is heard."""
        if self._recognizer.AcceptWaveform(chunk):
            text = json.loads(self._recognizer.Result()).get('text', '')
        else:
            text = json.loads(self._recognizer.PartialResult()).get('partial', '')
        if self._wake_phrase in text:
            self._recognizer.Reset()
            return True
        return False
