"""Normalizes recognized Spanish text for robust phrase matching
(case- and accent-insensitive, so "cuál" matches "cual")."""

import unicodedata


def normalize(text):
    text = unicodedata.normalize('NFKD', text.strip().lower())
    return ''.join(c for c in text if not unicodedata.combining(c))
