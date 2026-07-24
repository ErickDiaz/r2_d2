"""Offline speech-to-text using Vosk."""

import json

import vosk

vosk.SetLogLevel(-1)


class VoskTranscriber:
    """Transcribes a single spoken command using a shared Vosk model."""

    def __init__(self, model, sample_rate=16000):
        self._recognizer = vosk.KaldiRecognizer(model, sample_rate)
        self._sample_rate = sample_rate

    def transcribe(self, read_chunk, chunk_size, max_seconds=8):
        """Read chunks via read_chunk(chunk_size) -> bytes until an utterance ends
        (Vosk detects a pause) or max_seconds elapses. Returns the recognized text.
        """
        self._recognizer.Reset()
        max_reads = int(max_seconds * self._sample_rate / chunk_size)
        for _ in range(max_reads):
            if self._recognizer.AcceptWaveform(read_chunk(chunk_size)):
                break
        return json.loads(self._recognizer.Result()).get('text', '')
