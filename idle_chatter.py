"""Plays a random R2-D2 sound at random intervals, so the robot idly
chatters to itself even when nobody's talking to it.
"""

import random
import threading


class IdleChatter:
    """Background thread that plays a random sound every random_uniform(min, max) seconds."""

    def __init__(self, sounds, sound_names, min_seconds, max_seconds):
        self._sounds = sounds
        self._sound_names = list(sound_names)
        self._min_seconds = min_seconds
        self._max_seconds = max_seconds
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        self._stop.set()

    def _run(self):
        while not self._stop.wait(random.uniform(self._min_seconds, self._max_seconds)):
            self._sounds.play_random(self._sound_names)
