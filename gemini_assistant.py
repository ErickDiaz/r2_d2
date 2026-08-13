"""Answers open-ended questions using Google's Gemini API -- used as a
fallback when no local or Home Assistant command matches the recognized
text.
"""

import re

import requests

GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'

SYSTEM_INSTRUCTION = (
    'Sos R2-D2, un robot asistente. Respondes en espanol, en texto plano '
    'sin markdown ni simbolos de formato (nada de **, *, #, listas con '
    'guiones, etc.), porque tu respuesta se lee en voz alta con un '
    'sintetizador de voz. Se breve y conversacional. No escribas sonidos '
    'de robot como "bip bip", "bip boop" ni similares -- esos sonidos ya '
    'se reproducen aparte como efectos de audio reales, asi que decirlos '
    'con palabras queda redundante. Responde directo, sin ese relleno.'
)


class GeminiAssistant:
    """Sends recognized text to Gemini and returns its text response."""

    def __init__(self, api_key, model='gemini-flash-latest'):
        self._api_key = api_key
        self._model = model

    def ask(self, text):
        response = requests.post(
            GEMINI_URL.format(model=self._model),
            params={'key': self._api_key},
            json={
                'system_instruction': {'parts': [{'text': SYSTEM_INSTRUCTION}]},
                'contents': [{'parts': [{'text': text}]}],
            },
            timeout=15,
        )
        response.raise_for_status()
        candidates = response.json()['candidates']
        text = candidates[0]['content']['parts'][0]['text'].strip()
        return _strip_beep_words(_strip_markdown(text))


def _strip_markdown(text):
    """Removes markdown formatting Gemini sometimes adds despite instructions
    not to, since it gets read aloud as-is instead of rendered."""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'[*_`#]', '', text)
    text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
    return text


_BEEP_WORDS = re.compile(
    r'^\s*(?:b(?:i|o)+p[.,!]*\s*)+', re.IGNORECASE
)


def _strip_beep_words(text):
    """Quita sonidos de robot escritos ("bip bip", "bip boop", etc.) que
    Gemini a veces agrega igual pese a la instruccion -- quedan redundantes
    porque esos sonidos ya se reproducen aparte como efectos de audio."""
    return _BEEP_WORDS.sub('', text).strip()
