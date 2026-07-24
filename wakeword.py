"""Local wake-word detection using Picovoice Porcupine."""

import pvporcupine


class WakeWordDetector:
    """Detects a built-in Porcupine wake word from a stream of 16kHz mono int16 audio frames."""

    def __init__(self, access_key, keywords):
        self._keywords = list(keywords)
        self._porcupine = pvporcupine.create(access_key=access_key, keywords=self._keywords)

    @property
    def sample_rate(self):
        return self._porcupine.sample_rate

    @property
    def frame_length(self):
        return self._porcupine.frame_length

    def detect(self, frame):
        """Feed one audio frame (length == frame_length). Returns the matched keyword, or None."""
        index = self._porcupine.process(frame)
        return self._keywords[index] if index >= 0 else None
