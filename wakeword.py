"""Local wake-word detection using openWakeWord."""

from openwakeword.model import Model


class WakeWordDetector:
    """Detects a wake word from a stream of 16kHz mono int16 audio chunks."""

    def __init__(self, wakeword_models, threshold=0.5, chunk_size=1280):
        self._model = Model(wakeword_models=wakeword_models)
        self.threshold = threshold
        self.chunk_size = chunk_size

    def detect(self, chunk):
        """Feed one audio chunk. Returns the name of the triggered model, or None."""
        for name, score in self._model.predict(chunk).items():
            if score >= self.threshold:
                return name
        return None
