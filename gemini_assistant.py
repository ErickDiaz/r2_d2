"""Answers open-ended questions using Google's Gemini API -- used as a
fallback when no local or Home Assistant command matches the recognized
text.
"""

import requests

GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'


class GeminiAssistant:
    """Sends recognized text to Gemini and returns its text response."""

    def __init__(self, api_key, model='gemini-2.0-flash'):
        self._api_key = api_key
        self._model = model

    def ask(self, text):
        response = requests.post(
            GEMINI_URL.format(model=self._model),
            params={'key': self._api_key},
            json={'contents': [{'parts': [{'text': text}]}]},
            timeout=15,
        )
        response.raise_for_status()
        candidates = response.json()['candidates']
        return candidates[0]['content']['parts'][0]['text'].strip()
